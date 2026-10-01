import os

from dotenv import load_dotenv


BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)


# Load .env file
load_dotenv(
    os.path.join(BASE_DIR, ".env")
)


class Config:

    # Secret key from .env
    SECRET_KEY = os.getenv("SECRET_KEY")

    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not configured."
        )

    # Database
    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///"
        + os.path.join(
            BASE_DIR,
            "secure_files.db"
        )
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload folder
    UPLOAD_FOLDER = os.path.join(
        BASE_DIR,
        "uploads"
    )

    # Maximum file size: 50 MB
    MAX_CONTENT_LENGTH = (
        50 * 1024 * 1024
    )

    # Allowed file types
    ALLOWED_EXTENSIONS = {
        "pdf",
        "doc",
        "docx",
        "txt",
        "csv",
        "xls",
        "xlsx",
        "ppt",
        "pptx",
        "jpg",
        "jpeg",
        "png"
    }