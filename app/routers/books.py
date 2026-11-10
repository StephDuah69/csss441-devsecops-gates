"""Book catalogue API endpoints with query filtering, validation, and mutations."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    QUERY_PATTERN,
    Book,
    BookCreate,
    BookListResponse,
    BookUpdate,
)
from app.security import limiter, verify_admin
from app.services import book_service

logger = logging.getLogger("csss441.api")
router = APIRouter(tags=["Catalogue"])


@router.get(
    "/books",
    response_model=BookListResponse,
    status_code=status.HTTP_200_OK,
    summary="List or search books",
    description="Retrieve catalog books, optionally filtered by keyword query.",
)
def get_books(
    request: Request,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=50,
            pattern=QUERY_PATTERN,
            description="Optional search query keyword (1-50 alphanumeric characters)",
        ),
    ] = None,
    category: str | None = None,
    availability: str | None = None,
    sort_by: str = "title",
    sort_dir: str = "asc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> BookListResponse:
    """Retrieve all books or search books by keyword."""
    if q is not None:
        clean_query = q.strip().lower()
        if not clean_query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be whitespace-only.",
            )
    else:
        clean_query = None

    items, total = book_service.list_books(
        db=db,
        q=clean_query,
        category=category,
        availability=availability,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size,
    )

    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

    return BookListResponse(
        total=total,
        items=[Book.model_validate(b) for b in items],
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/api/books/{book_id}",
    response_model=Book,
    status_code=status.HTTP_200_OK,
    summary="Get single book by ID",
)
def get_book(book_id: int, db: Session = Depends(get_db)) -> Book:
    """Fetch details for a specific book record."""
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found.",
        )
    return Book.model_validate(book)


@router.post(
    "/api/books",
    response_model=Book,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book record (Admin only)",
)
@limiter.limit("30/minute")
def create_book(
    request: Request,
    book_in: BookCreate,
    is_admin: bool = Depends(verify_admin),
    db: Session = Depends(get_db),
) -> Book:
    """Insert a new book record after validating schema and duplicate ISBN check."""
    existing = book_service.get_book_by_isbn(db, book_in.isbn)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Book with ISBN '{book_in.isbn}' already exists in catalog.",
        )

    book = book_service.create_book(db, book_in)
    logger.info("Admin created book id=%d, title='%s'", book.id, book.title)
    return Book.model_validate(book)


@router.put(
    "/api/books/{book_id}",
    response_model=Book,
    status_code=status.HTTP_200_OK,
    summary="Update an existing book record (Admin only)",
)
@limiter.limit("30/minute")
def update_book(
    request: Request,
    book_id: int,
    updates: BookUpdate,
    is_admin: bool = Depends(verify_admin),
    db: Session = Depends(get_db),
) -> Book:
    """Modify details of an existing book."""
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found.",
        )

    updated = book_service.update_book(db, book, updates)
    logger.info("Admin updated book id=%d", updated.id)
    return Book.model_validate(updated)


@router.delete(
    "/api/books/{book_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a book record (Admin only)",
)
@limiter.limit("20/minute")
def delete_book(
    request: Request,
    book_id: int,
    is_admin: bool = Depends(verify_admin),
    db: Session = Depends(get_db),
):
    """Remove a book from catalog after admin authentication."""
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found.",
        )

    book_service.delete_book(db, book)
    logger.info("Admin deleted book id=%d", book_id)
    return {"message": f"Book with id {book_id} deleted successfully."}
