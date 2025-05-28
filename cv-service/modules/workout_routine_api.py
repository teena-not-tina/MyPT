# cv-service/modules/workout_routine_api.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

router = APIRouter(prefix="/api/workout", tags=["workout"])

# Pydantic models for request/response
class ExerciseSet(BaseModel):
    id: int
    reps: Optional[int] = None
    weight: Optional[float] = None
    time: Optional[str] = None
    completed: bool = False

class Exercise(BaseModel):
    id: int
    name: str
    sets: List[ExerciseSet]

class WorkoutRoutine(BaseModel):
    day: int
    title: str
    exercises: List[Exercise]

class UpdateSetRequest(BaseModel):
    reps: Optional[int] = None
    weight: Optional[float] = None
    time: Optional[str] = None
    completed: Optional[bool] = None

# In-memory storage for testing (replace with database in production)
workout_routines = [
    {
        "day": 1,
        "title": "1일차 - 하체 & 힙 집중",
        "exercises": [
            {
                "id": 1,
                "name": "워밍업: 러닝머신 빠르게 걷기",
                "sets": [{"id": 1, "time": "5분", "completed": False}]
            },
            {
                "id": 2,
                "name": "스미스머신 스쿼트",
                "sets": [
                    {"id": 1, "reps": 12, "weight": 20, "completed": False},
                    {"id": 2, "reps": 12, "weight": 20, "completed": False},
                    {"id": 3, "reps": 12, "weight": 20, "completed": False}
                ]
            },
            {
                "id": 3,
                "name": "레그프레스",
                "sets": [
                    {"id": 1, "reps": 12, "weight": 50, "completed": False},
                    {"id": 2, "reps": 12, "weight": 50, "completed": False},
                    {"id": 3, "reps": 12, "weight": 50, "completed": False}
                ]
            },
            {
                "id": 4,
                "name": "런지 (덤벨 들고)",
                "sets": [
                    {"id": 1, "reps": 10, "weight": 5, "completed": False},
                    {"id": 2, "reps": 10, "weight": 5, "completed": False},
                    {"id": 3, "reps": 10, "weight": 5, "completed": False}
                ]
            },
            {
                "id": 5,
                "name": "레그컬 (누워서 하는 거)",
                "sets": [
                    {"id": 1, "reps": 12, "weight": 20, "completed": False},
                    {"id": 2, "reps": 12, "weight": 20, "completed": False},
                    {"id": 3, "reps": 12, "weight": 20, "completed": False}
                ]
            },
            {
                "id": 6,
                "name": "힙 어브덕션 머신",
                "sets": [
                    {"id": 1, "reps": 15, "weight": 30, "completed": False},
                    {"id": 2, "reps": 15, "weight": 30, "completed": False},
                    {"id": 3, "reps": 15, "weight": 30, "completed": False}
                ]
            },
            {
                "id": 7,
                "name": "마무리: 천국의계단",
                "sets": [{"id": 1, "time": "10-15분", "completed": False}]
            }
        ]
    },
    {
        "day": 2,
        "title": "2일차 - 상체 & 복부",
        "exercises": [
            {
                "id": 8,
                "name": "워밍업: 러닝머신",
                "sets": [{"id": 1, "time": "5분", "completed": False}]
            },
            {
                "id": 9,
                "name": "랫풀다운",
                "sets": [
                    {"id": 1, "reps": 12, "weight": 15, "completed": False},
                    {"id": 2, "reps": 12, "weight": 15, "completed": False},
                    {"id": 3, "reps": 12, "weight": 15, "completed": False}
                ]
            },
            {
                "id": 10,
                "name": "시티드로우",
                "sets": [
                    {"id": 1, "reps": 12, "weight": 20, "completed": False},
                    {"id": 2, "reps": 12, "weight": 20, "completed": False},
                    {"id": 3, "reps": 12, "weight": 20, "completed": False}
                ]
            },
            {
                "id": 11,
                "name": "덤벨 숄더프레스",
                "sets": [
                    {"id": 1, "reps": 12, "weight": 4, "completed": False},
                    {"id": 2, "reps": 12, "weight": 4, "completed": False},
                    {"id": 3, "reps": 12, "weight": 4, "completed": False}
                ]
            },
            {
                "id": 12,
                "name": "케이블 트라이셉스 푸시다운",
                "sets": [
                    {"id": 1, "reps": 15, "weight": 15, "completed": False},
                    {"id": 2, "reps": 15, "weight": 15, "completed": False},
                    {"id": 3, "reps": 15, "weight": 15, "completed": False}
                ]
            },
            {
                "id": 13,
                "name": "복부운동 (플랭크 + 크런치 + 레그레이즈)",
                "sets": [
                    {"id": 1, "time": "30초 + 15회 + 15회", "completed": False},
                    {"id": 2, "time": "30초 + 15회 + 15회", "completed": False},
                    {"id": 3, "time": "30초 + 15회 + 15회", "completed": False}
                ]
            }
        ]
    },
    {
        "day": 3,
        "title": "3일차 - 하체 & 힙 + 유산소",
        "exercises": [
            {
                "id": 14,
                "name": "워밍업: 러닝머신",
                "sets": [{"id": 1, "time": "5분", "completed": False}]
            },
            {
                "id": 15,
                "name": "불가리안 스플릿 스쿼트",
                "sets": [
                    {"id": 1, "reps": 10, "weight": 4, "completed": False},
                    {"id": 2, "reps": 10, "weight": 4, "completed": False},
                    {"id": 3, "reps": 10, "weight": 4, "completed": False}
                ]
            },
            {
                "id": 16,
                "name": "데드리프트",
                "sets": [
                    {"id": 1, "reps": 12, "weight": 20, "completed": False},
                    {"id": 2, "reps": 12, "weight": 20, "completed": False},
                    {"id": 3, "reps": 12, "weight": 20, "completed": False}
                ]
            },
            {
                "id": 17,
                "name": "힙 쓰러스트 머신",
                "sets": [
                    {"id": 1, "reps": 12, "weight": 30, "completed": False},
                    {"id": 2, "reps": 12, "weight": 30, "completed": False},
                    {"id": 3, "reps": 12, "weight": 30, "completed": False}
                ]
            },
            {
                "id": 18,
                "name": "케이블 킥백",
                "sets": [
                    {"id": 1, "reps": 15, "weight": 10, "completed": False},
                    {"id": 2, "reps": 15, "weight": 10, "completed": False},
                    {"id": 3, "reps": 15, "weight": 10, "completed": False}
                ]
            },
            {
                "id": 19,
                "name": "천국의계단",
                "sets": [{"id": 1, "time": "15-20분", "completed": False}]
            }
        ]
    },
    {
        "day": 4,
        "title": "4일차 - 상체 & 복부 + 전신",
        "exercises": [
            {
                "id": 20,
                "name": "워밍업: 러닝머신",
                "sets": [{"id": 1, "time": "5분", "completed": False}]
            },
            {
                "id": 21,
                "name": "체스트프레스",
                "sets": [
                    {"id": 1, "reps": 12, "weight": 25, "completed": False},
                    {"id": 2, "reps": 12, "weight": 25, "completed": False},
                    {"id": 3, "reps": 12, "weight": 25, "completed": False}
                ]
            },
            {
                "id": 22,
                "name": "어깨 레터럴레이즈",
                "sets": [
                    {"id": 1, "reps": 15, "weight": 4, "completed": False},
                    {"id": 2, "reps": 15, "weight": 4, "completed": False},
                    {"id": 3, "reps": 15, "weight": 4, "completed": False}
                ]
            },
            {
                "id": 23,
                "name": "원암 덤벨로우",
                "sets": [
                    {"id": 1, "reps": 12, "weight": 8, "completed": False},
                    {"id": 2, "reps": 12, "weight": 8, "completed": False},
                    {"id": 3, "reps": 12, "weight": 8, "completed": False}
                ]
            },
            {
                "id": 24,
                "name": "케이블 우드쵸퍼",
                "sets": [
                    {"id": 1, "reps": 15, "weight": 15, "completed": False},
                    {"id": 2, "reps": 15, "weight": 15, "completed": False},
                    {"id": 3, "reps": 15, "weight": 15, "completed": False}
                ]
            },
            {
                "id": 25,
                "name": "버피테스트",
                "sets": [
                    {"id": 1, "reps": 10, "completed": False},
                    {"id": 2, "reps": 10, "completed": False},
                    {"id": 3, "reps": 10, "completed": False}
                ]
            },
            {
                "id": 26,
                "name": "마무리: 러닝머신",
                "sets": [{"id": 1, "time": "10분", "completed": False}]
            }
        ]
    }
]

# API Endpoints
@router.get("/routines", response_model=List[WorkoutRoutine])
async def get_all_routines():
    """Get all workout routines"""
    return workout_routines

@router.get("/routines/{day}", response_model=WorkoutRoutine)
async def get_routine_by_day(day: int):
    """Get a specific day's workout routine"""
    routine = next((r for r in workout_routines if r["day"] == day), None)
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    return routine

@router.put("/routines/{day}/exercises/{exercise_id}/sets/{set_id}")
async def update_set(day: int, exercise_id: int, set_id: int, update_data: UpdateSetRequest):
    """Update a specific set's information"""
    routine = next((r for r in workout_routines if r["day"] == day), None)
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    
    exercise = next((e for e in routine["exercises"] if e["id"] == exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} not found")
    
    set_item = next((s for s in exercise["sets"] if s["id"] == set_id), None)
    if not set_item:
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")
    
    # Update only provided fields
    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        set_item[key] = value
    
    return {"message": "Set updated successfully", "set": set_item}

@router.post("/routines/{day}/exercises/{exercise_id}/sets")
async def add_set(day: int, exercise_id: int):
    """Add a new set to an exercise"""
    routine = next((r for r in workout_routines if r["day"] == day), None)
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    
    exercise = next((e for e in routine["exercises"] if e["id"] == exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} not found")
    
    # Copy the last set's properties
    last_set = exercise["sets"][-1] if exercise["sets"] else {}
    new_set_id = max([s["id"] for s in exercise["sets"]]) + 1 if exercise["sets"] else 1
    
    new_set = {"id": new_set_id, "completed": False}
    for key in ["reps", "weight", "time"]:
        if key in last_set:
            new_set[key] = last_set[key]
    
    exercise["sets"].append(new_set)
    
    return {"message": "Set added successfully", "set": new_set}

@router.delete("/routines/{day}/exercises/{exercise_id}/sets/{set_id}")
async def delete_set(day: int, exercise_id: int, set_id: int):
    """Delete a specific set from an exercise"""
    routine = next((r for r in workout_routines if r["day"] == day), None)
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    
    exercise = next((e for e in routine["exercises"] if e["id"] == exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} not found")
    
    exercise["sets"] = [s for s in exercise["sets"] if s["id"] != set_id]
    
    return {"message": "Set deleted successfully"}

@router.delete("/routines/{day}/exercises/{exercise_id}")
async def delete_exercise(day: int, exercise_id: int):
    """Delete an entire exercise from a routine"""
    routine = next((r for r in workout_routines if r["day"] == day), None)
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    
    routine["exercises"] = [e for e in routine["exercises"] if e["id"] != exercise_id]
    
    return {"message": "Exercise deleted successfully"}

@router.post("/routines/{day}/exercises/{exercise_id}/complete-set/{set_id}")
async def toggle_set_completion(day: int, exercise_id: int, set_id: int):
    """Toggle the completion status of a set"""
    routine = next((r for r in workout_routines if r["day"] == day), None)
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    
    exercise = next((e for e in routine["exercises"] if e["id"] == exercise_id), None)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} not found")
    
    set_item = next((s for s in exercise["sets"] if s["id"] == set_id), None)
    if not set_item:
        raise HTTPException(status_code=404, detail=f"Set {set_id} not found")
    
    set_item["completed"] = not set_item.get("completed", False)
    
    return {"message": "Set completion toggled", "completed": set_item["completed"]}

# Integration point for posture correction
@router.post("/routines/camera/analyze")
async def analyze_exercise_posture(exercise_name: str):
    """Endpoint to trigger posture analysis for a specific exercise"""
    # This would integrate with your existing exercise_analyzer.py
    return {
        "message": f"Camera analysis triggered for {exercise_name}",
        "redirect_to": f"/exercise-analysis?exercise={exercise_name}"
    }