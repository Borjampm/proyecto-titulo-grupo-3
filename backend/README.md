# Backend FastAPI Service

This project is managed with [uv](https://github.com/astral-sh/uv) and exposes a simple FastAPI application that responds with a "Hello, world!" message at the root path (`/`).

## Prerequisites
- Python 3.10 or newer
- `uv` CLI installed (`pip install uv` or see the uv documentation for alternative installation methods)

## Setup
Use uv to create the virtual environment and install dependencies:

```bash
uv sync
```

This will create a `.venv` directory pinned to the dependencies listed in `uv.lock`.

## Test Environment

To build the test database using docker, run the following command:

```bash
docker build -f Dockerfile.postgress_test -t my-postgres14 .
```

Then, to run it, run the following command:

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

The database will be available with url:

```
postgresql://admin:admin@localhost:5432/mydatabase
```

To stop the test database, run the following command:

```bash
docker stop test-database
```

To remove the test database, run the following command:

```bash
docker rm test-database
```

To remove the test database volume, run the following command:

```bash
docker volume rm pgdata
```

## Running the server
Start the FastAPI application with uv and Uvicorn:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at http://127.0.0.1:8000/ and the `/` endpoint returns:

```json
{"message": "Hello, world!"}
```

## Updating dependencies
To add or upgrade packages, use uv commands (e.g., `uv add fastapi`). After updating dependencies, commit both `pyproject.toml` and `uv.lock`.

## Migrations
This project uses Alembic for migrations. Here are some common commands when using Alembic:

```bash
alembic init alembic              # set up Alembic
alembic revision -m "message"     # create empty migration
alembic revision --autogenerate -m "message"  # detect changes
alembic upgrade head              # apply migrations
alembic downgrade -1              # revert last migration
alembic history                   # see all migrations
alembic current                   # check current version
```