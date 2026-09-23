from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_chat, routes_upload
from app.core.config import settings
from app.core.logger import logger

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-ready RAG application API",
    version="1.0.0"
)

# Global Exception Handler (Senior Engineering Practice)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches all unhandled exceptions, logs the full stack trace securely on the backend,
    and returns a standardized, safe 500 error to the client without leaking internal details.
    """
    logger.error(f"Unhandled Exception at {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Our engineers have been notified."},
    )

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.PROJECT_NAME} API Server...")

# Set up CORS for React frontend (defaulting to allow all for local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes_chat.router, prefix="/api", tags=["chat"])
app.include_router(routes_upload.router, prefix="/api", tags=["upload"])

@app.get("/")
def read_root():
    logger.info("Health check endpoint pinged.")
    return {"message": "Welcome to the Production RAG API"}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
