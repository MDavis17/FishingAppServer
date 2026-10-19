import os

# Default: local SQLite for development.
# Production PostgreSQL example:
#   DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/fishing_app
# Optional query params: ?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./users.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = int(os.getenv("JWT_EXPIRY_MINUTES", "60"))
