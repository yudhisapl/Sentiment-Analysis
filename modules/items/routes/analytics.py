# modules/items/routes/analytics.py

from typing import List, Dict
from collections import Counter
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


class WordFrequency(BaseModel):
    word: str
    freq: int


@router.get("/analytics/distribution", response_model=Dict[str, int])
def sentiment_distribution(db: Session = Depends(get_db)):
    """
    Mengembalikan distribusi jumlah data per kategori status.

    Contoh respons:
    {
        "Anxiety": 250,
        "Depression": 180,
        "Normal": 120
    }
    """
    rows = (
        db.query(
            MentalHealthResponse.status,
            func.count(MentalHealthResponse.id)
        )
        .group_by(MentalHealthResponse.status)
        .all()
    )

    return {status: int(count) for status, count in rows}


# daftar stopword sederhana; silakan modif kalau datanya bahasa Indonesia
STOPWORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that", "these", "those",
    "am", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing",
    "a", "an", "the",
    "and", "but", "if", "or", "because", "as", "until", "while",
    "of", "at", "by", "for", "with", "about", "against",
    "between", "into", "through", "during", "before", "after",
    "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how",
    "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very",
    "can", "will", "just", "should", "now"
}

WORD_RE = re.compile(r"\b\w+\b")


@router.get(
    "/analytics/top-words",
    response_model=Dict[str, List[WordFrequency]]
)
def top_words_per_category(
    top_n: int = Query(
        10,
        ge=1,
        le=50,
        description="Jumlah kata teratas per kategori"
    ),
    db: Session = Depends(get_db),
):
    """
    Mengembalikan kata yang paling sering muncul pada masing-masing kategori.

    Struktur respons:
    {
      "Anxiety": [
        {"word": "anxiety", "freq": 45},
        {"word": "panic", "freq": 30},
        ...
      ],
      "Depression": [
        {"word": "depressed", "freq": 40},
        ...
      ],
      ...
    }
    """
    # Ambil (status, statement) dari DB
    rows = db.query(
        MentalHealthResponse.status,
        MentalHealthResponse.statement
    ).all()

    # Kelompokkan teks berdasarkan kategori
    texts_by_status: Dict[str, List[str]] = {}
    for status, statement in rows:
        texts_by_status.setdefault(status, []).append(statement or "")

    result: Dict[str, List[WordFrequency]] = {}

    for status, texts in texts_by_status.items():
        counter = Counter()

        for text in texts:
            # tokenisasi sederhana
            words = WORD_RE.findall(text.lower())
            # buang stopword & kata terlalu pendek
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
