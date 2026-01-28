from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db import engine, Base
from backend.upload import router as upload_router
from backend.download import router as download_router
from backend.routes.share import router as share_router
from backend.routes.files import router as files_router
from backend.routes.delete import router as delete_router
from backend.jobs.cleanup import cleanup_abandoned_uploads

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup logic
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    try:
        cleanup_abandoned_uploads(hours=6)
    except Exception as e:
        print("Cleanup job skipped:", e)

# Routers
app.include_router(upload_router)
app.include_router(download_router)
app.include_router(share_router)
app.include_router(files_router)
app.include_router(delete_router)

# Health check
@app.get("/")
def root():
    return {"message": "Backend Running ✅"}
