from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from datetime import datetime 
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model):
    __tablename__ = "user"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(120), nullable=False)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), unique=True, nullable=False)
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(128), nullable=False)
    first_name: so.Mapped[str] = so.mapped_column(sa.String(120), nullable=False)
    last_name: so.Mapped[str] = so.mapped_column(sa.String(120), nullable=False)

    friends: so.WriteOnlyMapped["Friend"] = so.relationship("Friend", back_populates="user", foreign_keys="[Friend.user_id]")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Friend(db.Model):
    __tablename__ = "friend"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("user.id", name="fk_friend_user_id"), nullable=False
    )
    friend_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("user.id", name="fk_friend_friend_id"), nullable=False
    )

class LocationGuess(db.Model):
    __tablename__ = "location_guess"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    game_history_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("game_history.id", ondelete="CASCADE", name="fk_location_guess_game_history_id"),
        nullable=False
    )
    location_name: so.Mapped[str] = so.mapped_column(
        sa.String(255), 
        nullable=False
    )
    actual_latitude: so.Mapped[float] = so.mapped_column(nullable=False)
    actual_longitude: so.Mapped[float] = so.mapped_column(nullable=False)
    guessed_latitude: so.Mapped[float] = so.mapped_column(nullable=False)
    guessed_longitude: so.Mapped[float] = so.mapped_column(nullable=False)
    distance_error_meters: so.Mapped[float] = so.mapped_column(nullable=False)
    time_taken_seconds: so.Mapped[int] = so.mapped_column(nullable=False)

    game_history: so.Mapped["GameHistory"] = so.relationship(back_populates="guesses")

class GameHistory(db.Model):
    __tablename__ = "game_history"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("user.id", ondelete="CASCADE", name="fk_game_history_user_id"),
        nullable=False
    )
    start_time: so.Mapped[datetime] = so.mapped_column(
        server_default=sa.func.now()
    )
    finish_time: so.Mapped[Optional[datetime]] = so.mapped_column(
        nullable=True
    )
    total_score: so.Mapped[int] = so.mapped_column(default=0)
    locations_guessed: so.Mapped[int] = so.mapped_column(default=0)
    correct_guesses: so.Mapped[int] = so.mapped_column(default=0)

    guesses: so.Mapped[list["LocationGuess"]] = so.relationship(
        back_populates="game_history",
        cascade="all, delete-orphan"
    )

class Stats(db.Model):
    __tablename__ = "stats"

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), nullable=False)
    win_streak: so.Mapped[Optional[int]] = so.mapped_column(nullable=True)
    total_wins: so.Mapped[Optional[int]] = so.mapped_column(nullable=True)
    win_percentage: so.Mapped[Optional[float]] = so.mapped_column(nullable=True)
    total_games: so.Mapped[Optional[int]] = so.mapped_column(nullable=True)
    time_spent: so.Mapped[int] = so.mapped_column(nullable=False)
    start_date: so.Mapped[datetime] = so.mapped_column(nullable=False)
