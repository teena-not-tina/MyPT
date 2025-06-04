// frontend/src/services/workoutService.js

const API_BASE_URL = process.env.REACT_APP_CV_SERVICE_URL || 'http://localhost:8001';

class WorkoutService {
  async getAllRoutines(userId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/workout/routines?user_id=${userId}`);
      if (!response.ok) throw new Error('Failed to fetch routines');
      return await response.json();
    } catch (error) {
      console.error('Error fetching routines:', error);
      throw error;
    }
  }

  async getRoutineByDay(day) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/workout/routines/${day}`);
      if (!response.ok) throw new Error(`Failed to fetch routine for day ${day}`);
      return await response.json();
    } catch (error) {
      console.error('Error fetching routine:', error);
      throw error;
    }
  }

  async resetUserRoutines(userId) {
    const response = await fetch(`${API_BASE_URL}/api/workout/routines/user/${userId}/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) throw new Error('Failed to reset routines');
    return await response.json();
  }

  // workoutService.js
  async completeRoutine(day, userId) {
    const response = await fetch(`${API_BASE_URL}/api/workout/routines/${day}/complete?user_id=${userId}`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to complete routine');
    return await response.json();
  }

  async updateSet(day, exerciseId, setId, updateData) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/workout/routines/${day}/exercises/${exerciseId}/sets/${setId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updateData)
        }
      );
      if (!response.ok) throw new Error('Failed to update set');
      return await response.json();
    } catch (error) {
      console.error('Error updating set:', error);
      throw error;
    }
  }

  async addSet(day, exerciseId) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/workout/routines/${day}/exercises/${exerciseId}/sets`,
        { method: 'POST' }
      );
      if (!response.ok) throw new Error('Failed to add set');
      return await response.json();
    } catch (error) {
      console.error('Error adding set:', error);
      throw error;
    }
  }

  async deleteSet(day, exerciseId, setId) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/workout/routines/${day}/exercises/${exerciseId}/sets/${setId}`,
        { method: 'DELETE' }
      );
      if (!response.ok) throw new Error('Failed to delete set');
      return await response.json();
    } catch (error) {
      console.error('Error deleting set:', error);
      throw error;
    }
  }

  async deleteExercise(day, exerciseId) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/workout/routines/${day}/exercises/${exerciseId}`,
        { method: 'DELETE' }
      );
      if (!response.ok) throw new Error('Failed to delete exercise');
      return await response.json();
    } catch (error) {
      console.error('Error deleting exercise:', error);
      throw error;
    }
  }

  async toggleSetCompletion(day, exerciseId, setId) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/workout/routines/${day}/exercises/${exerciseId}/complete-set/${setId}`,
        { method: 'POST' }
      );
      if (!response.ok) throw new Error('Failed to toggle set completion');
      return await response.json();
    } catch (error) {
      console.error('Error toggling set completion:', error);
      throw error;
    }
  }

  async triggerPostureAnalysis(exerciseName) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/workout/routines/camera/analyze`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ exercise_name: exerciseName })
        }
      );
      if (!response.ok) throw new Error('Failed to trigger posture analysis');
      return await response.json();
    } catch (error) {
      console.error('Error triggering posture analysis:', error);
      throw error;
    }
  }
}

export default new WorkoutService();