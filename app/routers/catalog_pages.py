"""HTML Frontend Template router for Book Catalog UI."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.security import generate_csrf_token
from app.services import book_service

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def serve_catalog_home(
    request: Request,
    q: str | None = None,
    category: str | None = None,
    availability: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=9, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Render main catalog dashboard with search, filter, and pagination."""
    items, total = book_service.list_books(
        db=db,
        q=q,
        category=category,
        availability=availability,
        sort_by="title",
        sort_dir="asc",
        page=page,
        page_size=page_size,
    )

    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
    csrf_token = generate_csrf_token()

    # Convert model objects to serializable dicts for template
    books_data = [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "category": b.category,
            "year": b.year,
            "isbn": b.isbn,
            "price": float(b.price),
            "availability": b.availability,
            "rating": float(b.rating) if b.rating is not None else None,
            "cover_url": b.cover_url,
        }
        for b in items
    ]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "active_page": "catalog",
            "books": books_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "query": q,
            "current_category": category,
            "current_availability": availability,
            "csrf_token": csrf_token,
            "selected_book": None,
        },
    )


@router.get("/books/{book_id}", response_class=HTMLResponse)
def serve_book_detail(
    request: Request,
    book_id: int,
    db: Session = Depends(get_db),
):
    """Render catalog dashboard with direct book drawer opened."""
    book = book_service.get_book(db, book_id)
    items, total = book_service.list_books(
        db=db,
        sort_by="title",
        sort_dir="asc",
        page=1,
        page_size=9,
    )
    total_pages = max(1, (total + 9 - 1) // 9) if total > 0 else 1
    csrf_token = generate_csrf_token()

    books_data = [
        {
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "category": b.category,
            "year": b.year,
            "isbn": b.isbn,
            "price": float(b.price),
            "availability": b.availability,
            "rating": float(b.rating) if b.rating is not None else None,
            "cover_url": b.cover_url,
        }
        for b in items
    ]

    selected_book = None
    if book:
        selected_book = {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "category": book.category,
            "year": book.year,
            "isbn": book.isbn,
            "price": float(book.price),
            "availability": book.availability,
            "rating": float(book.rating) if book.rating is not None else None,
            "cover_url": book.cover_url,
        }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "active_page": "catalog",
            "books": books_data,
            "total": total,
            "page": 1,
            "page_size": 9,
            "total_pages": total_pages,
            "query": None,
            "current_category": None,
            "current_availability": None,
            "csrf_token": csrf_token,
            "selected_book": selected_book,
        },
    )

