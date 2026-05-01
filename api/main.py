from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, text, cast, String
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.db_client import db_client
from database.models import Article

app = FastAPI(title="AI-News Backend Service", description="RESTful API cho dashboard")

frontend_dir = os.path.join(project_root, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/dashboard", StaticFiles(directory=frontend_dir, html=True), name="frontend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# database session
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
    published_date: Optional[str] = None
    source: Optional[str] = None
    categories: Optional[list] = None
    entities: Optional[list] = None
    topics: Optional[list] = None
    is_relevant: Optional[bool] = None
    relevance_score: Optional[float] = None
    impact_label: Optional[str] = None
    impact_score: Optional[float] = None
    impact_reason: Optional[str] = None
    summary: Optional[List[str]] = None
    content: Optional[str] = None

    class Config:
        orm_mode = True

@app.get("/")
def read_root():
    return {"message": "Welcome to AI-News API. Go to /dashboard to view the UI."}

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    # Đếm tổng số bài báo hôm nay
    today_str = datetime.now().strftime('%d %b %Y')
    total_articles = db.query(Article).count()
    today_articles = db.query(Article).filter(cast(Article.published_date, String).ilike(f"%{today_str}%")).count()
    
    # Tính số bài liên quan
    relevant_count = db.query(Article).filter(Article.is_relevant == True).count()
    
    # Tính số bài tích cực/tiêu cực/trung tính dựa trên bài có liên quan
    positive_count = db.query(Article).filter(
        Article.is_relevant == True, 
        Article.impact_label.ilike("%tích cực%") | Article.impact_label.ilike("%positive%")
    ).count()
    
    negative_count = db.query(Article).filter(
        Article.is_relevant == True, 
        Article.impact_label.ilike("%tiêu cực%") | Article.impact_label.ilike("%negative%")
    ).count()
    
    neutral_count = db.query(Article).filter(
        Article.is_relevant == True, 
        Article.impact_label.ilike("%trung tính%") | Article.impact_label.ilike("%neutral%")
    ).count()

    # % Bài tiêu cực / % Bài liên quan
    pct_relevant = round((relevant_count / total_articles * 100) if total_articles > 0 else 0, 1)
    pct_negative = round((negative_count / relevant_count * 100) if relevant_count > 0 else 0, 1)
    
    return {
        "total_articles": total_articles,
        "today_articles": today_articles,
        "relevant_articles": relevant_count,
        "positive": positive_count,
        "negative": negative_count,
        "neutral": neutral_count,
        "pct_relevant": pct_relevant,
        "pct_negative": pct_negative
    }

@app.get("/news", response_model=List[ArticleResponse])
def get_news(
    limit: int = 50, 
    impact_label: Optional[str] = None, 
    category: Optional[str] = None,
    entity: Optional[str] = None,
    topic: Optional[str] = None,
    min_relevance: Optional[float] = None,
    search: Optional[str] = None,
    time_range: Optional[str] = None, # 'today', '7days'
    db: Session = Depends(get_db)
):
    # is_relevant = True cho Dashboard
    query = db.query(Article).filter(Article.is_relevant == True)
    
    if impact_label and impact_label.lower() != 'all':
        if impact_label == 'Positive':
            query = query.filter(Article.impact_label.ilike("%tích cực%") | Article.impact_label.ilike("%positive%"))
        elif impact_label == 'Negative':
            query = query.filter(Article.impact_label.ilike("%tiêu cực%") | Article.impact_label.ilike("%negative%"))
        elif impact_label == 'Neutral':
            query = query.filter(Article.impact_label.ilike("%trung tính%") | Article.impact_label.ilike("%neutral%"))
        
    if min_relevance is not None:
        query = query.filter(Article.relevance_score >= min_relevance)
        
    if search:
        # Full Text Search trên title, sapo, content
        search_tsvector = func.to_tsvector('simple', func.coalesce(Article.title, '') + ' ' + func.coalesce(Article.sapo, '') + ' ' + func.coalesce(Article.content, ''))
        query = query.filter(search_tsvector.match(search))

    if category:
        query = query.filter(cast(Article.categories, String).ilike(f"%{category}%"))
    if entity:
        query = query.filter(cast(Article.entities, String).ilike(f"%{entity}%"))
    if topic:
        query = query.filter(cast(Article.topics, String).ilike(f"%{topic}%"))
        
    if time_range:
        if time_range == 'today':
            today_str = datetime.now().strftime('%d %b %Y')
            query = query.filter(cast(Article.published_date, String).ilike(f"%{today_str}%"))
        elif time_range == '7days':
            seven_days_ago = datetime.now() - timedelta(days=7)
            query = query.filter(Article.created_at >= seven_days_ago)
        
    # Order by newest
    query = query.order_by(Article.created_at.desc())
    
    articles = query.limit(limit).all()
    
    result = []
    for art in articles:
        source = "Unknown"
        if "tuoitre.vn" in art.url:
            source = "Tuổi Trẻ"
        elif "vnexpress.net" in art.url:
            source = "VNExpress"
            
        art_dict = {
            "id": art.id,
            "title": art.title,
            "url": art.url,
            "published_date": art.published_date,
            "source": source,
            "categories": art.categories,
            "entities": art.entities,
            "topics": art.topics,
            "is_relevant": art.is_relevant,
            "relevance_score": art.relevance_score,
            "impact_label": art.impact_label,
            "impact_score": art.impact_score,
            "impact_reason": art.impact_reason,
            "summary": art.summary,
            "content": art.content
        }
        result.append(art_dict)
        
    return result

@app.get("/news/{article_id}", response_model=ArticleResponse)
def get_news_detail(article_id: str, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
        
    source = "Unknown"
    if "tuoitre.vn" in article.url:
        source = "Tuổi Trẻ"
    elif "vnexpress.net" in article.url:
        source = "VNExpress"
        
    return {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "published_date": article.published_date,
        "source": source,
        "categories": article.categories,
        "entities": article.entities,
        "topics": article.topics,
        "is_relevant": article.is_relevant,
        "relevance_score": article.relevance_score,
        "impact_label": article.impact_label,
        "impact_score": article.impact_score,
        "impact_reason": article.impact_reason,
        "summary": article.summary,
        "content": article.content
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
