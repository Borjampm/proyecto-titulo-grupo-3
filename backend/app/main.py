from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from app.deps import lifespan
from app.routers.patients import router as patients_router
from app.routers.clinical_episodes import router as clinical_episodes_router
from app.routers.task_instances import router as task_instances_router
from app.routers.excel_upload import router as excel_upload_router
from app.routers.workers import router as workers_router
from app.routers.documents import router as documents_router
from app.routers.alerts import router as alerts_router

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

@app.get("/", response_class=PlainTextResponse)
async def read_root() -> str:
    return """
The lion does not concern himself with approval before merging to main.
            
            **********  ******
        **************************
      ******************************
    ****    ****            ****    **
    ****  ****                ****  **
  **********                    ********
  **********  ****        ****  ********
************      **    **      ********
************      **    **      ********
************      **    **    **********
**************    ********    **********
  ************        **      ********
    ************    ******  **********
    ****************      ************
      **************      **********
        **************************
            ********************
                **************
                  **********
                      ****
"""


app.include_router(patients_router)
app.include_router(clinical_episodes_router)
app.include_router(task_instances_router)
app.include_router(excel_upload_router)
app.include_router(workers_router)
app.include_router(documents_router)
app.include_router(alerts_router)

