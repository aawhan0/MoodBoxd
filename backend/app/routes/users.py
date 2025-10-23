from fastapi import APIRouter
from app.services.letterboxd_scraper import get_user_data

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{username}")
def fetch_user_data(username: str):
    user_data = get_user_data(username)
    return {"username": username, "data": user_data}