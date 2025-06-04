# cv-service/modules/exercise_websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from typing import Dict, List, Optional
import traceback

from .exercise_analyzer import Exercise, PostureFeedback

router = APIRouter(prefix="/api/workout", tags=["websocket"])

class LandmarkAnalyzer:
    """Lightweight analyzer that works with landmark data only"""
    
    def __init__(self):
        self.rep_count = 0
        self.exercise_state = "ready"
        self.target_reps = None
        
    def calculate_angle(self, a, b, c):
        """Calculate angle between three points"""
        import numpy as np
        
        a = np.array([a['x'], a['y']])
        b = np.array([b['x'], b['y']])
        c = np.array([c['x'], c['y']])
        
        ba = a - b
        bc = c - b
        
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return np.degrees(angle)
    
    def analyze_pushup(self, landmarks: List[Dict]) -> Dict:
        """Analyze pushup form from landmarks"""
        # MediaPipe landmark indices
        LEFT_SHOULDER = 11
        RIGHT_SHOULDER = 12
        LEFT_ELBOW = 13
        RIGHT_ELBOW = 14
        LEFT_WRIST = 15
        RIGHT_WRIST = 16
        LEFT_HIP = 23
        RIGHT_HIP = 24
        LEFT_ANKLE = 27
        RIGHT_ANKLE = 28
        
        feedback_messages = []
        is_correct = True
        
        # Calculate elbow angles
        left_elbow_angle = self.calculate_angle(
            landmarks[LEFT_SHOULDER],
            landmarks[LEFT_ELBOW],
            landmarks[LEFT_WRIST]
        )
        right_elbow_angle = self.calculate_angle(
            landmarks[RIGHT_SHOULDER],
            landmarks[RIGHT_ELBOW],
            landmarks[RIGHT_WRIST]
        )
        avg_elbow_angle = (left_elbow_angle + right_elbow_angle) / 2
        
        # Calculate body alignment
        mid_shoulder = {
            'x': (landmarks[LEFT_SHOULDER]['x'] + landmarks[RIGHT_SHOULDER]['x']) / 2,
            'y': (landmarks[LEFT_SHOULDER]['y'] + landmarks[RIGHT_SHOULDER]['y']) / 2
        }
        mid_hip = {
            'x': (landmarks[LEFT_HIP]['x'] + landmarks[RIGHT_HIP]['x']) / 2,
            'y': (landmarks[LEFT_HIP]['y'] + landmarks[RIGHT_HIP]['y']) / 2
        }
        mid_ankle = {
            'x': (landmarks[LEFT_ANKLE]['x'] + landmarks[RIGHT_ANKLE]['x']) / 2,
            'y': (landmarks[LEFT_ANKLE]['y'] + landmarks[RIGHT_ANKLE]['y']) / 2
        }
        
        body_alignment_angle = self.calculate_angle(mid_shoulder, mid_hip, mid_ankle)
        
        # Form checks
        if avg_elbow_angle > 120:
            feedback_messages.append("팔을 더 굽혀주세요 (90도 목표)")
            is_correct = False
        elif avg_elbow_angle < 70:
            feedback_messages.append("너무 낮게 내려가지 마세요")
        
        if abs(body_alignment_angle - 180) > 15:
            if body_alignment_angle < 165:
                feedback_messages.append("엉덩이를 올려 일직선을 유지하세요")
            else:
                feedback_messages.append("엉덩이를 내려 일직선을 유지하세요")
            is_correct = False
        
        # Rep counting
        if avg_elbow_angle < 100 and self.exercise_state != "down":
            self.exercise_state = "down"
        elif avg_elbow_angle > 150 and self.exercise_state == "down":
            self.exercise_state = "up"
            self.rep_count += 1
        
        return {
            "isCorrect": is_correct,
            "messages": feedback_messages,
            "angleData": {
                "elbowAngle": avg_elbow_angle,
                "bodyAlignment": body_alignment_angle
            }
        }
    
    def analyze_squat(self, landmarks: List[Dict]) -> Dict:
        """Analyze squat form from landmarks"""
        LEFT_HIP = 23
        RIGHT_HIP = 24
        LEFT_KNEE = 25
        RIGHT_KNEE = 26
        LEFT_ANKLE = 27
        RIGHT_ANKLE = 28
        
        feedback_messages = []
        is_correct = True
        
        # Calculate knee angles
        left_knee_angle = self.calculate_angle(
            landmarks[LEFT_HIP],
            landmarks[LEFT_KNEE],
            landmarks[LEFT_ANKLE]
        )
        right_knee_angle = self.calculate_angle(
            landmarks[RIGHT_HIP],
            landmarks[RIGHT_KNEE],
            landmarks[RIGHT_ANKLE]
        )
        avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
        
        # Form checks
        if avg_knee_angle > 110:
            feedback_messages.append("더 깊게 앉으세요 (90도 목표)")
            is_correct = False
        elif avg_knee_angle < 70:
            feedback_messages.append("너무 깊게 앉지 마세요")
        
        # Check knee position
        if landmarks[LEFT_KNEE]['x'] < landmarks[LEFT_ANKLE]['x'] - 0.1:
            feedback_messages.append("무릎이 너무 앞으로 나가지 않도록 하세요")
            is_correct = False
        
        # Rep counting
        if avg_knee_angle < 100 and self.exercise_state != "down":
            self.exercise_state = "down"
        elif avg_knee_angle > 160 and self.exercise_state == "down":
            self.exercise_state = "up"
            self.rep_count += 1
        
        return {
            "isCorrect": is_correct,
            "messages": feedback_messages,
            "angleData": {
                "kneeAngle": avg_knee_angle
            }
        }
    
    def analyze_exercise(self, exercise: str, landmarks: List[Dict]) -> Dict:
        """Route to appropriate exercise analyzer"""
        if exercise == "푸시업":
            return self.analyze_pushup(landmarks)
        elif exercise == "스쿼트":
            return self.analyze_squat(landmarks)
        else:
            # Add more exercises as needed
            return {
                "isCorrect": True,
                "messages": ["운동을 계속하세요"],
                "angleData": {}
            }
    
    def reset(self):
        """Reset exercise state"""
        self.rep_count = 0
        self.exercise_state = "ready"


@router.websocket("/ws/analyze")
async def websocket_analyze(websocket: WebSocket):
    """WebSocket endpoint for real-time posture analysis"""
    await websocket.accept()
    
    analyzer = LandmarkAnalyzer()
    exercise_name = None
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_json()
            
            if data['type'] == 'init':
                # Initialize exercise
                exercise_name = data.get('exercise')
                analyzer.target_reps = data.get('targetReps', 10)
                analyzer.reset()
                
                await websocket.send_json({
                    "type": "status",
                    "message": f"{exercise_name} 분석 시작",
                    "status": "ready"
                })
                
            elif data['type'] == 'landmarks':
                # Analyze landmarks
                if not exercise_name:
                    continue
                
                landmarks = data['landmarks']
                
                # Quick validation
                if not landmarks or len(landmarks) < 33:
                    continue
                
                # Analyze form
                feedback = analyzer.analyze_exercise(exercise_name, landmarks)
                
                # Check if exercise complete
                is_complete = False
                if analyzer.target_reps and analyzer.rep_count >= analyzer.target_reps:
                    is_complete = True
                
                # Send feedback
                await websocket.send_json({
                    "type": "feedback",
                    "feedback": feedback,
                    "repCount": analyzer.rep_count,
                    "isComplete": is_complete
                })
                
            elif data['type'] == 'reset':
                # Reset exercise
                analyzer.reset()
                await websocket.send_json({
                    "type": "status",
                    "message": "리셋 완료",
                    "repCount": 0
                })
                
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        print(traceback.format_exc())
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# Health check endpoint
@router.get("/ws/health")
async def websocket_health():
    """Check if WebSocket service is available"""
    return {
        "status": "healthy",
        "endpoint": "/api/workout/ws/analyze",
        "protocol": "ws"
    }