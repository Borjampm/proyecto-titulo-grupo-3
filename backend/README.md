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
