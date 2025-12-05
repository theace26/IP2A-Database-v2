from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class FileAttachment(Base):
    __tablename__ = "file_attachments"

    id = Column(Integer, primary_key=True, index=True)

    # 'student', 'credential', 'jatc_application', etc.
    record_type = Column(String(50), nullable=False)
    # generic FK (validated in service)
    record_id = Column(Integer, nullable=False)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)   # path on disk
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer)
    description = Column(String(255))

    uploaded_at = Column(DateTime, default=datetime.utcnow)
