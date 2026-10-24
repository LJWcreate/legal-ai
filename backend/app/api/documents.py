"""文档模块：上传（后台异步解析分析）、列表、状态、报告、删除。

安全要点：
- 类型白名单 + 大小限制；
- 文件按用户隔离存储 uploads/{user_id}/{doc_id}/；
- 所有接口校验文档归属，A 用户拿不到 B 用户的文档。
"""
import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models.document import ALLOWED_FILE_TYPES, AnalysisReport, Document
from app.models.user import User
from app.schemas import DocumentResponse, ReportResponse
from app.services.agent.contract_agent import analyze_document_task

router = APIRouter()


def _owned_doc(db: Session, doc_id: int, user_id: int) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None or doc.user_id != user_id:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload(
    background: BackgroundTasks,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if file.filename is None:
        raise HTTPException(status_code=400, detail="缺少文件名")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_FILE_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型，仅允许 {sorted(ALLOWED_FILE_TYPES)}")

    doc = Document(user_id=current_user.id, filename=file.filename, file_type=suffix.lstrip("."), file_path="", file_size=0)
    db.add(doc)
    db.flush()  # 先拿 id 用于隔离目录

    dest_dir = settings.upload_dir / str(current_user.id) / str(doc.id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / file.filename
    size = 0
    with dest.open("wb") as out:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            if size > settings.max_upload_mb * 1024 * 1024:
                out.close()
                shutil.rmtree(dest_dir, ignore_errors=True)
                db.rollback()
                raise HTTPException(status_code=413, detail=f"文件超过 {settings.max_upload_mb}MB 限制")
            out.write(chunk)

    doc.file_path = str(dest)
    doc.file_size = size
    doc.status = "pending"
    db.commit()
    db.refresh(doc)

    background.add_task(analyze_document_task, doc.id)
    return doc


@router.get("", response_model=list[DocumentResponse])
def list_docs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.id.desc()).all()


@router.get("/{doc_id}/status", response_model=DocumentResponse)
def doc_status(doc_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _owned_doc(db, doc_id, current_user.id)


@router.get("/{doc_id}/report", response_model=ReportResponse)
def get_report(doc_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = _owned_doc(db, doc_id, current_user.id)
    report = db.query(AnalysisReport).filter(AnalysisReport.document_id == doc.id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="报告尚未生成，请稍后再试")
    return ReportResponse(
        document_id=doc.id,
        summary=report.summary,
        risk_items=report.risk_items,
        disclaimer=settings.disclaimer,
    )


@router.delete("/{doc_id}", status_code=204)
def delete_doc(doc_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = _owned_doc(db, doc_id, current_user.id)
    db.query(AnalysisReport).filter(AnalysisReport.document_id == doc.id).delete()
    db.delete(doc)
    db.commit()
    shutil.rmtree(settings.upload_dir / str(current_user.id) / str(doc_id), ignore_errors=True)
