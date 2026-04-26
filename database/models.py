from sqlalchemy import Column, String, Float, Boolean, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Metadata
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    published_date = Column(String, nullable=True) 
    sapo = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    categories = Column(JSON, nullable=True)
    entities = Column(JSON, nullable=True)
    topics = Column(JSON, nullable=True)
    
    is_relevant = Column(Boolean, default=False)
    relevance_score = Column(Float, nullable=True)
    
    summary = Column(JSON, nullable=True)
    impact_label = Column(String, nullable=True)
    impact_score = Column(Float, nullable=True)
    impact_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
