# cv-service/modules/workout_routine_api.py

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
import os
from datetime import datetime

router = APIRouter(prefix="/api/workout", tags=["workout"])

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://root:example@192.168.0.199:27017/?authSource=admin")
MONGO_DB = os.getenv("MONGO_DB", "test")

class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

mongodb = MongoDB()

async def get_database() -> AsyncIOMotorDatabase:
    return mongodb.db

# MongoDB connection lifecycle
async def connect_to_mongo():
    mongodb.client = AsyncIOMotorClient(MONGO_URL)
    mongodb.db = mongodb.client[MONGO_DB]
    print(f"Connected to MongoDB at {MONGO_URL}, DB: {mongodb.db.name}")

async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()
        print("Disconnected from MongoDB")

# Data models
class WorkoutSet(BaseModel):
    id: int
    reps: Optional[int] = None
    weight: Optional[float] = None
    time: Optional[str] = None
    completed: bool = False

class Exercise(BaseModel):
    id: int
    name: str
    sets: List[WorkoutSet]

class Routine(BaseModel):
    day: int
    title: str
    exercises: List[Exercise]

class RoutineInDB(Routine):
    id: str = Field(alias="_id")
    
    class Config:
        populate_by_name = True

# Helper function to convert MongoDB document to dict
def routine_helper(routine) -> dict:
    return {
        "_id": str(routine["_id"]),
        "day": routine["day"],
        "title": routine["title"],
        "exercises": routine["exercises"]
    }

# Test endpoint to check database connection
@router.get("/test-connection")
async def test_connection(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Test MongoDB connection and return collection stats"""
    try:
        # Get collection names
        collections = await db.list_collection_names()
        
        # Count documents in routines collection
        count = await db.routines.count_documents({})
        
        # Get a sample routine
        sample = await db.routines.find_one()
        
        return {
            "status": "connected",
            "database": db.name,
            "collections": collections,
            "routines_count": count,
            "sample_routine": routine_helper(sample) if sample else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# API Endpoints
@router.get("/routines")
async def get_all_routines(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get all workout routines"""
    routines = []
    async for routine in db.routines.find():
        routines.append(routine_helper(routine))
    return routines

@router.get("/routines/{day}")
async def get_routine_by_day(day: int, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Get a specific day's routine"""
    routine = await db.routines.find_one({"day": day})
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    return routine_helper(routine)

@router.put("/routines/{day}/exercises/{exercise_id}/sets/{set_id}")
async def update_set(
    day: int, 
    exercise_id: int, 
    set_id: int, 
    update_data: Dict,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update a specific set"""
    # Find the routine
    routine = await db.routines.find_one({"day": day})
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    
    # Update the specific set
    updated = False
    for exercise in routine["exercises"]:
        if exercise["id"] == exercise_id:
            for set_item in exercise["sets"]:
                if set_item["id"] == set_id:
                    # Update the set data
                    for key, value in update_data.items():
                        if key in set_item or key in ["reps", "weight", "time", "completed"]:
                            set_item[key] = value
                    updated = True
                    break
            if updated:
                break
    
    if not updated:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} or Set {set_id} not found")
    
    # Save the updated routine
    await db.routines.update_one(
        {"day": day},
        {"$set": {"exercises": routine["exercises"]}}
    )
    
    return {"message": "Set updated successfully"}

@router.post("/routines/{day}/exercises/{exercise_id}/sets")
async def add_set(
    day: int, 
    exercise_id: int,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Add a new set to an exercise"""
    routine = await db.routines.find_one({"day": day})
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    
    new_set = None
    for exercise in routine["exercises"]:
        if exercise["id"] == exercise_id:
            # Create new set based on the last set
            if exercise["sets"]:
                last_set = exercise["sets"][-1]
                new_set = last_set.copy()
                new_set["id"] = max(s["id"] for s in exercise["sets"]) + 1
                new_set["completed"] = False
            else:
                # Default set if no existing sets
                new_set = {"id": 1, "reps": 10, "weight": 0, "completed": False}
            
            exercise["sets"].append(new_set)
            break
    
    if not new_set:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} not found")
    
    # Save the updated routine
    await db.routines.update_one(
        {"day": day},
        {"$set": {"exercises": routine["exercises"]}}
    )
    
    return {"message": "Set added successfully", "set": new_set}

@router.delete("/routines/{day}/exercises/{exercise_id}/sets/{set_id}")
async def delete_set(
    day: int, 
    exercise_id: int, 
    set_id: int,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete a specific set"""
    routine = await db.routines.find_one({"day": day})
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    
    updated = False
    for exercise in routine["exercises"]:
        if exercise["id"] == exercise_id:
            original_length = len(exercise["sets"])
            exercise["sets"] = [s for s in exercise["sets"] if s["id"] != set_id]
            if len(exercise["sets"]) < original_length:
                updated = True
            break
    
    if not updated:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} or Set {set_id} not found")
    
    # Save the updated routine
    await db.routines.update_one(
        {"day": day},
        {"$set": {"exercises": routine["exercises"]}}
    )
    
    return {"message": "Set deleted successfully"}

@router.delete("/routines/{day}/exercises/{exercise_id}")
async def delete_exercise(
    day: int, 
    exercise_id: int,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete an exercise from a routine"""
    routine = await db.routines.find_one({"day": day})
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    
    original_length = len(routine["exercises"])
    routine["exercises"] = [e for e in routine["exercises"] if e["id"] != exercise_id]
    
    if len(routine["exercises"]) == original_length:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} not found")
    
    # Save the updated routine
    await db.routines.update_one(
        {"day": day},
        {"$set": {"exercises": routine["exercises"]}}
    )
    
    return {"message": "Exercise deleted successfully"}

@router.post("/routines/{day}/exercises/{exercise_id}/complete-set/{set_id}")
async def toggle_set_completion(
    day: int, 
    exercise_id: int, 
    set_id: int,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Toggle set completion status"""
    routine = await db.routines.find_one({"day": day})
    if not routine:
        raise HTTPException(status_code=404, detail=f"Routine for day {day} not found")
    
    toggled = False
    for exercise in routine["exercises"]:
        if exercise["id"] == exercise_id:
            for set_item in exercise["sets"]:
                if set_item["id"] == set_id:
                    set_item["completed"] = not set_item["completed"]
                    toggled = True
                    break
            if toggled:
                break
    
    if not toggled:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} or Set {set_id} not found")
    
    # Save the updated routine
    await db.routines.update_one(
        {"day": day},
        {"$set": {"exercises": routine["exercises"]}}
    )
    
    # Find the updated set to return its status
    for exercise in routine["exercises"]:
        if exercise["id"] == exercise_id:
            for set_item in exercise["sets"]:
                if set_item["id"] == set_id:
                    return {"message": "Set completion toggled", "completed": set_item["completed"]}

@router.post("/routines/camera/analyze")
async def trigger_posture_analysis(request_data: Dict):
    """Trigger posture analysis (placeholder)"""
    exercise_name = request_data.get("exercise_name")
    return {
        "message": f"Analysis triggered for {exercise_name}",
        "status": "ready",
        "websocket_url": "ws://localhost:8001/api/workout/ws/analyze"
    }

# Add user-specific endpoints (for future use)
@router.get("/routines/user/{user_id}")
async def get_user_routines(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get all routines for a specific user"""
    routines = []
    async for routine in db.routines.find({"user_id": user_id}):
        routines.append(routine_helper(routine))
    return routines

@router.post("/routines/user/{user_id}/copy-default")
async def copy_default_routines_for_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Copy default routines for a new user"""
    # Check if user already has routines
    existing = await db.routines.find_one({"user_id": user_id})
    if existing:
        raise HTTPException(status_code=400, detail="User already has routines")
    
    # Get default routines (ones without user_id)
    default_routines = []
    async for routine in db.routines.find({"user_id": {"$exists": False}}):
        # Create a copy for the user
        routine_copy = routine.copy()
        routine_copy.pop("_id", None)  # Remove the original ID
        routine_copy["user_id"] = user_id
        routine_copy["created_at"] = datetime.utcnow()
        default_routines.append(routine_copy)
    
    if default_routines:
        result = await db.routines.insert_many(default_routines)
        return {"message": f"Created {len(result.inserted_ids)} routines for user {user_id}"}
    else:
        raise HTTPException(status_code=404, detail="No default routines found")