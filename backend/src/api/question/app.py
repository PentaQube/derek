from fastapi import FastAPI

from src.api.common.exception_handlers import register_exception_handlers

from .create.routes import router as create_router
from .delete.routes import router as delete_router
from .list.routes import router as list_router
from .retrieve.routes import router as retrieve_router
from .update.routes import router as update_router

app = FastAPI()


# Update document
app.title = "Derek Community APIs"
app.description = "API endpoints for question CRUD."

# Register the exception handlers
register_exception_handlers(app)

app.include_router(create_router, tags=["Question"], prefix="")
app.include_router(delete_router, tags=["Question"], prefix="")
app.include_router(list_router, tags=["Question"], prefix="")
app.include_router(retrieve_router, tags=["Question"], prefix="")
app.include_router(update_router, tags=["Question"], prefix="")
