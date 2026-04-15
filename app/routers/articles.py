from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import httpx

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter()

EXTERNAL_ARTICLES_URL = "https://jsonplaceholder.typicode.com/posts"

def _notify_subscribers(db: Session, article: models.Article):
    """Create a notification record for every subscribed user."""
    subscribers = db.query(models.Subscription).all()
    for sub in subscribers:
        notification = models.Notification(
            user_id=sub.user_id,
            article_id=article.id,
            message=f"New article available: {article.title}",
        )
        db.add(notification)
    db.commit()

@router.post("/", response_model=schemas.ArticleOut, status_code=201)
def create_article(
    article_in: schemas.ArticleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    article = models.Article(
        title=article_in.title,
        content=article_in.content,
        author_id=current_user.id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    # Notify subscribers after the article is posted
    _notify_subscribers(db, article)
    return article

@router.get("/", response_model=list[schemas.ArticleOut])
def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return db.query(models.Article).offset(skip).limit(limit).all()

@router.get("/{article_id}", response_model=schemas.ArticleOut)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.put("/{article_id}", response_model=schemas.ArticleOut)
def update_article(
    article_id: int,
    article_in: schemas.ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to edit this article")

    # Only update fields that were actually provided
    if article_in.title is not None:
        article.title = article_in.title
    if article_in.content is not None:
        article.content = article_in.content

    db.commit()
    db.refresh(article)
    return article

@router.delete("/{article_id}", status_code=204)
def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this article")
    db.delete(article)
    db.commit()

@router.post("/import/bulk", response_model=schemas.BulkImportResult, status_code=201)
def bulk_import(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Fetch articles from an external source and save them to the database."""
    try:
        response = httpx.get(EXTERNAL_ARTICLES_URL, params={"_limit": limit}, timeout=10)
        response.raise_for_status()
        raw_articles = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch external articles: {exc}")

    imported = []
    failed = 0

    for item in raw_articles:
        try:
            article = models.Article(
                title=item["title"],
                content=item["body"],
                author_id=current_user.id,
            )
            db.add(article)
            db.flush()  # get article.id before the final commit
            imported.append(article)
        except Exception:
            failed += 1
            db.rollback()
            continue

    if imported:
        db.commit()
        for article in imported:
            db.refresh(article)
            _notify_subscribers(db, article)

    return schemas.BulkImportResult(
        imported=len(imported),
        failed=failed,
        articles=imported,
    )