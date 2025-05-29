# cv-service/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import your modules here
from modules.workout_routine_api import router as workout_router
from modules.exercise_api import router as exercise_router

# Create FastAPI app
app = FastAPI(
    title="B-Fit CV Service API",
    description="Computer Vision service for B-Fit health app",
    version="1.0.0"
)

# Configure CORS - IMPORTANT: Make sure your React app URL is included
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "*"  # Allow all origins during development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - THIS IS THE KEY PART
app.include_router(workout_router)
app.include_router(exercise_router)  # This includes all the exercise analysis endpoints

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "B-Fit CV Service API",
        "version": "1.0.0",
        "endpoints": {
            "workout": "/api/workout",
            "exercise": "/exercise",
            "docs": "/docs",
            "health": "/health"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "cv-service"
    }

# This endpoint is now redundant since exercise_router already provides these
# But keeping it for backward compatibility or as a summary endpoint
@app.get("/api/pose")
async def pose_analysis_placeholder():
    """Get available pose analysis exercises"""
    from modules.exercise_analyzer import Exercise
    
    exercises = [{"id": ex.name, "name": ex.value} for ex in Exercise]
    return {
        "message": "Pose analysis is available",
        "status": "active",
        "available_exercises": exercises,
        "endpoints": {
            "analyze_frame": "/exercise/analyze-frame",
            "analyze_video": "/exercise/analyze-video", 
            "live_analysis": "/exercise/live-analysis",
            "websocket": "ws://localhost:8001/exercise/live-analysis"
        }
    }

@app.get("/api/ocr")
async def ocr_placeholder():
    return {
        "message": "OCR processing endpoint - Coming soon",
        "status": "not_implemented"
    }

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True  # Enable auto-reload during development
    )