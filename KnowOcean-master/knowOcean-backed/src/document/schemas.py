"""文档模块 Pydantic 模型"""
from pydantic import BaseModel, Field


class DocumentListItem(BaseModel):
    document_id: int = Field(..., alias="documentId")
    file_name: str = Field(..., alias="fileName")
    file_ext: str = Field(default="", alias="fileExt")
    file_size: int = Field(default=0, alias="fileSize")
    status: str  # PROCESSING | READY | FAILED | UPLOADED
    uploader_user_id: int = Field(..., alias="uploaderUserId")
    group_id: int = Field(..., alias="groupId")
    uploaded_at: str | None = Field(default=None, alias="uploadedAt")
    model_config = {"populate_by_name": True}
