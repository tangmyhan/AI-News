from sqlalchemy import Column, String, Float, Boolean, JSON, DateTime, Text, Index, func, text
import sqlalchemy.dialects.postgresql
from sqlalchemy.orm import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class Article(Base):
    __tablename__ = 'articles'

    # Khóa chính
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Thông tin cơ bản của bài viết (Metadata)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    published_date = Column(String, nullable=True) 
    sapo = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    categories = Column(JSON, nullable=True)
    entities = Column(JSON, nullable=True)
    topics = Column(JSON, nullable=True)
    
    # Kết quả NLP - Đánh giá mức độ liên quan
    is_relevant = Column(Boolean, default=False)
    relevance_score = Column(Float, nullable=True)
    
    # Kết quả NLP - Phân tích tác động
    summary = Column(JSON, nullable=True)
    impact_label = Column(String, nullable=True)
    impact_score = Column(Float, nullable=True)
    impact_reason = Column(Text, nullable=True)

    # Thời gian tạo và cập nhật bản ghi
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        # GIN Index: Full-Text Search
        Index(
            'idx_fts_articles',
            text("to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(sapo, '') || ' ' || coalesce(content, ''))"),
            postgresql_using='gin'
        ),
        # Index cho sắp xếp theo thời gian mới nhất
        Index('idx_published_date', published_date.desc()),
        # Index cho các filter nghiệp vụ
        Index('idx_impact_label', impact_label)
    )
