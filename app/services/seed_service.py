"""Database Seeding Service for CSSS 441 Book Catalog.

Idempotent: inserts default sample books only if they do not already exist.
Safe to rerun multiple times.
"""

from decimal import Decimal

from app.database import Base, SessionLocal, engine
from app.models import BookModel

SAMPLE_DATA = [
    {
        "id": 1,
        "title": "Security Engineering: A Guide to Building Dependable Distributed Systems",
        "author": "Ross Anderson",
        "category": "Security",
        "year": 2020,
        "isbn": "9781119642787",
        "price": Decimal("65.00"),
        "currency": "USD",
        "availability": "IN_STOCK",
        "rating": Decimal("4.8"),
    },
    {
        "id": 2,
        "title": "Threat Modeling: Designing for Security",
        "author": "Adam Shostack",
        "category": "Security",
        "year": 2014,
        "isbn": "9781118809990",
        "price": Decimal("49.99"),
        "currency": "USD",
        "availability": "IN_STOCK",
        "rating": Decimal("4.6"),
    },
    {
        "id": 3,
        "title": "Building Secure and Reliable Systems",
        "author": "Heather Adkins, Betsy Beyer, Paul Blankinship",
        "category": "Site Reliability & Security",
        "year": 2020,
        "isbn": "9781492083122",
        "price": Decimal("42.50"),
        "currency": "USD",
        "availability": "CHECKED_OUT",
        "rating": Decimal("4.7"),
    },
    {
        "id": 4,
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "category": "Architecture",
        "year": 2017,
        "isbn": "9781449373320",
        "price": Decimal("52.00"),
        "currency": "USD",
        "availability": "IN_STOCK",
        "rating": Decimal("4.9"),
    },
    {
        "id": 5,
        "title": "The Web Application Hacker's Handbook",
        "author": "Dafydd Stuttard, Marcus Pinto",
        "category": "Security",
        "year": 2011,
        "isbn": "9781118026472",
        "price": Decimal("45.00"),
        "currency": "USD",
        "availability": "UNAVAILABLE",
        "rating": Decimal("4.7"),
    },
    {
        "id": 6,
        "title": "Site Reliability Engineering: How Google Runs Production Systems",
        "author": "Betsy Beyer, Chris Jones, Jennifer Petoff, Niall Murphy",
        "category": "DevOps",
        "year": 2016,
        "isbn": "9781491929124",
        "price": Decimal("38.99"),
        "currency": "USD",
        "availability": "IN_STOCK",
        "rating": Decimal("4.8"),
    },
]


def seed_database() -> int:
    """Ensure database schema exists and seed missing sample books."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    inserted_count = 0

    try:
        for book_dict in SAMPLE_DATA:
            existing = (
                session.query(BookModel)
                .filter((BookModel.isbn == book_dict["isbn"]) | (BookModel.id == book_dict["id"]))
                .first()
            )

            if not existing:
                book = BookModel(**book_dict)
                session.add(book)
                inserted_count += 1

        session.commit()
        return inserted_count
    except Exception:
        session.rollback()
        return 0
    finally:
        session.close()
