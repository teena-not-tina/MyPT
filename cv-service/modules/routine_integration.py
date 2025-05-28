# cv-service/modules/routine_integration.py

"""
Example of how to integrate the exercise analyzer with a routine system.
This shows how the exercise analyzer would be called from your routine page.
"""

from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
from .exercise_analyzer import ExerciseAnalyzer, Exercise


@dataclass
class ExerciseSet:
    """Represents a single exercise set in a routine."""
    exercise: Exercise
    target_reps: int
    rest_time: int = 30  # seconds
    
    
@dataclass
class Routine:
    """Represents a workout routine."""
    name: str
    exercises: List[ExerciseSet]
    

class RoutineSession:
    """Manages a workout routine session."""
    
    def __init__(self, routine: Routine):
        self.routine = routine
        self.current_exercise_index = 0
        self.completed_sets = []
        self.analyzer = ExerciseAnalyzer()
        
    def get_current_exercise(self) -> ExerciseSet:
        """Get the current exercise in the routine."""
        if self.current_exercise_index < len(self.routine.exercises):
            return self.routine.exercises[self.current_exercise_index]
        return None
    
    def start_current_exercise(self, video_source=0):
        """
        Start the current exercise with posture correction.
        
        Args:
            video_source: Webcam index (0) or video file path
            
        Returns:
            Dict with completion status and stats
        """
        current_set = self.get_current_exercise()
        if not current_set:
            return {"completed": False, "message": "No more exercises"}
        
        # Reset analyzer for new exercise
        self.analyzer.reset_exercise_state()
        
        # Set target reps
        exercise_completed = False
        def on_complete():
            nonlocal exercise_completed
            exercise_completed = True
        
        self.analyzer.set_target_reps(current_set.target_reps, on_complete)
        
        # Return the analyzer configured for this exercise
        # In real implementation, this would start the video capture
        return {
            "exercise": current_set.exercise,
            "target_reps": current_set.target_reps,
            "analyzer": self.analyzer,
            "completed": False
        }
    
    def complete_current_exercise(self, actual_reps: int):
        """Mark current exercise as complete and move to next."""
        current_set = self.get_current_exercise()
        if current_set:
            self.completed_sets.append({
                "exercise": current_set.exercise.value,
                "target_reps": current_set.target_reps,
                "actual_reps": actual_reps,
                "completed": actual_reps >= current_set.target_reps
            })
            self.current_exercise_index += 1
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current routine progress."""
        total_exercises = len(self.routine.exercises)
        completed_count = len(self.completed_sets)
        
        return {
            "routine_name": self.routine.name,
            "total_exercises": total_exercises,
            "completed_exercises": completed_count,
            "progress_percentage": (completed_count / total_exercises * 100) if total_exercises > 0 else 0,
            "current_exercise_index": self.current_exercise_index,
            "completed_sets": self.completed_sets,
            "is_complete": completed_count >= total_exercises
        }


# Example usage showing how your routine page would interact with the analyzer
def example_routine_flow():
    """
    This demonstrates how your routine page would use the exercise analyzer.
    """
    
    # Example routine (this would come from your database)
    my_routine = Routine(
        name="Upper Body Strength",
        exercises=[
            ExerciseSet(Exercise.PUSHUP, target_reps=15, rest_time=30),
            ExerciseSet(Exercise.DUMBBELL_CURL, target_reps=12, rest_time=30),
            ExerciseSet(Exercise.ONE_ARM_ROW, target_reps=10, rest_time=30),
            ExerciseSet(Exercise.PLANK, target_reps=1, rest_time=0),  # 1 "rep" = complete hold
        ]
    )
    
    # Start routine session
    session = RoutineSession(my_routine)
    
    # Simulate going through the routine
    print(f"Starting routine: {my_routine.name}")
    print("-" * 50)
    
    while not session.get_progress()["is_complete"]:
        progress = session.get_progress()
        current_set = session.get_current_exercise()
        
        print(f"\nExercise {progress['current_exercise_index'] + 1}/{progress['total_exercises']}")
        print(f"Next: {current_set.exercise.value} - {current_set.target_reps} reps")
        
        # Start exercise with analyzer
        exercise_config = session.start_current_exercise(video_source=0)  # Use webcam
        
        # This is where your UI would:
        # 1. Show the exercise name and target reps
        # 2. Start the video capture with the configured analyzer
        # 3. Display real-time feedback
        # 4. Automatically return when target reps are reached
        
        print(f"Exercise analyzer configured for {exercise_config['exercise'].value}")
        print(f"Target: {exercise_config['target_reps']} reps")
        
        # Simulate exercise completion (in real app, this happens when analyzer.rep_count >= target)
        # The analyzer will call its completion callback when target is reached
        actual_reps = exercise_config['target_reps']  # Simulated
        
        # Mark exercise complete
        session.complete_current_exercise(actual_reps)
        
        # Show rest period if not last exercise
        if not session.get_progress()["is_complete"] and current_set.rest_time > 0:
            print(f"\nRest for {current_set.rest_time} seconds...")
            # In real app, show rest timer
    
    # Routine complete
    print("\n" + "="*50)
    print("ROUTINE COMPLETE! 🎉")
    print("="*50)
    
    # Show summary
    progress = session.get_progress()
    print(f"\nSummary for {progress['routine_name']}:")
    for i, completed_set in enumerate(progress['completed_sets']):
        status = "✓" if completed_set['completed'] else "✗"
        print(f"{status} {completed_set['exercise']}: {completed_set['actual_reps']}/{completed_set['target_reps']} reps")


# API endpoint example for routine integration
from fastapi import APIRouter
from typing import Optional

router = APIRouter(prefix="/routine", tags=["routine"])

# Global session storage (in production, use proper session management)
active_sessions = {}


@router.post("/start-exercise")
async def start_routine_exercise(
    session_id: str,
    exercise_index: int
):
    """
    Called by routine page when starting an exercise.
    Returns configuration for the exercise analyzer.
    """
    session = active_sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}
    
    # Move to specified exercise
    session.current_exercise_index = exercise_index
    config = session.start_current_exercise()
    
    return {
        "exercise": config["exercise"].name,
        "exercise_name": config["exercise"].value,
        "target_reps": config["target_reps"],
        "message": f"Start {config['exercise'].value} - aim for {config['target_reps']} reps"
    }


@router.post("/complete-exercise")
async def complete_routine_exercise(
    session_id: str,
    actual_reps: int
):
    """
    Called when exercise is completed (either by reaching target or user ending early).
    """
    session = active_sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}
    
    session.complete_current_exercise(actual_reps)
    progress = session.get_progress()
    
    return {
        "progress": progress,
        "next_exercise": session.get_current_exercise().exercise.value if session.get_current_exercise() else None,
        "routine_complete": progress["is_complete"]
    }


if __name__ == "__main__":
    example_routine_flow()