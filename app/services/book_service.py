"""Service layer for parameterized database operations on Book entities.

Enforces:
- Parameterized queries to eliminate SQL injection (CWE-89)
- Safe sorting allowlist
- Server-side pagination
"""

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models import BookModel
from app.schemas import BookCreate, BookUpdate

# Strict allowlist of sortable database columns
SORT_ALLOWLIST = {
    "title": BookModel.title,
    "author": BookModel.author,
    "year": BookModel.year,
    "price": BookModel.price,
    "created_at": BookModel.created_at,
}


def list_books(
    db: Session,
    q: str | None = None,
    category: str | None = None,
    availability: str | None = None,
    sort_by: str = "title",
    sort_dir: str = "asc",
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[BookModel], int]:
    """Retrieve filtered, sorted, and paginated books using safe parameterized query."""
    stmt = select(BookModel)
    count_stmt = select(func.count(BookModel.id))

    # Search filter across title, author, category
    if q and q.strip():
        search_term = f"%{q.strip().lower()}%"
        filter_clause = (
            func.lower(BookModel.title).like(search_term)
            | func.lower(BookModel.author).like(search_term)
            | func.lower(BookModel.category).like(search_term)
        )
        stmt = stmt.where(filter_clause)
        count_stmt = count_stmt.where(filter_clause)

    # Category filter
    if category and category.strip() and category.strip().lower() != "all":
        stmt = stmt.where(func.lower(BookModel.category) == category.strip().lower())
        count_stmt = count_stmt.where(func.lower(BookModel.category) == category.strip().lower())

    # Availability filter
    if availability and availability.strip() and availability.strip().lower() != "all":
        stmt = stmt.where(BookModel.availability == availability.strip().upper())
        count_stmt = count_stmt.where(BookModel.availability == availability.strip().upper())

    # Total matching records count
    total = db.scalar(count_stmt) or 0

    # Sorting with strict allowlist
    sort_col = SORT_ALLOWLIST.get(sort_by, BookModel.title)
    if sort_dir.lower() == "desc":
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(sort_col)

    # Pagination
    offset = max(0, (page - 1) * page_size)
    stmt = stmt.offset(offset).limit(page_size)

    items = list(db.scalars(stmt).all())
    return items, total


def get_book_by_id(db: Session, book_id: int) -> BookModel | None:
    """Retrieve single book by primary key."""
    return db.get(BookModel, book_id)


# Convenience alias
get_book = get_book_by_id



def get_book_by_isbn(db: Session, isbn: str) -> BookModel | None:
    """Check existence of a book by ISBN."""
    stmt = select(BookModel).where(BookModel.isbn == isbn.strip())
    return db.scalar(stmt)


def create_book(db: Session, book_in: BookCreate) -> BookModel:
    """Insert a new validated book record."""
    book = BookModel(
        title=book_in.title.strip(),
        author=book_in.author.strip(),
        isbn=book_in.isbn,
        category=book_in.category.strip(),
        year=book_in.year,
        price=book_in.price,
        currency=book_in.currency.upper(),
        availability=book_in.availability,
        rating=book_in.rating,
        cover_url=book_in.cover_url.strip() if book_in.cover_url else None,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(db: Session, book: BookModel, updates: BookUpdate) -> BookModel:
    """Update fields of an existing book."""
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if isinstance(value, str):
                value = value.strip()
            setattr(book, field, value)

    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book: BookModel) -> None:
    """Remove a book record."""
    db.delete(book)
    db.commit()
