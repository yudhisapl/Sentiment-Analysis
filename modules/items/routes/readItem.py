# modules/items/routes/readItem.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from modules.items.schema.models import MentalHealthResponse
from modules.items.schema.schemas import MentalHealthOut


router = APIRouter(
    prefix="/mental-health",
    tags=["mental_health_read"],
)


@router.get("/responses", response_model=List[MentalHealthOut])
def read_all_responses(
    skip: int = Query(0, ge=0, description="Jumlah data yang dilewati (offset)"),
    limit: int = Query(100, ge=1, le=100, description="Jumlah maksimum data yang dikembalikan"),
    db: Session = Depends(get_db),
):
    """
    Mengembalikan data mental_health_responses dengan pagination.

    - skip  : offset (mulai dari data ke berapa), default 0
    - limit : berapa banyak data yang dikembalikan, default 100 (maks 100)
    """
    data = (
        db.query(MentalHealthResponse)
        .order_by(MentalHealthResponse.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return data


@router.get("/responses/{response_id}", response_model=MentalHealthOut)
def read_response_by_id(response_id: int, db: Session = Depends(get_db)):
    """
    Mengembalikan satu baris berdasarkan id.
    """
    obj = (
        db.query(MentalHealthResponse)
        .filter(MentalHealthResponse.id == response_id)
        .first()
    )
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Response dengan id={response_id} tidak ditemukan.",
        )
    return obj
