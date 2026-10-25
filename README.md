# FishingAppServer

A FastAPI backend for a fishing app that tracks trips, catches, and species information.

## Database

### Overview

This app uses **PostgreSQL** hosted on [Neon](https://neon.tech). Neon provides serverless Postgres with connection pooling (PgBouncer).

- **ORM**: SQLAlchemy 2.x
- **Migrations**: Alembic
- **Driver**: psycopg2-binary

### Environment Variables

Database credentials are loaded from `.env.local` (created by `neon deploy`) or `.env`:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Pooled connection string (for app queries) |
| `DATABASE_URL_UNPOOLED` | Direct connection string (for migrations) |
| `NEON_BRANCH` | Current Neon branch name |

### Schema

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users       │       │     trips       │       │    catches      │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──────<│ user_id (FK)    │       │ id (PK)         │
│ email           │       │ id (PK)         │──────<│ trip_id (FK)    │
│ password_hash   │       │ date            │       │ user_id (FK)    │
│ google_id       │       │ status          │       │ date_time       │
│ created_at      │       │ location_name   │       │ species         │
│ is_active       │       │ location_lat    │       │ water_type      │
└─────────────────┘       │ location_lng    │       │ bait            │
                          │ created_at      │       │ location_*      │
                          └─────────────────┘       │ weight, length  │
                                   │                └─────────────────┘
                                   │
                          ┌────────┴────────┐
                          │trip_target_species│ (M2M)
                          └────────┬────────┘
                                   │
┌─────────────────┐       ┌────────┴────────┐       ┌─────────────────┐
│    regions      │       │    species      │       │ user_favorites  │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │──────<│ species_id (FK) │
│ name            │       │ name            │       │ user_id (FK)    │
└────────┬────────┘       │ scientific_name │       │ created_at      │
         │                │ avg_length      │       └─────────────────┘
         │                │ lifespan        │
┌────────┴────────┐       │ depth_range     │
│ species_regions │ (M2M) │ image           │
└────────┬────────┘       │ kingdom         │
         └───────────────>└─────────────────┘
```

### Local Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up Neon (if not already done)
npx neon@latest init -y --org-id <org-id> --project-id <project-id> --branch production --services postgres
npx neon@latest deploy

# 4. Run migrations
alembic upgrade head

# 5. Start the server
uvicorn app.main:app --reload
```

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "description of changes"

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Interacting with the Database

#### Via Python Shell

```python
source venv/bin/activate
python3

>>> from app.Auth.database import SessionLocal, engine
>>> from app.models.db_models import Species, Trip, CatchEntry
>>> from app.Auth.models import User

>>> db = SessionLocal()

# Query all users
>>> db.query(User).all()

# Query species by name
>>> db.query(Species).filter(Species.name.ilike('%bass%')).all()

# Get a user's trips
>>> db.query(Trip).filter(Trip.user_id == 1).all()

# Get catches for a trip
>>> db.query(CatchEntry).filter(CatchEntry.trip_id == 1).all()

>>> db.close()
```

#### Via psql (Direct Connection)

```bash
# Get connection string from .env.local, then:
psql "postgresql://user:pass@host/db?sslmode=require"

# Common queries
\dt                          -- List all tables
\d+ species                  -- Describe species table
SELECT * FROM users;         -- List users
SELECT * FROM species LIMIT 10;
SELECT COUNT(*) FROM catches;
```

#### Via Neon Console

1. Go to [console.neon.tech](https://console.neon.tech)
2. Select project `raspy-glade-29883523`
3. Use the SQL Editor for queries

### API Endpoints (Database Operations)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create user |
| POST | `/auth/login` | Authenticate user |
| GET | `/species/` | List species (auth required) |
| GET | `/trips/` | List user's trips |
| POST | `/trips/` | Create a trip |
| GET | `/catch/` | List user's catches |
| POST | `/catch/` | Log a catch |

API docs available at `http://localhost:8000/docs` when running locally.

---

## Range Map Tools

Building a range map:
download a csv with lat, long, probability

# start processing env

source fishmaps/bin/activate

# Multiple polygons per band (default 5° clustering)

python3 probability_bands_to_kml.py input.csv output.kml --name "Species" --alpha 0.8

# Tighter clusters → more, smaller polygons

python3 probability_bands_to_kml.py input.csv output.kml --cluster-distance 3

# Looser clusters → fewer, larger polygons

python3 probability_bands_to_kml.py input.csv output.kml --cluster-distance 10

# Single polygon per band (no clustering)

python3 probability_bands_to_kml.py input.csv output.kml --cluster-distance 0

# Different distances per band:

python probability_bands_to_kml.py in.csv out.kml --cluster-distance-low 3 --cluster-distance-mid 5

All bands use 5°:
python probability_bands_to_kml.py in.csv out.kml
or
python probability_bands_to_kml.py in.csv out.kml --cluster-distance 5
Different distances per band:
python probability_bands_to_kml.py in.csv out.kml --cluster-distance-low 3 --cluster-distance-mid 5 --cluster-distance-high 8
Only override one band:
python probability_bands_to_kml.py in.csv out.kml --cluster-distance 5 --cluster-distance-high 10
