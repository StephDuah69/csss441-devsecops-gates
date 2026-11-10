"""SQLAlchemy Database Models for Book Catalog."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class BookModel(Base):
    """Book entity table definition."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, default="General", index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("19.99"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    availability: Mapped[str] = mapped_column(
        String(20), nullable=False, default="IN_STOCK", index=True
    )
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True, default=None)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (Index("idx_books_search", "title", "author", "category"),)

    @property
    def genre(self) -> str:
        """Alias genre to category for domain consistency."""
        return self.category

    @genre.setter
    def genre(self, value: str) -> None:
        self.category = value

    @property
    def publication_year(self) -> int:
        """Alias publication_year to year."""
        return self.year

    @publication_year.setter
    def publication_year(self, value: int) -> None:
        self.year = value
