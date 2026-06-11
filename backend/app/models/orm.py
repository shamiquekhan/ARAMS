from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.models.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    tier = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)

class ResearchTask(Base):
    __tablename__ = "research_tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    query = Column(Text, nullable=False)
    status = Column(String, default="pending")
    task_plan = Column(JSONB)
    iteration_count = Column(Integer, default=0)
    confidence_score = Column(Float)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    results = relationship("ResearchResult", back_populates="task")
    sources = relationship("Source", back_populates="task")
    report = relationship("Report", back_populates="task", uselist=False)

class ResearchResult(Base):
    __tablename__ = "research_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("research_tasks.id"))
    agent_name = Column(String, nullable=False)
    subtask = Column(Text)
    findings = Column(JSONB)
    verified = Column(Boolean, default=False)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("ResearchTask", back_populates="results")

class Source(Base):
    __tablename__ = "sources"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("research_tasks.id"))
    url = Column(Text, nullable=False)
    title = Column(String)
    domain = Column(String)
    trust_score = Column(Float)
    published_date = Column(DateTime)
    content_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("ResearchTask", back_populates="sources")

class Report(Base):
    __tablename__ = "reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("research_tasks.id"), unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String)
    executive_summary = Column(Text)
    full_content = Column(Text, nullable=False)
    citations = Column(JSONB)
    word_count = Column(Integer)
    human_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("ResearchTask", back_populates="report")
