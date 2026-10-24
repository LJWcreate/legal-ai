"""全局配置：一律从环境变量读取，禁止硬编码密钥。"""
from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # 数据库
    database_url: str = "postgresql+psycopg://legalai:legalai@localhost:5432/legalai"

    # JWT
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_chat_model: str = "deepseek-chat"

    # Embedding
    embedding_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_api_key: str = ""
    embedding_model: str = "BAAI/bge-m3"
    embedding_dim: int = 1024

    # 重排序（硅基流动 rerank 接口，与 embedding 同 Key）
    rerank_model: str = "BAAI/bge-reranker-v2-m3"
    rerank_candidates: int = 20   # 先粗检索的候选数
    rerank_enabled: bool = True

    # 视觉模型（图片合同 OCR，硅基流动，与 embedding 同 Key 同网关）
    vision_model: str = "Qwen/Qwen3-VL-32B-Instruct"

    # 上传
    upload_dir: Path = BASE_DIR / "uploads"
    max_upload_mb: int = 20

    # 免责声明（后端统一附带，避免前端遗漏）
    disclaimer: str = (
        "本内容仅作参考，不构成法律意见，不能代替执业律师的专业判断，"
        "请结合实际情况甄别。"
    )

    model_config = {"env_file": BASE_DIR / ".env", "extra": "ignore"}


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
