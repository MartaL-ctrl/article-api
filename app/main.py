from fastapi import FastAPI
from app.database import engine, Base
from app.routers import articles, users, subscriptions

# Create all tables on startup if they don't exist yet
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Article API", version="1.0.0")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])

@app.get("/health")
def health():
    return {"status": "ok"}