from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter()

@router.post("/", response_model=schemas.SubscriptionOut, status_code=201)
def subscribe(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Prevent duplicate subscriptions for the same user
    existing = (
        db.query(models.Subscription)
        .filter(models.Subscription.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already subscribed")

    sub = models.Subscription(user_id=current_user.id)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub

@router.delete("/", status_code=204)
def unsubscribe(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    sub = (
        db.query(models.Subscription)
        .filter(models.Subscription.user_id == current_user.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Not subscribed")
    db.delete(sub)
    db.commit()

@router.get("/notifications", response_model=list[schemas.NotificationOut])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Return newest notifications first
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )

@router.post("/notifications/{notification_id}/read", response_model=schemas.NotificationOut)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Filter by user_id to prevent users from marking other users' notifications
    notif = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif