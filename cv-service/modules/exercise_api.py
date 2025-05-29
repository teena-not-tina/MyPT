# exercise_api.py (The Server Endpoints)

# What it does: Creates web endpoints for your React app to talk to
# Think of it as: A waiter that takes requests from your frontend and returns exercise feedback
# To use: Add to your cv-service/main.py file

from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import cv2
import numpy as np
import io
import json
import asyncio
from typing import Optional
import base64
from PIL import Image

from .exercise_analyzer import ExerciseAnalyzer, Exercise, PostureFeedback


router = APIRouter(prefix="/exercise", tags=["exercise"])

# Global analyzer instance (you might want to manage this differently in production)
analyzer = ExerciseAnalyzer()


@router.post("/analyze-frame")
async def analyze_exercise_frame(
    file: UploadFile = File(...),
    exercise: str = "PUSHUP"
):
    """
    Analyze a single frame for exercise posture.
    
    Args:
        file: Image file (JPEG/PNG)
        exercise: Exercise type (PUSHUP, SQUAT, LEG_RAISE, DUMBBELL_CURL, ONE_ARM_ROW, PLANK)
    
    Returns:
        JSON with posture feedback
    """
    try:
        # Validate exercise type
        try:
            exercise_enum = Exercise[exercise.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid exercise type: {exercise}")
        
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Analyze exercise
        feedback = analyzer.analyze_exercise(frame, exercise_enum)
        
        if feedback is None:
            return {
                "success": False,
                "message": "No pose detected in image",
                "feedback": None
            }
        
        # Convert feedback to JSON-serializable format
        return {
            "success": True,
            "feedback": {
                "is_correct": feedback.is_correct,
                "messages": feedback.feedback_messages,
                "angles": feedback.angle_data,
                "confidence": feedback.confidence
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-video")
async def analyze_exercise_video(
    file: UploadFile = File(...),
    exercise: str = "PUSHUP",
    output_format: str = "json"
):
    """
    Analyze a video for exercise posture.
    
    Args:
        file: Video file (MP4, AVI, etc.)
        exercise: Exercise type
        output_format: "json" for frame-by-frame data or "video" for annotated video
    
    Returns:
        JSON with analysis results or annotated video stream
    """
    try:
        # Validate exercise type
        try:
            exercise_enum = Exercise[exercise.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid exercise type: {exercise}")
        
        # Save uploaded file temporarily
        contents = await file.read()
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Process video
        cap = cv2.VideoCapture(temp_path)
        
        if output_format == "json":
            # Return frame-by-frame analysis
            results = []
            frame_num = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Skip frames for performance
                if frame_num % 5 == 0:  # Analyze every 5th frame
                    feedback = analyzer.analyze_exercise(frame, exercise_enum)
                    if feedback:
                        results.append({
                            "frame": frame_num,
                            "timestamp": frame_num / cap.get(cv2.CAP_PROP_FPS),
                            "is_correct": feedback.is_correct,
                            "messages": feedback.feedback_messages,
                            "angles": feedback.angle_data,
                            "confidence": feedback.confidence
                        })
                
                frame_num += 1
            
            cap.release()
            analyzer.reset_exercise_state()
            
            return {
                "success": True,
                "total_frames": frame_num,
                "analyzed_frames": len(results),
                "final_rep_count": analyzer.rep_count,
                "analysis": results
            }
            
        else:  # output_format == "video"
            # Return annotated video
            # This is more complex - you'd need to process and stream the video
            # For now, return a message
            cap.release()
            return {
                "success": False,
                "message": "Video output format not yet implemented. Use 'json' format."
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if 'temp_path' in locals():
            import os
            os.remove(temp_path)


@router.websocket("/live-analysis")
async def websocket_live_analysis(websocket: WebSocket):
    """
    WebSocket endpoint for real-time exercise analysis.
    
    Client sends:
    {
        "type": "frame",
        "exercise": "PUSHUP",
        "data": "base64_encoded_image"
    }
    
    Server responds:
    {
        "type": "feedback",
        "feedback": { ... },
        "annotated_frame": "base64_encoded_image"
    }
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive frame data
            data = await websocket.receive_json()
            
            if data["type"] == "frame":
                try:
                    # Decode base64 image
                    image_data = base64.b64decode(data["data"])
                    nparr = np.frombuffer(image_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    # Get exercise type
                    try:
                        exercise_enum = Exercise[data["exercise"].upper()]
                    except KeyError:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Invalid exercise type: {data['exercise']}"
                        })
                        continue
                    
                    # Analyze frame
                    feedback = analyzer.analyze_exercise(frame, exercise_enum)
                    
                    # Draw landmarks on frame
                    annotated_frame = analyzer.draw_landmarks(frame, include_feedback=True, feedback=feedback)
                    
                    # Encode annotated frame to base64
                    _, buffer = cv2.imencode('.jpg', annotated_frame)
                    annotated_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    if feedback:
                        # Send feedback with annotated frame
                        await websocket.send_json({
                            "type": "feedback",
                            "feedback": {
                                "is_correct": feedback.is_correct,
                                "messages": feedback.feedback_messages,
                                "angles": feedback.angle_data,
                                "confidence": feedback.confidence
                            },
                            "annotated_frame": annotated_base64
                        })
                    else:
                        await websocket.send_json({
                            "type": "feedback",
                            "feedback": None,
                            "message": "No pose detected",
                            "annotated_frame": annotated_base64
                        })
                except Exception as frame_error:
                    print(f"Error processing frame: {frame_error}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Error processing frame: {str(frame_error)}"
                    })
                    
            elif data["type"] == "reset":
                analyzer.reset_exercise_state()
                await websocket.send_json({
                    "type": "reset",
                    "message": "Exercise state reset"
                })
                
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass


@router.get("/exercises")
async def get_available_exercises():
    """Get list of available exercises."""
    return {
        "exercises": [
            {
                "id": exercise.name,
                "name": exercise.value,
                "description": get_exercise_description(exercise)
            }
            for exercise in Exercise
        ]
    }


def get_exercise_description(exercise: Exercise) -> str:
    """Get description for each exercise."""
    descriptions = {
        Exercise.PUSHUP: "Upper body exercise targeting chest, shoulders, and triceps",
        Exercise.SQUAT: "Lower body exercise targeting quadriceps, hamstrings, and glutes",
        Exercise.LEG_RAISE: "Core exercise targeting lower abdominals",
        Exercise.DUMBBELL_CURL: "Arm exercise targeting biceps",
        Exercise.ONE_ARM_ROW: "Back exercise targeting lats and middle back",
        Exercise.PLANK: "Core stability exercise targeting entire core"
    }
    return descriptions.get(exercise, "")


# Add to your main FastAPI app in cv-service/main.py:
# from modules.exercise_api import router as exercise_router
# app.include_router(exercise_router)