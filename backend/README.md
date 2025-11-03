# Backend FastAPI Service

A modern, async FastAPI application for patient management with PostgreSQL database, SQLAlchemy ORM, and Alembic migrations.

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Running with Docker](#running-with-docker)
- [API Documentation](#api-documentation)
- [Database Migrations](#database-migrations)
- [Development](#development)
- [Testing](#testing)
- [Additional Resources](#additional-resources)

## Prerequisites

- **Python 3.12 or newer**
- **[uv](https://github.com/astral-sh/uv)** - Modern Python package manager
  ```bash
  # Install uv (choose one method)
  pip install uv
  # or
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Docker** (for running PostgreSQL test database)
- **PostgreSQL 14+** (or use Docker setup below)

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and settings
│   ├── db.py                # Database connection and Base
│   ├── deps.py              # Dependency injection (sessions, auth, etc.)
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── patient.py
│   ├── routers/             # API route handlers
│   │   └── patients.py
│   └── schemas/             # Pydantic models for validation
│       ├── __init__.py
│       └── patient.py
├── alembic/                 # Database migration files
│   ├── versions/
│   └── env.py
├── alembic.ini              # Alembic configuration
├── pyproject.toml           # Project dependencies and metadata
├── uv.lock                  # Locked dependency versions
└── README.md
```

## 🚀 Setup

### 1. Clone and Navigate

```bash
cd backend
```

### 2. Install Dependencies

Use `uv` to create a virtual environment and install all dependencies:

```bash
uv sync
```

This will:
- Create a `.venv` directory in your project
- Install all dependencies from `uv.lock`
- Set up the project in development mode

### 3. Activate Virtual Environment

```bash
# On macOS/Linux
source .venv/bin/activate

# On Windows
.venv\Scripts\activate
```

## ⚙️ Environment Configuration

Create a `.env` file in the backend directory:

```bash
cp .env.test_template .env
```

**Important:** Update the `.env` file with the correct DATABASE_URL format for async PostgreSQL:

```env
# ⚠️ Note the +asyncpg in the URL - required for async operations
DATABASE_URL=postgresql+asyncpg://admin:admin@localhost:5432/mydatabase
```

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string with `+asyncpg` driver | - | ✅ Yes |

## 🗄️ Database Setup

### Option 1: Docker PostgreSQL (Recommended for Development)

#### Build the PostgreSQL Image

```bash
docker build -f Dockerfile.postgres -t my-postgres14 .
```

#### Run the Database Container

```bash
docker run -d \
  --name postgres-database \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin \
  -e POSTGRES_DB=mydatabase \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  my-postgres14
```

#### Verify Database is Running

```bash
docker ps | grep postgres-database
docker logs postgres-database
```

#### Database Connection Details

- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `mydatabase`
- **User:** `admin`
- **Password:** `admin`
- **Full URL:** `postgresql+asyncpg://admin:admin@localhost:5432/mydatabase`

### Option 2: Local PostgreSQL Installation

If you have PostgreSQL installed locally, create a database:

```sql
CREATE DATABASE mydatabase;
CREATE USER admin WITH PASSWORD 'admin';
GRANT ALL PRIVILEGES ON DATABASE mydatabase TO admin;
```

### Initialize Database with Migrations

After setting up PostgreSQL and configuring `.env`, run migrations:

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Verify current migration status
uv run alembic current
```

### Useful Database Commands

```bash
uv run db-seed # Seed the database with sample data
uv run db-reset # Reset the database and seed with sample data
uv run db-clear # Clear the database and recreate it empty
```

## 🏃 Running the Application

### Development Server

Start the FastAPI application with hot reload:

```bash
uv run dev
```
Or alternatively:
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at:
- **API:** http://127.0.0.1:8000/
- **Interactive Docs (Swagger):** http://127.0.0.1:8000/docs
- **Alternative Docs (ReDoc):** http://127.0.0.1:8000/redoc

### Quick Health Check

```bash
curl http://localhost:8000/
# Expected: {"message": "Hello, world!"}
```

## 🐳 Running with Docker

### Build the API Docker Image

```bash
docker build -f Dockerfile.API -t fastapi-backend .
```

### Run the API Container

#### Option 1: Using environment file (Recommended)

Create a `.env` file with your configuration (if not already created):

```env
DATABASE_URL=database_url
```

**Note:** When running the API in Docker, use `host.docker.internal` instead of `localhost` to connect to a database running on your host machine (macOS/Windows). On Linux, use `--network host` or connect to the database container by name if using Docker Compose.

Run the container:

```bash
docker run -d \
  --name fastapi-backend \
  -p 8000:8000 \
  --env-file .env \
  fastapi-backend
```

#### Option 2: Using environment variables directly

```bash
docker run -d \
  --name fastapi-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://admin:admin@host.docker.internal:5432/mydatabase \
  fastapi-backend
```

### Manage the Container

```bash
# View logs
docker logs fastapi-backend

# Follow logs in real-time
docker logs -f fastapi-backend

# Stop the container
docker stop fastapi-backend

# Start the container
docker start fastapi-backend

# Remove the container
docker rm fastapi-backend

# View running containers
docker ps
```

### Run Database Migrations in Container

If you need to run migrations inside the container:

```bash
# Execute migrations
docker exec fastapi-backend alembic upgrade head

# Check current migration version
docker exec fastapi-backend alembic current
```

### Docker Compose (Full Stack - Recommended)

The easiest way to run both the database and API together is using Docker Compose. A `docker-compose.yml` file is already configured in the project.

**What it includes:**
- PostgreSQL 14 database with health checks
- FastAPI backend with automatic migrations on startup
- Persistent database storage
- Isolated network for services
- Proper service dependencies

**Start the full stack:**

```bash
# Build and start all services in detached mode
docker-compose up -d --build

# View all logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api
docker-compose logs -f postgres

# Check service status
docker-compose ps
```

**Test the API:**

```bash
# Health check
curl http://localhost:8000/

# View interactive docs
open http://localhost:8000/docs
```

**Manage the stack:**

```bash
# Stop all services (keeps data)
docker-compose stop

# Start stopped services
docker-compose start

# Stop and remove containers (keeps data)
docker-compose down

# Stop and remove everything including volumes (clean slate)
docker-compose down -v

# Rebuild services after code changes
docker-compose up -d --build

# View resource usage
docker-compose stats
```

**Notes:**
- Database migrations run automatically when the API starts
- Database data persists in a Docker volume named `backend_postgres_data`
- The API waits for the database to be healthy before starting
- Access the API at http://localhost:8000
- Access the database at localhost:5432

## 📚 API Documentation

### Interactive API Documentation

Visit http://localhost:8000/docs to explore the API with Swagger UI, where you can:
- See all available endpoints
- View request/response schemas
- Test API calls directly from the browser

## 🔄 Database Migrations

This project uses Alembic for database schema versioning.

### Common Commands

```bash
# Initialize Alembic (already done)
uv run alembic init alembic

# Create a new empty migration
uv run alembic revision -m "description of changes"

# Auto-generate migration from model changes (recommended)
uv run alembic revision --autogenerate -m "add new field to patients"

# Apply all pending migrations
uv run alembic upgrade head

# Revert the last migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# Check current database version
uv run alembic current

# Show SQL without executing (dry run)
uv run alembic upgrade head --sql
```

### Migration Workflow

1. **Modify your models** in `app/models/`
2. **Generate migration:**
   ```bash
   uv run alembic revision --autogenerate -m "describe changes"
   ```
3. **Review the generated migration** in `alembic/versions/`
4. **Apply the migration:**
   ```bash
   uv run alembic upgrade head
   ```

## 🛠️ Development

### Adding New Dependencies

```bash
# Add a production dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Example: Add pytest for testing
uv add --dev pytest pytest-asyncio httpx
```

After adding dependencies, both `pyproject.toml` and `uv.lock` will be updated. Commit both files.

## 🧪 Testing

This project includes comprehensive endpoint testing with PostgreSQL support.

### Prerequisites

The tests require Docker to run a separate PostgreSQL test database (to avoid conflicts with development data and support PostgreSQL-specific features like JSONB).

### Quick Start

1. **Start the test database:**
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   ```

2. **Run all tests:**
   ```bash
   uv run pytest
   ```

3. **Stop the test database** (when done):
   ```bash
   docker-compose -f docker-compose.test.yml down
   ```

### Common Test Commands

```bash
# Run all tests with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/test_patients.py

# Run specific test function
uv run pytest tests/unit/test_patients.py::TestGetPatients::test_list_patients_empty

# Run with coverage report
uv run pytest --cov=app --cov-report=html
```

Then open `htmlcov/index.html` in your browser to see the coverage report.

**View coverage in terminal:**

```bash
# Show coverage summary with missing lines
uv run pytest --cov=app --cov-report=term-missing

# Show only coverage summary
uv run pytest --cov=app --cov-report=term
```

**Coverage options:**

- `--cov=app` - Measure coverage for the `app` package
- `--cov-report=html` - Generate HTML report (opens `htmlcov/index.html`)
- `--cov-report=term-missing` - Show terminal output with missing line numbers
- `--cov-report=term` - Show only coverage percentage in terminal
- `--cov-report=xml` - Generate XML report (useful for CI/CD)

**Example output:**
```
Name                                          Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------
app/routers/patients.py                          19      3    84%   18, 37-38
app/routers/task_instances.py                    77     44    43%   56-57, 81-89
---------------------------------------------------------------------------
TOTAL                                           753    110    85%
```

This shows:
- **Stmts**: Total statements
- **Miss**: Missed statements
- **Cover**: Coverage percentage
- **Missing**: Line numbers of missed code

### Test Database Configuration

- **Host:** `localhost`
- **Port:** `5433` (different from dev database to avoid conflicts)
- **Database:** `test_db`
- **User:** `test_user`
- **Password:** `test_password`

### Writing Tests

Tests must be **async** since the application uses async database operations:

```python
class TestEndpoint:
    async def test_example(self, client):
        """Test example endpoint."""
        response = await client.get("/endpoint/")
        assert response.status_code == 200
```

For more details, see [tests/README.md](tests/README.md).

## 📝 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [UV Documentation](https://github.com/astral-sh/uv)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 📄 License

[Specify your license here]

---

**Note:** This is a development setup. For production deployment, consider:
- Using environment-specific configuration
- Setting up proper authentication/authorization
- Implementing rate limiting
- Adding monitoring and logging
- Using production-grade WSGI server configuration
- Setting up CI/CD pipelines



