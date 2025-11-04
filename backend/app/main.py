from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <-- 1. IMPORT THIS

from app.deps import lifespan
from app.routers.patients import router as patients_router
from app.routers.clinical_episodes import router as clinical_episodes_router
from app.routers.task_instances import router as task_instances_router
from app.routers.excel_upload import router as excel_upload_router

app = FastAPI(lifespan=lifespan)

# Esto es para cambiar CORS. Eventualmente deberíamos cambiar
# origins para que contenga sólo el dominio de nuestro (eventual)
# frontend. Por ahora, simplemente haré que acepte cualquier origen.
origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Specifies the allowed origins
    allow_credentials=True,    # Allows cookies/auth headers
    allow_methods=["*"],       # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],       # Allows all headers
)

@app.get("/")
async def read_root() -> dict[str, str]:
    return {"message": "Hello, world!"}


app.include_router(patients_router)
app.include_router(clinical_episodes_router)
app.include_router(task_instances_router)
app.include_router(excel_upload_router)

