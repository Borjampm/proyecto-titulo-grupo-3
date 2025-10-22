from fastapi import FastAPI

from app.deps import lifespan
from app.routers.patients import router as patients_router
from app.routers.clinical_episodes import router as clinical_episodes_router
from app.routers.task_instances import router as task_instances_router

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Hello, world!"}


app.include_router(patients_router)
app.include_router(clinical_episodes_router)
app.include_router(task_instances_router)
