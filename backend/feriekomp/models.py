from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class AntallBesokende(Base):
    """Enkel modell for å telle besøk."""

    __tablename__ = "antall_besokende"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    antall: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sist_oppdatert: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    def as_dict(self) -> dict:
        return {
            "antall": self.antall,
            "sist_oppdatert": self.sist_oppdatert.strftime("%Y-%m-%d %H:%M:%S"),
        }
