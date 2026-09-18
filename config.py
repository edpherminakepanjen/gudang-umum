import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "gu-rsh-kepanjen-secret-2026")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "gudang_umum.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = 60 * 60 * 8  # 8 hours

    # Branding
    APP_NAME = "Gudang Umum (GU)"
    APP_FULL_NAME = "Gudang Umum (GU) — RS Hermina Kepanjen"
    APP_SHORT = "Gudang Umum"
    HOSPITAL = "RS Hermina Kepanjen"
    FOOTER_LINE = "Gudang Umum RS Hermina Kepanjen"
    POWERED_BY = "Powered by IT RSH Kepanjen"
    TIMEZONE = "WIB"
