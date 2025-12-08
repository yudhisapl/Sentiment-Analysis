from pydantic import BaseModel
from typing import Optional


class MentalHealthBase(BaseModel):
    # Input dasar: hanya statement pasien
    statement: str


class MentalHealthCreate(MentalHealthBase):
    """
    Dipakai di endpoint POST (insert data baru).
    Admin hanya memasukkan 'statement', diagnosa awal akan diprediksi oleh ML.
    """
    pass


class MentalHealthUpdate(BaseModel):
    """
    Dipakai di endpoint PUT (update data oleh psikolog setelah konsultasi).
    Hanya boleh mengubah status (diagnosa akhir).
    """
    status: str


class MentalHealthOut(BaseModel):
    """
    Output untuk semua endpoint CRUD:
    - status_initial : hasil prediksi model ML dari 'statement'
    - status_final   : nilai kolom 'status' di database (diagnosa akhir)
    """
    id: int
    statement: str
    status_initial: str
    status_final: str

    class Config:
        orm_mode = True
