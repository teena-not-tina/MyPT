import React, { useState, useEffect } from 'react';
import { Camera, MoreVertical, Plus, Trash2, Edit2, Check, X } from 'lucide-react';
import ExerciseAnalyzer from './ExerciseAnalyzer';

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

  // Styles
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

  // Mock data
  const mockRoutines = [
    {
      day: 1,
      title: "1일차 - 하체 & 힙 집중",
      exercises: [
        { id: 1, name: "워밍업: 러닝머신 빠르게 걷기", sets: [{ id: 1, time: "5분", completed: false }] },
        { id: 2, name: "스미스머신 스쿼트", sets: [{ id: 1, reps: 12, weight: 20, completed: false }, { id: 2, reps: 12, weight: 20, completed: false }, { id: 3, reps: 12, weight: 20, completed: false }] },
        { id: 3, name: "레그프레스", sets: [{ id: 1, reps: 12, weight: 50, completed: false }, { id: 2, reps: 12, weight: 50, completed: false }, { id: 3, reps: 12, weight: 50, completed: false }] },
        { id: 4, name: "런지 (덤벨 들고)", sets: [{ id: 1, reps: 10, weight: 5, completed: false }, { id: 2, reps: 10, weight: 5, completed: false }, { id: 3, reps: 10, weight: 5, completed: false }] },
        { id: 5, name: "레그컬 (누워서 하는 거)", sets: [{ id: 1, reps: 12, weight: 20, completed: false }, { id: 2, reps: 12, weight: 20, completed: false }, { id: 3, reps: 12, weight: 20, completed: false }] },
        { id: 6, name: "힙 어브덕션 머신", sets: [{ id: 1, reps: 15, weight: 30, completed: false }, { id: 2, reps: 15, weight: 30, completed: false }, { id: 3, reps: 15, weight: 30, completed: false }] },
        { id: 7, name: "마무리: 천국의계단", sets: [{ id: 1, time: "10-15분", completed: false }] }
      ]
    },
    {
      day: 2,
      title: "2일차 - 상체 & 복부",
      exercises: [
        { id: 8, name: "워밍업: 러닝머신", sets: [{ id: 1, time: "5분", completed: false }] },
        { id: 9, name: "랫풀다운", sets: [{ id: 1, reps: 12, weight: 15, completed: false }, { id: 2, reps: 12, weight: 15, completed: false }, { id: 3, reps: 12, weight: 15, completed: false }] },
        { id: 10, name: "시티드로우", sets: [{ id: 1, reps: 12, weight: 20, completed: false }, { id: 2, reps: 12, weight: 20, completed: false }, { id: 3, reps: 12, weight: 20, completed: false }] },
        { id: 11, name: "덤벨 숄더프레스", sets: [{ id: 1, reps: 12, weight: 4, completed: false }, { id: 2, reps: 12, weight: 4, completed: false }, { id: 3, reps: 12, weight: 4, completed: false }] },
        { id: 12, name: "케이블 트라이셉스 푸시다운", sets: [{ id: 1, reps: 15, weight: 15, completed: false }, { id: 2, reps: 15, weight: 15, completed: false }, { id: 3, reps: 15, weight: 15, completed: false }] },
        { id: 13, name: "복부운동 (플랭크 + 크런치 + 레그레이즈)", sets: [{ id: 1, time: "30초 + 15회 + 15회", completed: false }, { id: 2, time: "30초 + 15회 + 15회", completed: false }, { id: 3, time: "30초 + 15회 + 15회", completed: false }] }
      ]
    },
    {
      day: 3,
      title: "3일차 - 하체 & 힙 + 유산소",
      exercises: [
        { id: 14, name: "워밍업: 러닝머신", sets: [{ id: 1, time: "5분", completed: false }] },
        { id: 15, name: "불가리안 스플릿 스쿼트", sets: [{ id: 1, reps: 10, weight: 4, completed: false }, { id: 2, reps: 10, weight: 4, completed: false }, { id: 3, reps: 10, weight: 4, completed: false }] },
        { id: 16, name: "데드리프트", sets: [{ id: 1, reps: 12, weight: 20, completed: false }, { id: 2, reps: 12, weight: 20, completed: false }, { id: 3, reps: 12, weight: 20, completed: false }] },
        { id: 17, name: "힙 쓰러스트 머신", sets: [{ id: 1, reps: 12, weight: 30, completed: false }, { id: 2, reps: 12, weight: 30, completed: false }, { id: 3, reps: 12, weight: 30, completed: false }] },
        { id: 18, name: "케이블 킥백", sets: [{ id: 1, reps: 15, weight: 10, completed: false }, { id: 2, reps: 15, weight: 10, completed: false }, { id: 3, reps: 15, weight: 10, completed: false }] },
        { id: 19, name: "천국의계단", sets: [{ id: 1, time: "15-20분", completed: false }] }
      ]
    },
    {
      day: 4,
      title: "4일차 - 상체 & 복부 + 전신",
      exercises: [
        { id: 20, name: "워밍업: 러닝머신", sets: [{ id: 1, time: "5분", completed: false }] },
        { id: 21, name: "체스트프레스", sets: [{ id: 1, reps: 12, weight: 25, completed: false }, { id: 2, reps: 12, weight: 25, completed: false }, { id: 3, reps: 12, weight: 25, completed: false }] },
        { id: 22, name: "어깨 레터럴레이즈", sets: [{ id: 1, reps: 15, weight: 4, completed: false }, { id: 2, reps: 15, weight: 4, completed: false }, { id: 3, reps: 15, weight: 4, completed: false }] },
        { id: 23, name: "원암 덤벨로우", sets: [{ id: 1, reps: 12, weight: 8, completed: false }, { id: 2, reps: 12, weight: 8, completed: false }, { id: 3, reps: 12, weight: 8, completed: false }] },
        { id: 24, name: "케이블 우드쵸퍼", sets: [{ id: 1, reps: 15, weight: 15, completed: false }, { id: 2, reps: 15, weight: 15, completed: false }, { id: 3, reps: 15, weight: 15, completed: false }] },
        { id: 25, name: "버피테스트", sets: [{ id: 1, reps: 10, completed: false }, { id: 2, reps: 10, completed: false }, { id: 3, reps: 10, completed: false }] },
        { id: 26, name: "마무리: 러닝머신", sets: [{ id: 1, time: "10분", completed: false }] }
      ]
    }
  ];

  useEffect(() => {
    fetchRoutines();
  }, []);

  const fetchRoutines = async () => {
    try {
      setLoading(true);
      setRoutines(mockRoutines);
      setLoading(false);
    } catch (err) {
      setError('운동 루틴을 불러오는데 실패했습니다.');
      setLoading(false);
    }
  };

  const currentRoutine = routines.find(r => r.day === selectedDay);

  const handleCompleteSet = async (exerciseId, setId) => {
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
  };

  const handleEditSet = async (exerciseId, setId, field, value) => {
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
  };

  const handleAddSet = async (exerciseId) => {
    const exercise = currentRoutine.exercises.find(e => e.id === exerciseId);
    const lastSet = exercise.sets[exercise.sets.length - 1];
    const newSet = {
      id: Math.max(...exercise.sets.map(s => s.id)) + 1,
      ...Object.keys(lastSet).reduce((acc, key) => {
        if (key !== 'id' && key !== 'completed') {
          acc[key] = lastSet[key];
        }
        return acc;
      }, {}),
      completed: false
    };

    setRoutines(prev => prev.map(routine => {
      if (routine.day === selectedDay) {
        return {
          ...routine,
          exercises: routine.exercises.map(ex => {
            if (ex.id === exerciseId) {
              return { ...ex, sets: [...ex.sets, newSet] };
            }
            return ex;
          })
        };
      }
      return routine;
    }));
  };

  const handleDeleteSet = async (exerciseId, setId) => {
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
  };

  const handleDeleteExercise = async (exerciseId) => {
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
  };

  const handleCameraClick = async (exerciseName) => {
    if (!isExerciseSupported(exerciseName)) {
      console.log(`Exercise ${exerciseName} is not supported for posture analysis`);
      return;
    }
    setSelectedExercise(exerciseName);
    setShowAnalyzer(true);
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
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>운동 루틴</h1>
      
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
        </div>
      )}
    </div>
  );
};

export default WorkoutRoutine;