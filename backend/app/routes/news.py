from fastapi import APIRouter, HTTPException, status, Query
from backend.app.services.news_service import news_service

router = APIRouter(prefix="/api/news", tags=["news"])

@router.get("")
async def get_news(
    category: str | None = Query(None, description="Category filter (world, technology, science, business, india, sports, lifestyle, trending)"),
    search: str | None = Query(None, description="Search query")
):
    articles = await news_service.get_articles(category=category, search=search)
    return {
        "status": "success",
        "count": len(articles),
        "articles": articles
    }

@router.get("/{article_id}")
async def get_article(article_id: str):
    article = await news_service.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    return article
