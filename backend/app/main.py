from fastapi import FastAPI

from app.deps import lifespan
from app.routers.patients import router as patients_router

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Hello, world!"}


app.include_router(patients_router)
