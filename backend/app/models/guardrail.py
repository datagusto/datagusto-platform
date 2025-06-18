from sqlalchemy import Column, String, Boolean, Integer, JSON, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.project import Project
import uuid

from app.core.database import Base


class Guardrail(Base):
    __tablename__ = "guardrails"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # 適用条件
    trigger_condition = Column(JSON, nullable=False)
    # 例: {"type": "always"} or {"type": "specific_tool", "tool_name": "db_query"}
    
    # チェック設定
    check_config = Column(JSON, nullable=False)
    # 例: {"type": "missing_values_any"} or {"type": "missing_values_column", "target_column": "user_id"}
    
    # アクション設定
    action = Column(JSON, nullable=False)
    # 例: {"type": "filter_records"} or {"type": "interrupt_agent"}
    
    # 統計
    execution_count = Column(Integer, default=0, nullable=False)
    applied_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="guardrails")