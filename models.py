from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ==========================================================
# USER MODEL
# ==========================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    # Files owned by user
    files = db.relationship(
        "File",
        backref="owner",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # Files shared with user
    shared_files = db.relationship(
        "FileShare",
        foreign_keys="FileShare.shared_with",
        backref="recipient",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # Activity logs
    activities = db.relationship(
        "ActivityLog",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"


# ==========================================================
# FILE MODEL
# ==========================================================

class File(db.Model):
    __tablename__ = "files"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    filename = db.Column(
        db.String(255),
        nullable=False
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=False
    )

    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    file_hash = db.Column(
        db.String(255),
        nullable=False
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # File shares
    shares = db.relationship(
        "FileShare",
        backref="file",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # Activity logs related to this file
    activities = db.relationship(
        "ActivityLog",
        backref="file",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<File {self.filename}>"


# ==========================================================
# FILE SHARE MODEL
# ==========================================================

class FileShare(db.Model):
    __tablename__ = "file_shares"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    file_id = db.Column(
        db.Integer,
        db.ForeignKey("files.id"),
        nullable=False
    )

    shared_with = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    permission = db.Column(
        db.String(20),
        default="read",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<FileShare {self.file_id} -> {self.shared_with}>"


# ==========================================================
# ACTIVITY LOG MODEL
# ==========================================================

class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    file_id = db.Column(
        db.Integer,
        db.ForeignKey("files.id"),
        nullable=True
    )

    action = db.Column(
        db.String(50),
        nullable=False
    )

    details = db.Column(
        db.String(255),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<ActivityLog {self.action}>"