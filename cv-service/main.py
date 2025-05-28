# cv-service/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import your modules here
from modules.workout_routine_api import router as workout_router

# Create FastAPI app
app = FastAPI(
    title="B-Fit CV Service API",
    description="Computer Vision service for B-Fit health app",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
        "http://localhost:3001",  # Alternative React port
        # Add your production URLs here later
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workout_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "B-Fit CV Service API",
        "version": "1.0.0",
        "endpoints": {
            "workout": "/api/workout",
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

# Placeholder endpoints for future modules
@app.get("/api/pose")
async def pose_analysis_placeholder():
    return {
        "message": "Pose analysis endpoint - Coming soon",
        "status": "not_implemented"
    }

@app.get("/api/ocr")
async def ocr_placeholder():
    return {
        "message": "OCR processing endpoint - Coming soon",
        "status": "not_implemented"
    }

# When you're ready to add your other modules, uncomment and import them:
# from modules.yolo_detector import router as yolo_router
# from modules.pose_analyzer import router as pose_router
# from modules.ocr_processor import router as ocr_router
# from modules.exercise_analyzer import router as exercise_router
# from modules.routine_integration import router as integration_router

# app.include_router(yolo_router)
# app.include_router(pose_router)
# app.include_router(ocr_router)
# app.include_router(exercise_router)
# app.include_router(integration_router)

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True  # Enable auto-reload during development
    )