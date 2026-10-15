from fastapi import FastAPI

from src.api.common.exception_handlers import register_exception_handlers

from .create.routes import router as create_router
from .delete.routes import router as delete_router
from .join.routes import router as join_router
from .list.routes import router as list_router
from .retrieve.routes import router as retrieve_router
from .update.routes import router as update_router

app = FastAPI()

app.title = "SessionParticipant APIs"
app.description = "API endpoints for session participant CRUD."

register_exception_handlers(app)

app.include_router(create_router, tags=["SessionParticipant"])
app.include_router(join_router, tags=["SessionParticipant"])
app.include_router(list_router, tags=["SessionParticipant"])
app.include_router(retrieve_router, tags=["SessionParticipant"])
app.include_router(update_router, tags=["SessionParticipant"])
app.include_router(delete_router, tags=["SessionParticipant"])
