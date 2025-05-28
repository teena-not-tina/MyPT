// frontend/src/components/Exercise/ExerciseAnalyzer.js

import React, { useState, useRef, useEffect } from 'react';
import Webcam from 'react-webcam';
import axios from 'axios';

const ExerciseAnalyzer = () => {
  const [selectedExercise, setSelectedExercise] = useState('PUSHUP');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [repCount, setRepCount] = useState(0);
  const [useWebcam, setUseWebcam] = useState(true);
  const [wsConnection, setWsConnection] = useState(null);
  
  const webcamRef = useRef(null);
  const fileInputRef = useRef(null);
  
  const exercises = [
    { id: 'PUSHUP', name: '푸시업', description: 'Push-up' },
    { id: 'SQUAT', name: '스쿼트', description: 'Squat' },
    { id: 'LEG_RAISE', name: '레그레이즈', description: 'Leg Raise' },
    { id: 'DUMBBELL_CURL', name: '덤벨컬', description: 'Dumbbell Curl' },
    { id: 'ONE_ARM_ROW', name: '원암덤벨로우', description: 'One-arm Dumbbell Row' },
    { id: 'PLANK', name: '플랭크', description: 'Plank' }
  ];

  // WebSocket setup for real-time analysis
  useEffect(() => {
    if (isAnalyzing && useWebcam) {
      const ws = new WebSocket('ws://localhost:8001/exercise/live-analysis');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setWsConnection(ws);
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'feedback' && data.feedback) {
          setFeedback(data.feedback);
          if (data.feedback.angles && data.feedback.angles.rep_count !== undefined) {
            setRepCount(data.feedback.angles.rep_count);
          }
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setWsConnection(null);
      };
      
      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      };
    }
  }, [isAnalyzing, useWebcam]);

  // Send frames to WebSocket
  useEffect(() => {
    if (isAnalyzing && wsConnection && webcamRef.current) {
      const interval = setInterval(() => {
        const imageSrc = webcamRef.current.getScreenshot();
        if (imageSrc && wsConnection.readyState === WebSocket.OPEN) {
          // Remove data:image/jpeg;base64, prefix
          const base64Data = imageSrc.split(',')[1];
          
          wsConnection.send(JSON.stringify({
            type: 'frame',
            exercise: selectedExercise,
            data: base64Data
          }));
        }
      }, 100); // Send frame every 100ms (10 FPS)
      
      return () => clearInterval(interval);
    }
  }, [isAnalyzing, wsConnection, selectedExercise]);

  const handleStartStop = () => {
    if (isAnalyzing) {
      setIsAnalyzing(false);
      if (wsConnection) {
        wsConnection.close();
      }
    } else {
      setIsAnalyzing(true);
      setFeedback(null);
      setRepCount(0);
    }
  };

  const handleReset = () => {
    setRepCount(0);
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      wsConnection.send(JSON.stringify({ type: 'reset' }));
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('exercise', selectedExercise);

    try {
      const response = await axios.post(
        'http://localhost:8001/exercise/analyze-video',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          params: { output_format: 'json' }
        }
      );

      if (response.data.success) {
        console.log('Video analysis results:', response.data);
        // You could display the results in a modal or separate component
        alert(`Analysis complete! Total reps: ${response.data.final_rep_count}`);
      }
    } catch (error) {
      console.error('Error analyzing video:', error);
      alert('Error analyzing video. Please try again.');
    }
  };

  const getFeedbackColor = () => {
    if (!feedback) return 'gray';
    return feedback.is_correct ? 'green' : 'red';
  };

  return (
    <div className="exercise-analyzer">
      <h2>Exercise Posture Analyzer</h2>
      
      {/* Exercise Selection */}
      <div className="exercise-selection">
        <h3>Select Exercise:</h3>
        <div className="exercise-buttons">
          {exercises.map((exercise) => (
            <button
              key={exercise.id}
              onClick={() => setSelectedExercise(exercise.id)}
              className={selectedExercise === exercise.id ? 'selected' : ''}
            >
              {exercise.name}
              <small>{exercise.description}</small>
            </button>
          ))}
        </div>
      </div>

      {/* Input Mode Selection */}
      <div className="input-mode">
        <label>
          <input
            type="radio"
            checked={useWebcam}
            onChange={() => setUseWebcam(true)}
          />
          Webcam (Real-time)
        </label>
        <label>
          <input
            type="radio"
            checked={!useWebcam}
            onChange={() => setUseWebcam(false)}
          />
          Upload Video
        </label>
      </div>

      {/* Main Content Area */}
      <div className="analysis-area">
        {useWebcam ? (
          <>
            <div className="webcam-container">
              <Webcam
                ref={webcamRef}
                screenshotFormat="image/jpeg"
                width={640}
                height={480}
                className="webcam-feed"
              />
              
              {/* Overlay for feedback */}
              {isAnalyzing && feedback && (
                <div className="feedback-overlay">
                  <div className={`status ${getFeedbackColor()}`}>
                    {feedback.is_correct ? '✓ Good Form!' : '⚠ Adjust Form'}
                  </div>
                  <div className="rep-counter">
                    Reps: {repCount}
                  </div>
                </div>
              )}
            </div>
            
            <div className="controls">
              <button onClick={handleStartStop} className="primary-button">
                {isAnalyzing ? 'Stop Analysis' : 'Start Analysis'}
              </button>
              {isAnalyzing && (
                <button onClick={handleReset} className="secondary-button">
                  Reset Count
                </button>
              )}
            </div>
          </>
        ) : (
          <div className="file-upload-area">
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
            />
            <button 
              onClick={() => fileInputRef.current.click()}
              className="upload-button"
            >
              📹 Upload Video for Analysis
            </button>
          </div>
        )}
      </div>

      {/* Feedback Messages */}
      {feedback && feedback.messages.length > 0 && (
        <div className="feedback-messages">
          <h4>Feedback:</h4>
          <ul>
            {feedback.messages.map((msg, index) => (
              <li key={index}>{msg}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Angle Data (for debugging or advanced users) */}
      {feedback && feedback.angles && (
        <div className="angle-data">
          <h4>Technical Data:</h4>
          <pre>{JSON.stringify(feedback.angles, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default ExerciseAnalyzer;

// CSS (add to your stylesheet)
const styles = `
.exercise-analyzer {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.exercise-selection {
  margin-bottom: 20px;
}

.exercise-buttons {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.exercise-buttons button {
  padding: 10px;
  border: 2px solid #ddd;
  background: white;
  cursor: pointer;
  transition: all 0.3s;
}

.exercise-buttons button.selected {
  border-color: #007bff;
  background: #e7f1ff;
}

.exercise-buttons button small {
  display: block;
  font-size: 0.8em;
  color: #666;
}

.input-mode {
  margin-bottom: 20px;
}

.input-mode label {
  margin-right: 20px;
}

.webcam-container {
  position: relative;
  display: inline-block;
}

.feedback-overlay {
  position: absolute;
  top: 20px;
  left: 20px;
  right: 20px;
  color: white;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}

.status {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 10px;
}

.status.green {
  color: #4CAF50;
}

.status.red {
  color: #f44336;
}

.rep-counter {
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 20px;
  background: rgba(0,0,0,0.5);
  padding: 10px;
  border-radius: 5px;
}

.controls {
  margin-top: 20px;
  text-align: center;
}

.primary-button, .secondary-button {
  padding: 10px 20px;
  margin: 0 10px;
  font-size: 16px;
  cursor: pointer;
}

.primary-button {
  background: #007bff;
  color: white;
  border: none;
  border-radius: 5px;
}

.secondary-button {
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 5px;
}

.upload-button {
  padding: 40px;
  border: 2px dashed #ddd;
  background: #f8f9fa;
  cursor: pointer;
  font-size: 18px;
  width: 100%;
}

.feedback-messages {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 5px;
}

.angle-data {
  margin-top: 20px;
  padding: 15px;
  background: #f0f0f0;
  border-radius: 5px;
  font-family: monospace;
}
`;