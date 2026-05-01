import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc, or_
from typing import List, Optional
from pydantic import BaseModel

from database.db_client import db_client
from database.models import Article

app = FastAPI(title="AI-News Backend Service", description="RESTful API cho dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = db_client.get_session()
    try:
        yield db
    finally:
        db.close()

class ArticleResponse(BaseModel):
    id: str
    title: str
    url: str
    sapo: Optional[str] = None
    published_date: Optional[str] = None
    summary: Optional[List[str]] = None
    impact_label: Optional[str] = None
    impact_score: Optional[float] = None
    impact_reason: Optional[str] = None
    relevance_score: Optional[float] = None
    topics: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    
    class Config:
        from_attributes = True

@app.get("/")
def read_root():
    return {"message": "Welcome to AI-News API"}

@app.get("/news", response_model=List[ArticleResponse])
def get_news(
    query: Optional[str] = None,
    impact_label: Optional[str] = None,
    time_range: Optional[str] = None,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    base_query = db.query(Article).filter(Article.is_relevant == True)
    
    if impact_label:
        base_query = base_query.filter(Article.impact_label == impact_label)
        
    if time_range:
        now = datetime.utcnow()
        if time_range == "today":
            today_str = now.strftime('%d/%m/%Y')
            base_query = base_query.filter(Article.published_date.like(f"%{today_str}%"))
        elif time_range == "7days":
            seven_days_ago = now - timedelta(days=7)
            base_query = base_query.filter(Article.created_at >= seven_days_ago)

    if query:
        fts_filter = text("to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(sapo, '') || ' ' || coalesce(content, '')) @@ plainto_tsquery('simple', :search_query)")
        base_query = base_query.filter(fts_filter).params(search_query=query)
        
    articles = base_query.order_by(desc(Article.published_date)).offset(offset).limit(limit).all()
    
    for article in articles:
        if article.topics and isinstance(article.topics, list):
            article.topics = [t.get("name", "") if isinstance(t, dict) else t for t in article.topics]
            
    return articles

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_scraped = db.query(Article).count()
    total_relevant = db.query(Article).filter(Article.is_relevant == True).count()
    
    percent_relevant = round((total_relevant / total_scraped * 100) if total_scraped > 0 else 0, 1)

    today_str = datetime.utcnow().strftime('%d/%m/%Y')
    today_count = db.query(Article).filter(Article.published_date.like(f"%{today_str}%")).count()
    
    impact_counts = db.query(
        Article.impact_label, 
        func.count(Article.id)
    ).filter(Article.is_relevant == True).group_by(Article.impact_label).all()
    
    stats = {
        "total_articles": total_relevant,
        "total_scraped": total_scraped,
        "percent_relevant": percent_relevant,
        "today_count": today_count,
        "positive": 0,
        "negative": 0,
        "neutral": 0,
        "percent_negative": 0
    }
    
    for label, count in impact_counts:
        if label:
            if label.lower() == "tích cực":
                stats["positive"] = count
            elif label.lower() == "tiêu cực":
                stats["negative"] = count
            elif label.lower() == "trung lập":
                stats["neutral"] = count
                
    stats["percent_negative"] = round((stats["negative"] / total_relevant * 100) if total_relevant > 0 else 0, 1)
            
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
