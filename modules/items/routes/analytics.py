# modules/items/routes/analytics.py

from typing import List, Dict
from collections import Counter, defaultdict
import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from database import get_db
from modules.items.schema.models import MentalHealthResponse


router = APIRouter(
    prefix="/mental-health",
    tags=["mental_health_analytics"],
)


# =======================
#  MODEL UNTUK RESPON
# =======================

class WordFrequency(BaseModel):
    word: str
    freq: int


# =======================
# 1. DISTRIBUSI SENTIMEN
# =======================

@router.get("/analytics/distribution", response_model=Dict[str, int])
def sentiment_distribution(db: Session = Depends(get_db)):
    """
    Mengembalikan distribusi jumlah data per kategori status.
    Melewati baris dengan status kosong / NULL.
    """
    rows = (
        db.query(
            MentalHealthResponse.status,
            func.count(MentalHealthResponse.id),
        )
        .filter(
            MentalHealthResponse.status.isnot(None),
            MentalHealthResponse.status != ""
        )
        .group_by(MentalHealthResponse.status)
        .all()
    )

    result: Dict[str, int] = {}
    for status, count in rows:
        status_norm = status.strip()
        if not status_norm:
            continue
        result[status_norm] = int(count)

    return result

# =======================
#  UTIL: STOPWORDS & REGEX
# =======================

# daftar stopword sederhana; silakan modif kalau datanya bahasa Indonesia
STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom",
    "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing",
    "a", "an", "the",
    "and", "but", "if", "or", "because", "as", "until", "while",
    "of", "at", "by", "for", "with", "about", "against",
    "between", "into", "through", "during", "before", "after",
    "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under",
    "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very",
    "can", "will", "just", "should", "now",
}

WORD_RE = re.compile(r"\b\w+\b")


# =========================================
# 2. TOP WORDS PER KATEGORI (clean_statement)
# =========================================

@router.get(
    "/analytics/top-words",
    response_model=Dict[str, List[WordFrequency]],
)
def top_words_per_category(
    top_n: int = Query(
        10,
        ge=1,
        le=50,
        description="Jumlah kata teratas per kategori",
    ),
    db: Session = Depends(get_db),
):
    """
    Top kata per kategori, berbasis `clean_statement`,
    melewati status kosong.
    """
    rows = (
        db.query(
            MentalHealthResponse.status,
            MentalHealthResponse.clean_statement,
        )
        .filter(
            MentalHealthResponse.status.isnot(None),
            MentalHealthResponse.status != "",
            MentalHealthResponse.clean_statement.isnot(None),
            MentalHealthResponse.clean_statement != "",
        )
        .all()
    )

    texts_by_status: Dict[str, List[str]] = {}
    for status, clean_text in rows:
        status_norm = status.strip()
        if not status_norm:
            continue
        texts_by_status.setdefault(status_norm, []).append(clean_text or "")

    result: Dict[str, List[WordFrequency]] = {}

    for status, texts in texts_by_status.items():
        counter = Counter()

        for text in texts:
            words = WORD_RE.findall(text.lower())
            words = [
                w for w in words
                if w not in STOPWORDS and len(w) > 2
            ]
            counter.update(words)

        most_common = counter.most_common(top_n)
        result[status] = [
            WordFrequency(word=w, freq=int(c))
            for w, c in most_common
        ]

    return result



# =================================================
# 3. RATA-RATA PANJANG KALIMAT PER KATEGORI (CLEAN)
# =================================================

@router.get("/analytics/length-stats", response_model=Dict[str, float])
def length_stats_per_category(db: Session = Depends(get_db)):
    """
    Mengembalikan median panjang kalimat (jumlah kata) per kategori,
    berbasis clean_statement, melewati status kosong dan teks kosong,
    serta mengabaikan outlier super panjang (misal > 400 kata).
    """
    rows = (
        db.query(
            MentalHealthResponse.status,
            MentalHealthResponse.clean_statement,
        )
        .filter(
            MentalHealthResponse.status.isnot(None),
            MentalHealthResponse.status != "",
            MentalHealthResponse.clean_statement.isnot(None),
            MentalHealthResponse.clean_statement != "",
        )
        .all()
    )

    lengths_by_status: Dict[str, List[int]] = defaultdict(list)

    for status, clean_text in rows:
        status_norm = status.strip()
        if not status_norm:
            continue

        text = clean_text or ""
        n_words = len(text.split())

        # abaikan outlier super panjang (opsional, bisa kamu atur threshold-nya)
        if n_words == 0 or n_words > 400:
            continue

        lengths_by_status[status_norm].append(n_words)

    import math

    result: Dict[str, float] = {}
    for status, lengths in lengths_by_status.items():
        if not lengths:
            continue
        lengths_sorted = sorted(lengths)
        m = len(lengths_sorted)
        mid = m // 2

        if m % 2 == 1:
            median = lengths_sorted[mid]
        else:
            median = (lengths_sorted[mid - 1] + lengths_sorted[mid]) / 2

        result[status] = round(float(median), 2)

    return result

# =====================================
# 4. CONTOH KALIMAT PER KATEGORI (CLEAN)
# =====================================

@router.get("/analytics/examples", response_model=List[str])
def examples_by_category(
    status: str = Query(..., description="Nama kategori, misal: Anxiety"),
    n: int = Query(5, ge=1, le=50, description="Jumlah contoh kalimat"),
    db: Session = Depends(get_db),
):
    """
    Contoh kalimat untuk satu kategori tertentu,
    pakai `clean_statement`.
    """
    rows = (
        db.query(MentalHealthResponse.clean_statement)
        .filter(
            MentalHealthResponse.status == status,
            MentalHealthResponse.clean_statement.isnot(None),
            MentalHealthResponse.clean_statement != "",
        )
        .order_by(MentalHealthResponse.id)
        .limit(n)
        .all()
    )

    examples = [txt for (txt,) in rows if txt]
    return examples