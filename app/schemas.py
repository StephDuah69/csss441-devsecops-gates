"""Pydantic v2 schemas and request validation models for Book Catalog."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Final

from pydantic import BaseModel, ConfigDict, Field, field_validator

APP_NAME: Final[str] = "csss441-book-catalog"
APP_VERSION: Final[str] = "1.0.0"
QUERY_PATTERN: Final[str] = r"^[a-zA-Z0-9\s\.\-_]+$"
ISBN_PATTERN: Final[str] = r"^(97[89])?[0-9]{9}[0-9Xx]$"


class HealthResponse(BaseModel):
    """Health check response payload."""

    model_config = ConfigDict(extra="ignore")

    status: str = Field(default="healthy", description="Current health status of the service")
    app: str = Field(default=APP_NAME, description="Application identifier")
    version: str = Field(default=APP_VERSION, description="Application semantic version")


class BookBase(BaseModel):
    """Base schema for book attributes."""

    model_config = ConfigDict(extra="ignore")

    title: str = Field(..., min_length=1, max_length=120, description="Book title")
    author: str = Field(..., min_length=1, max_length=100, description="Author name")
    category: str = Field(
        default="General", min_length=1, max_length=50, description="Category or genre"
    )
    year: int = Field(..., ge=1450, le=2030, description="Publication year")
    isbn: str = Field(..., description="Unique ISBN-10 or ISBN-13 identifier")
    price: Decimal = Field(default=Decimal("19.99"), ge=Decimal("0.00"), description="Book price")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="Currency code")
    availability: str = Field(default="IN_STOCK", description="Stock availability status")
    rating: Decimal | None = Field(
        default=None, ge=Decimal("0.0"), le=Decimal("5.0"), description="Rating (0-5)"
    )
    cover_url: str | None = Field(default=None, max_length=500, description="Cover image URL")

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        """Validate ISBN format."""
        clean = v.replace("-", "").replace(" ", "").strip()
        if not re.match(ISBN_PATTERN, clean):
            raise ValueError("Invalid ISBN format. Must be a valid 10 or 13-digit ISBN.")
        return clean

    @field_validator("availability")
    @classmethod
    def validate_availability(cls, v: str) -> str:
        """Validate availability status."""
        allowed = {"IN_STOCK", "CHECKED_OUT", "UNAVAILABLE"}
        upper_v = v.strip().upper()
        if upper_v not in allowed:
            raise ValueError(f"Availability must be one of: {', '.join(allowed)}")
        return upper_v


class BookCreate(BookBase):
    """Schema for book creation."""


class BookUpdate(BaseModel):
    """Schema for updating an existing book record."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = Field(None, min_length=1, max_length=120)
    author: str | None = Field(None, min_length=1, max_length=100)
    category: str | None = Field(None, min_length=1, max_length=50)
    year: int | None = Field(None, ge=1450, le=2030)
    price: Decimal | None = Field(None, ge=Decimal("0.00"))
    availability: str | None = None
    rating: Decimal | None = Field(None, ge=Decimal("0.0"), le=Decimal("5.0"))
    cover_url: str | None = Field(None, max_length=500)

    @field_validator("availability")
    @classmethod
    def validate_availability(cls, v: str | None) -> str | None:
        """Validate optional availability status."""
        if v is None:
            return None
        allowed = {"IN_STOCK", "CHECKED_OUT", "UNAVAILABLE"}
        upper_v = v.strip().upper()
        if upper_v not in allowed:
            raise ValueError(f"Availability must be one of: {', '.join(allowed)}")
        return upper_v


class Book(BaseModel):
    """Book entity schema matching legacy format with extended fields."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)

    id: int = Field(gt=0, description="Unique book identifier")
    title: str = Field(min_length=1, max_length=120, description="Book title")
    author: str = Field(min_length=1, max_length=100, description="Author name")
    category: str = Field(min_length=1, max_length=50, description="Subject category")
    year: int = Field(ge=1450, le=2030, description="Publication year")
    isbn: str = Field(default="0000000000", description="ISBN")
    price: Decimal = Field(default=Decimal("19.99"), ge=Decimal("0.00"))
    currency: str = Field(default="USD")
    availability: str = Field(default="IN_STOCK")
    rating: Decimal | None = None
    cover_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BookListResponse(BaseModel):
    """List response wrapping book items and count."""

    model_config = ConfigDict(extra="ignore")

    total: int = Field(ge=0, description="Total matching books")
    items: list[Book] = Field(default_factory=list, description="Array of book records")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")
    total_pages: int = Field(default=1, ge=1, description="Total number of pages")
