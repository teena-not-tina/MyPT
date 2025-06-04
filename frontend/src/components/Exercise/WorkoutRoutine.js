import React, { useState, useEffect } from 'react';
import { Camera, MoreVertical, Plus, Trash2, Edit2, Check, X } from 'lucide-react';
import ExerciseAnalyzer from './ExerciseAnalyzer';
import workoutService from '../../services/workoutService';

// Exercise enum for supported exercises
const Exercise = {
  PUSHUP: "푸시업",
  SQUAT: "스쿼트",
  LEG_RAISE: "레그레이즈",
  DUMBBELL_CURL: "덤벨컬",
  ONE_ARM_ROW: "원암 덤벨로우",
  PLANK: "플랭크"
};

// Helper function to check if exercise is supported
const isExerciseSupported = (exerciseName) => {
  return Object.values(Exercise).includes(exerciseName);
};

const WorkoutRoutine = () => {
  const [routines, setRoutines] = useState([]);
  const [selectedDay, setSelectedDay] = useState(1);
  const [editingExercise, setEditingExercise] = useState(null);
  const [editingSet, setEditingSet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAnalyzer, setShowAnalyzer] = useState(false);
  const [selectedExercise, setSelectedExercise] = useState(null);

  const userId = 1

  // Styles (same as before)
  const styles = {
    container: {
      maxWidth: '896px',
      margin: '0 auto',
      padding: '1rem'
    },
    title: {
      fontSize: '1.5rem',
      fontWeight: 'bold',
      marginBottom: '1.5rem'
    },
    daySelection: {
      display: 'flex',
      gap: '0.5rem',
      marginBottom: '1.5rem',
      overflowX: 'auto'
    },
    dayButton: (isActive) => ({
      padding: '0.5rem 1rem',
      borderRadius: '0.5rem',
      whiteSpace: 'nowrap',
      border: 'none',
      cursor: 'pointer',
      transition: 'all 0.2s',
      backgroundColor: isActive ? '#3b82f6' : '#e5e7eb',
      color: isActive ? 'white' : '#374151'
    }),
    routineTitle: {
      fontSize: '1.25rem',
      fontWeight: '600',
      marginBottom: '1rem'
    },
    exerciseCard: {
      backgroundColor: 'white',
      borderRadius: '0.5rem',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
      padding: '1rem',
      marginBottom: '1rem'
    },
    exerciseHeader: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start',
      marginBottom: '0.75rem'
    },
    exerciseName: {
      fontSize: '1.125rem',
      fontWeight: '500'
    },
    iconButton: {
      padding: '0.5rem',
      background: 'none',
      border: 'none',
      color: '#4b5563',
      borderRadius: '0.5rem',
      cursor: 'pointer',
      transition: 'background-color 0.2s'
    },
    dropdownMenu: {
      position: 'absolute',
      right: '0',
      marginTop: '0.5rem',
      width: '12rem',
      backgroundColor: 'white',
      borderRadius: '0.5rem',
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
      zIndex: '10',
      border: '1px solid #e5e7eb'
    },
    deleteButton: {
      width: '100%',
      padding: '0.5rem 1rem',
      textAlign: 'left',
      color: '#dc2626',
      border: 'none',
      background: 'none',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      borderRadius: '0.5rem'
    },
    setRow: {
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      marginBottom: '0.5rem'
    },
    setLabel: {
      fontSize: '0.875rem',
      color: '#6b7280',
      width: '3rem'
    },
    editInputs: {
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      flex: '1'
    },
    input: {
      padding: '0.25rem 0.5rem',
      border: '1px solid #d1d5db',
      borderRadius: '0.25rem',
      fontSize: '0.875rem',
      width: '4rem'
    },
    doneButton: (completed) => ({
      marginLeft: 'auto',
      padding: '0.25rem 1rem',
      borderRadius: '0.5rem',
      fontSize: '0.875rem',
      fontWeight: '500',
      border: 'none',
      cursor: 'pointer',
      backgroundColor: completed ? '#10b981' : '#e5e7eb',
      color: completed ? 'white' : '#374151'
    }),
    addSetButton: {
      display: 'flex',
      alignItems: 'center',
      gap: '0.5rem',
      marginTop: '0.5rem',
      padding: '0.25rem 0.75rem',
      fontSize: '0.875rem',
      color: '#2563eb',
      background: 'none',
      border: 'none',
      borderRadius: '0.5rem',
      cursor: 'pointer'
    }
  };

  useEffect(() => {
    fetchRoutines();
  }, [userId]);

  const fetchRoutines = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await workoutService.getAllRoutines(userId);
      setRoutines(data);
      setLoading(false);
    } catch (err) {
      setError('운동 루틴을 불러오는데 실패했습니다.');
      setLoading(false);
      console.error('Failed to fetch routines:', err);
    }
  };

  const currentRoutine = routines.find(r => r.day === selectedDay);

  const handleCompleteSet = async (exerciseId, setId) => {
    try {
      await workoutService.toggleSetCompletion(selectedDay, exerciseId, setId);
      
      // Update local state optimistically
      setRoutines(prev => prev.map(routine => {
        if (routine.day === selectedDay) {
          return {
            ...routine,
            exercises: routine.exercises.map(exercise => {
              if (exercise.id === exerciseId) {
                return {
                  ...exercise,
                  sets: exercise.sets.map(set => {
                    if (set.id === setId) {
                      return { ...set, completed: !set.completed };
                    }
                    return set;
                  })
                };
              }
              return exercise;
            })
          };
        }
        return routine;
      }));
    } catch (err) {
      console.error('Failed to toggle set completion:', err);
      // Optionally show error message to user
    }
  };

  const handleCompleteRoutine = async () => {
    try {
      const result = await workoutService.completeRoutine(selectedDay, userId);
      alert(`루틴 완료! 현재 진행도: ${result.progress}, 레벨: ${result.level}`);

      // 루틴 리셋 API 호출
      await workoutService.resetUserRoutines(userId);

      // 루틴/진행상황 다시 불러오기
      fetchRoutines();
    } catch (err) {
      alert('아직 완료되지 않은 세트가 있습니다!');
    }
  };
    

  

  const handleEditSet = async (exerciseId, setId, field, value) => {
    try {
      const updateData = { [field]: value };
      await workoutService.updateSet(selectedDay, exerciseId, setId, updateData);
      
      // Update local state
      setRoutines(prev => prev.map(routine => {
        if (routine.day === selectedDay) {
          return {
            ...routine,
            exercises: routine.exercises.map(exercise => {
              if (exercise.id === exerciseId) {
                return {
                  ...exercise,
                  sets: exercise.sets.map(set => {
                    if (set.id === setId) {
                      return { ...set, [field]: value };
                    }
                    return set;
                  })
                };
              }
              return exercise;
            })
          };
        }
        return routine;
      }));
    } catch (err) {
      console.error('Failed to update set:', err);
    }
  };

  const handleAddSet = async (exerciseId) => {
    try {
      const result = await workoutService.addSet(selectedDay, exerciseId);
      
      // Refresh routines to get the new set with proper ID from backend
      await fetchRoutines();
    } catch (err) {
      console.error('Failed to add set:', err);
    }
  };

  const handleDeleteSet = async (exerciseId, setId) => {
    try {
      await workoutService.deleteSet(selectedDay, exerciseId, setId);
      
      // Update local state
      setRoutines(prev => prev.map(routine => {
        if (routine.day === selectedDay) {
          return {
            ...routine,
            exercises: routine.exercises.map(ex => {
              if (ex.id === exerciseId) {
                return { ...ex, sets: ex.sets.filter(s => s.id !== setId) };
              }
              return ex;
            })
          };
        }
        return routine;
      }));
    } catch (err) {
      console.error('Failed to delete set:', err);
    }
  };

  const handleReset = async () => {
  try {
    await workoutService.resetUserRoutines(userId);
    // 루틴/진행상황 다시 불러오기
    fetchRoutines();
    alert('루틴이 리셋되었습니다!');
  } catch (err) {
    alert('루틴 리셋에 실패했습니다.');
  }
};


// JSX
<button onClick={handleReset} style={{marginBottom: '1rem', backgroundColor: '#ef4444', color: 'white', padding: '0.5rem 1rem', borderRadius: '0.5rem', border: 'none', cursor: 'pointer'}}>
  루틴 리셋
</button>



  const handleDeleteExercise = async (exerciseId) => {
    try {
      await workoutService.deleteExercise(selectedDay, exerciseId);
      
      // Update local state
      setRoutines(prev => prev.map(routine => {
        if (routine.day === selectedDay) {
          return {
            ...routine,
            exercises: routine.exercises.filter(ex => ex.id !== exerciseId)
          };
        }
        return routine;
      }));
      setEditingExercise(null);
    } catch (err) {
      console.error('Failed to delete exercise:', err);
    }
  };


  const handleCameraClick = async (exerciseName) => {
    if (!isExerciseSupported(exerciseName)) {
      console.log(`Exercise ${exerciseName} is not supported for posture analysis`);
      return;
    }
    
    try {
      await workoutService.triggerPostureAnalysis(exerciseName);
      setSelectedExercise(exerciseName);
      setShowAnalyzer(true);
    } catch (err) {
      console.error('Failed to trigger posture analysis:', err);
    }
  };

  if (showAnalyzer) {
    return (
      <div style={styles.container}>
        <button 
          onClick={() => setShowAnalyzer(false)}
          style={{
            padding: '0.5rem 1rem',
            marginBottom: '1rem',
            backgroundColor: '#e5e7eb',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: 'pointer'
          }}
        >
          ← 돌아가기
        </button>
        <ExerciseAnalyzer exerciseName={selectedExercise} />
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ ...styles.container, display: 'flex', justifyContent: 'center', alignItems: 'center', height: '16rem' }}>
        <div style={{ fontSize: '1.125rem' }}>운동 루틴을 불러오는 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca', color: '#b91c1c', padding: '0.75rem 1rem', borderRadius: '0.25rem' }}>
          {error}
        </div>
        <button 
          onClick={fetchRoutines}
          style={{
            marginTop: '1rem',
            padding: '0.5rem 1rem',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '0.5rem',
            cursor: 'pointer'
          }}
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>운동 루틴</h1>
      <button
        onClick={handleReset}
        style={{
          marginBottom: '1rem',
          backgroundColor: '#ef4444',
          color: 'white',
          padding: '0.5rem 1rem',
          borderRadius: '0.5rem',
          border: 'none',
          cursor: 'pointer'
        }}
      >
        루틴 리셋
      </button>
      <div style={styles.daySelection}>
        {[1, 2, 3, 4].map(day => (
          <button
            key={day}
            onClick={() => setSelectedDay(day)}
            style={styles.dayButton(selectedDay === day)}
          >
            {day}일차
          </button>
        ))}
      </div>

      {currentRoutine && (
        <div>
          <h2 style={styles.routineTitle}>{currentRoutine.title}</h2>
          
          <div>
            {currentRoutine.exercises.map(exercise => (
              <div key={exercise.id} style={styles.exerciseCard}>
                <div style={styles.exerciseHeader}>
                  <h3 style={styles.exerciseName}>{exercise.name}</h3>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {isExerciseSupported(exercise.name) && (
                      <button
                        onClick={() => handleCameraClick(exercise.name)}
                        style={styles.iconButton}
                        title="자세 교정"
                      >
                        <Camera size={20} />
                      </button>
                    )}
                    <div style={{ position: 'relative' }}>
                      <button
                        onClick={() => setEditingExercise(editingExercise === exercise.id ? null : exercise.id)}
                        style={styles.iconButton}
                      >
                        <MoreVertical size={20} />
                      </button>
                      {editingExercise === exercise.id && (
                        <div style={styles.dropdownMenu}>
                          <button
                            onClick={() => handleDeleteExercise(exercise.id)}
                            style={styles.deleteButton}
                          >
                            <Trash2 size={16} />
                            운동 삭제
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div>
                  {exercise.sets.map((set, index) => (
                    <div key={set.id} style={styles.setRow}>
                      <span style={styles.setLabel}>
                        세트 {index + 1}
                      </span>
                      
                      {editingSet === `${exercise.id}-${set.id}` ? (
                        <div style={styles.editInputs}>
                          {set.time ? (
                            <input
                              type="text"
                              value={set.time}
                              onChange={(e) => handleEditSet(exercise.id, set.id, 'time', e.target.value)}
                              style={{ ...styles.input, width: '6rem' }}
                              autoFocus
                            />
                          ) : (
                            <>
                              <input
                                type="number"
                                value={set.reps || ''}
                                onChange={(e) => handleEditSet(exercise.id, set.id, 'reps', parseInt(e.target.value) || 0)}
                                style={styles.input}
                                placeholder="회"
                                autoFocus
                              />
                              <span style={{ fontSize: '0.875rem' }}>회</span>
                              {set.weight !== undefined && (
                                <>
                                  <input
                                    type="number"
                                    value={set.weight || ''}
                                    onChange={(e) => handleEditSet(exercise.id, set.id, 'weight', parseFloat(e.target.value) || 0)}
                                    style={styles.input}
                                    placeholder="kg"
                                  />
                                  <span style={{ fontSize: '0.875rem' }}>kg</span>
                                </>
                              )}
                            </>
                          )}
                          <button
                            onClick={() => setEditingSet(null)}
                            style={{ ...styles.iconButton, color: '#10b981', padding: '0.25rem' }}
                          >
                            <Check size={16} />
                          </button>
                          {exercise.sets.length > 1 && (
                            <button
                              onClick={() => handleDeleteSet(exercise.id, set.id)}
                              style={{ ...styles.iconButton, color: '#dc2626', padding: '0.25rem' }}
                            >
                              <Trash2 size={16} />
                            </button>
                          )}
                        </div>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: '1' }}>
                          <button
                            onClick={() => setEditingSet(`${exercise.id}-${set.id}`)}
                            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'none', border: 'none', cursor: 'pointer', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}
                          >
                            <span style={{ fontSize: '0.875rem' }}>
                              {set.time || `${set.reps}회 ${set.weight !== undefined ? `${set.weight}kg` : ''}`}
                            </span>
                            <Edit2 size={14} style={{ color: '#9ca3af' }} />
                          </button>
                          <button
                            onClick={() => handleCompleteSet(exercise.id, set.id)}
                            style={styles.doneButton(set.completed)}
                          >
                            {set.completed ? '완료' : 'Done'}
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                  
                  <button
                    onClick={() => handleAddSet(exercise.id)}
                    style={styles.addSetButton}
                  >
                    <Plus size={16} />
                    세트 추가
                  </button>
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={handleCompleteRoutine}
            style={{
              marginTop: '2rem',
              backgroundColor: '#10b981',
              color: 'white',
              padding: '0.75rem 1.5rem',
              borderRadius: '0.5rem',
              border: 'none',
              fontSize: '1rem',
              fontWeight: 'bold',
              cursor: 'pointer'
            }}
          >
            루틴 완료
          </button>
        </div>
      )}
    </div>
  );
};

export default WorkoutRoutine;