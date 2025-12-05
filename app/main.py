from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from app.routers.instructors import router as instructors_router
from app.routers.students import router as students_router
from app.routers.cohorts import router as cohorts_router
from app.routers.locations import router as locations_router
from app.routers.instructor_hours import router as instructor_hours_router
from app.routers.credentials import router as credentials_router
from app.routers.tools import router as tools_router
from app.routers.jatc_applications import router as jatc_router


# ------------------------------------------------------------
# Initialize FastAPI
# ------------------------------------------------------------
app = FastAPI(
    title="IP2A Database API",
    description="Backend API for the IBEW IP2A Program",
    version="2.0.0",
)


# ------------------------------------------------------------
# CORS (allow frontend development)
# ------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# Root + health check
# ------------------------------------------------------------
@app.get("/")
def root():
    return {"message": "IP2A API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ------------------------------------------------------------
# Register Routers
# ------------------------------------------------------------
app.include_router(instructors_router)
app.include_router(students_router)
app.include_router(cohorts_router)
app.include_router(locations_router)
app.include_router(instructor_hours_router)
app.include_router(credentials_router)
app.include_router(tools_router)
app.include_router(jatc_router)
