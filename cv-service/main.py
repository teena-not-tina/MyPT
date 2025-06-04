# cv-service/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import uvicorn

# Import your modules here
from modules.workout_routine_api import router as workout_router
from modules.exercise_api import router as exercise_router
from modules.exercise_websocket import router as websocket_router  # NEW!

from modules.workout_routine_api import router as workout_router
from modules.workout_routine_api import connect_to_mongo, close_mongo_connection

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


# Create FastAPI app
app = FastAPI(
    title="B-Fit CV Service API",
    description="Computer Vision service for B-Fit health app",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - IMPORTANT: Make sure your React app URL is included
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workout_router)
app.include_router(exercise_router)
app.include_router(websocket_router)  # NEW! WebSocket support

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "B-Fit CV Service API",
        "version": "1.0.0",
        "endpoints": {
            "workout": "/api/workout",
            "exercise": "/exercise",
            "websocket": "/api/workout/ws",  # NEW!
            "docs": "/docs",
            "health": "/health"
        }
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": {
            "workout_api": "active",
            "exercise_api": "active",
            "websocket": "active"
        }
    }


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True  # Enable auto-reload during development
    )