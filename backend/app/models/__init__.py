"""ORM 模型汇总，main.py 导入以注册到 Base.metadata。"""
from app.models.user import User  # noqa: F401
from app.models.chat import Chat, Message  # noqa: F401
from app.models.document import Document, AnalysisReport  # noqa: F401
from app.models.law import LawChunk  # noqa: F401
