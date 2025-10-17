# Backend FastAPI Service

A modern, async FastAPI application for patient management with PostgreSQL database, SQLAlchemy ORM, and Alembic migrations.

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Database Migrations](#database-migrations)
- [Development](#development)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Python 3.10 or newer**
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

# Optional: Add these for future enhancements
DEBUG=True
API_V1_PREFIX=/api/v1
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string with `+asyncpg` driver | - | ✅ Yes |
| `DEBUG` | Enable debug mode | `False` | ❌ No |
| `API_V1_PREFIX` | API version prefix | `/api/v1` | ❌ No |
| `ALLOWED_ORIGINS` | CORS allowed origins (JSON array) | `[]` | ❌ No |

## 🗄️ Database Setup

### Option 1: Docker PostgreSQL (Recommended for Development)

#### Build the PostgreSQL Image

```bash
docker build -f Dockerfile.postgress_test -t my-postgres14 .
```

#### Run the Database Container

```bash
docker run -d \
  --name test-database \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=admin \
  -e POSTGRES_DB=mydatabase \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  my-postgres14
```

#### Verify Database is Running

```bash
docker ps | grep test-database
docker logs test-database
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

## 📚 API Documentation

### Endpoints

#### Root
- **GET /** - Health check / Hello world
  - Response: `{"message": "Hello, world!"}`

#### Patients

- **GET /patients/** - List all patients
  - Response: `Array<Patient>`
  - Example:
    ```bash
    curl http://localhost:8000/patients/
    ```

- **POST /patients/** - Create a new patient
  - Request Body: `PatientCreate`
  - Response: `Patient`
  - Example:
    ```bash
    curl -X POST http://localhost:8000/patients/ \
      -H "Content-Type: application/json" \
      -d '{
        "medical_identifier": "P001",
        "first_name": "Juan",
        "last_name": "Pérez",
        "rut": "12345678-9",
        "birth_date": "1990-01-15",
        "gender": "male"
      }'
    ```

### Data Models

#### Patient Schema

```python
{
  "id": 1,
  "medical_identifier": "P001",
  "first_name": "Juan",
  "last_name": "Pérez",
  "rut": "12345678-9",
  "birth_date": "1990-01-15",
  "gender": "male"
}
```

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

### Code Style

```bash
# Format code (if ruff is installed)
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking (if mypy is installed)
uv run mypy app/
```

### Recommended Development Tools

```bash
uv add --dev ruff mypy pytest pytest-asyncio httpx pytest-cov
```

## 🧪 Testing

### Setup Tests (Future)

```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio httpx pytest-cov

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_patients.py -v
```

### Test Database

For testing, consider using a separate test database:

```env
# .env.test
DATABASE_URL=postgresql+asyncpg://admin:admin@localhost:5432/mydatabase_test
```

## 🔧 Troubleshooting

### Database Connection Issues

**Error:** `asyncpg.exceptions.InvalidPasswordError` or connection refused

**Solutions:**
1. Verify database is running:
   ```bash
   docker ps | grep test-database
   ```
2. Check DATABASE_URL in `.env` uses `postgresql+asyncpg://`
3. Verify credentials match Docker environment variables
4. Test direct connection:
   ```bash
   docker exec -it test-database psql -U admin -d mydatabase
   ```

### Migration Issues

**Error:** `Target database is not up to date`

**Solution:**
```bash
# Check current version
uv run alembic current

# Check history
uv run alembic history

# Upgrade to latest
uv run alembic upgrade head
```

**Error:** `Can't locate revision identified by 'xxxx'`

**Solution:** The migration history is out of sync. You may need to:
```bash
# Stamp the database with current version
uv run alembic stamp head
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'app'`

**Solutions:**
1. Ensure you're in the backend directory
2. Activate the virtual environment
3. Run commands with `uv run` prefix

### Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uv run uvicorn app.main:app --port 8001
```

## 🐳 Docker Commands Reference

### Database Container Management

```bash
# Start existing container
docker start test-database

# Stop container
docker stop test-database

# Remove container
docker rm test-database

# Remove container and volume (⚠️ deletes all data)
docker rm test-database
docker volume rm pgdata

# View logs
docker logs test-database -f

# Access PostgreSQL CLI
docker exec -it test-database psql -U admin -d mydatabase
```

## 📦 Updating Dependencies

```bash
# Update all dependencies to latest compatible versions
uv sync --upgrade

# Update a specific package
uv add package-name@latest

# Lock dependencies without updating
uv lock
```

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Run tests and linters
4. Update documentation
5. Submit a pull request

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
