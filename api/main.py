from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="AI-News Backend Service", description="RESTful API cho dashboard")

class ArticleResponse(BaseModel):
    title: str
    url: str
    content: Optional[str] = None
    summary: Optional[List[str]] = None
    impact_label: Optional[str] = None
    impact_score: Optional[float] = None
    entities: Optional[List[str]] = None

@app.get("/")
def read_root():
    return {"message": "Welcome to AI-News API"}

@app.get("/news", response_model=List[ArticleResponse])
def get_news(limit: int = 20, impact_label: Optional[str] = None, topic: Optional[str] = None):
    # TODO: Fetch from database
    return []

@app.get("/stats")
def get_stats():
    # TODO: Return dashboard statistics 
    return {
        "total_articles": 0,
        "positive": 0,
        "negative": 0,
        "neutral": 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
