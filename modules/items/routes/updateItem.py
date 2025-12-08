# modules/items/routes/updateItem.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from modules.items.schema.models import MentalHealthResponse
from modules.items.schema.schemas import MentalHealthUpdate, MentalHealthOut
from modules.items.ml.services.predict_xgb import predict_text

router = APIRouter(
    prefix="/mental-health",
    tags=["mental_health_update"],
)


def _to_out(obj: MentalHealthResponse) -> MentalHealthOut:
    status_initial = predict_text(obj.statement)
    status_final = obj.status

    return MentalHealthOut(
        id=obj.id,
        statement=obj.statement,
        status_initial=status_initial,
        status_final=status_final,
    )


@router.put("/responses/{response_id}", response_model=MentalHealthOut)
def update_response(
    response_id: int,
    payload: MentalHealthUpdate,
    db: Session = Depends(get_db),
):
    """
    Memperbarui status (diagnosa akhir) untuk id tertentu.
    Statement TIDAK boleh diubah di sini.
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

    # Hanya update status (diagnosa akhir)
    obj.status = payload.status

    db.commit()
    db.refresh(obj)

    return _to_out(obj)

