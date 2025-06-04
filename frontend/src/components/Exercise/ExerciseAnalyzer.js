import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Camera, CameraOff, RotateCcw, ArrowLeft } from 'lucide-react';

const ExerciseAnalyzer = ({ exerciseName, targetReps = 10, onComplete, onBack }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [repCount, setRepCount] = useState(0);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  
  const poseRef = useRef(null);
  const cameraRef = useRef(null);
  const wsRef = useRef(null);
  const animationIdRef = useRef(null);
  const lastSendTimeRef = useRef(0);
  
  // Initialize MediaPipe Pose
  useEffect(() => {
    const initializePose = async () => {
      try {
        setIsLoading(true);
        
        // Load MediaPipe Pose
        const pose = new window.Pose({
          locateFile: (file) => {
            return `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`;
          }
        });
        
        pose.setOptions({
          modelComplexity: 1,
          smoothLandmarks: true,
          enableSegmentation: false,
          smoothSegmentation: false,
          minDetectionConfidence: 0.5,
          minTrackingConfidence: 0.5
        });
        
        pose.onResults(onPoseResults);
        poseRef.current = pose;
        
        setIsLoading(false);
      } catch (err) {
        console.error('Failed to initialize MediaPipe:', err);
        setError('Failed to load pose detection');
        setIsLoading(false);
      }
    };
    
    // Load MediaPipe scripts
    const script1 = document.createElement('script');
    script1.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js';
    script1.crossOrigin = 'anonymous';
    
    const script2 = document.createElement('script');
    script2.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/control_utils/control_utils.js';
    script2.crossOrigin = 'anonymous';
    
    const script3 = document.createElement('script');
    script3.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js';
    script3.crossOrigin = 'anonymous';
    
    const script4 = document.createElement('script');
    script4.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/pose/pose.js';
    script4.crossOrigin = 'anonymous';
    
    document.head.appendChild(script1);
    document.head.appendChild(script2);
    document.head.appendChild(script3);
    document.head.appendChild(script4);
    
    script4.onload = () => {
      initializePose();
    };
    
    return () => {
      document.head.removeChild(script1);
      document.head.removeChild(script2);
      document.head.removeChild(script3);
      document.head.removeChild(script4);
    };
  }, []);
  
  // WebSocket connection
  useEffect(() => {
    if (!isCameraOn) return;
    
    const connectWebSocket = () => {
      const ws = new WebSocket('ws://localhost:8001/api/workout/ws/analyze');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Send initial exercise info
        ws.send(JSON.stringify({
          type: 'init',
          exercise: exerciseName,
          targetReps: targetReps
        }));
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'feedback') {
          setFeedback(data.feedback);
          if (data.repCount !== undefined) {
            setRepCount(data.repCount);
          }
          
          // Check if exercise complete
          if (data.isComplete && onComplete) {
            onComplete();
          }
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error');
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      };
      
      wsRef.current = ws;
    };
    
    connectWebSocket();
    
    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [isCameraOn, exerciseName, targetReps, onComplete]);
  
  // Process pose results
  const onPoseResults = useCallback((results) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw the video
    ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);
    
    if (results.poseLandmarks) {
      // Draw landmarks and connections
      window.drawConnectors(ctx, results.poseLandmarks, window.POSE_CONNECTIONS, {
        color: '#00FF00',
        lineWidth: 4
      });
      
      window.drawLandmarks(ctx, results.poseLandmarks, {
        color: '#FF0000',
        lineWidth: 2,
        radius: 6
      });
      
      // Send landmarks to backend (throttled)
      const now = Date.now();
      if (wsRef.current && 
          wsRef.current.readyState === WebSocket.OPEN && 
          now - lastSendTimeRef.current > 100) { // Send max 10 times per second
        
        wsRef.current.send(JSON.stringify({
          type: 'landmarks',
          landmarks: results.poseLandmarks,
          timestamp: now
        }));
        
        lastSendTimeRef.current = now;
      }
    }
    
    ctx.restore();
  }, []);
  
  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        
        const camera = new window.Camera(videoRef.current, {
          onFrame: async () => {
            if (poseRef.current && videoRef.current) {
              await poseRef.current.send({ image: videoRef.current });
            }
          },
          width: 640,
          height: 480
        });
        
        camera.start();
        cameraRef.current = camera;
        setIsCameraOn(true);
        setError(null);
      }
    } catch (err) {
      console.error('Camera error:', err);
      setError('카메라 접근 권한이 필요합니다');
    }
  };
  
  // Stop camera
  const stopCamera = () => {
    if (cameraRef.current) {
      cameraRef.current.stop();
      cameraRef.current = null;
    }
    
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    
    setIsCameraOn(false);
  };
  
  // Reset exercise
  const resetExercise = () => {
    setRepCount(0);
    setFeedback(null);
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'reset' }));
    }
  };
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
  
  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
          <h2 className="text-2xl font-bold">{exerciseName} 자세 분석</h2>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={resetExercise}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={!isCameraOn}
          >
            <RotateCcw size={20} />
          </button>
          
          <button
            onClick={isCameraOn ? stopCamera : startCamera}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              isCameraOn 
                ? 'bg-red-500 hover:bg-red-600 text-white' 
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
            disabled={isLoading}
          >
            {isCameraOn ? (
              <>
                <CameraOff className="inline mr-2" size={20} />
                카메라 끄기
              </>
            ) : (
              <>
                <Camera className="inline mr-2" size={20} />
                카메라 켜기
              </>
            )}
          </button>
        </div>
      </div>
      
      {/* Status bar */}
      <div className="mb-4 p-3 bg-gray-100 rounded-lg flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
            isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
          }`}>
            {isConnected ? '● 연결됨' : '● 연결 안됨'}
          </span>
          
          <span className="text-lg font-medium">
            횟수: <span className="text-blue-600">{repCount}</span> / {targetReps}
          </span>
        </div>
        
        {/* Progress bar */}
        <div className="w-48 bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: `${Math.min((repCount / targetReps) * 100, 100)}%` }}
          />
        </div>
      </div>
      
      {/* Video/Canvas container */}
      <div className="relative bg-black rounded-lg overflow-hidden" style={{ aspectRatio: '4/3' }}>
        <video
          ref={videoRef}
          className="absolute inset-0 w-full h-full object-cover"
          style={{ display: 'none' }}
          playsInline
        />
        
        <canvas
          ref={canvasRef}
          width={640}
          height={480}
          className="w-full h-full"
        />
        
        {!isCameraOn && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center text-white">
              <Camera size={48} className="mx-auto mb-4 opacity-50" />
              <p className="text-lg">카메라를 켜서 운동을 시작하세요</p>
            </div>
          </div>
        )}
        
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50">
            <div className="text-white text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
              <p>포즈 감지 로딩 중...</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Feedback panel */}
      {feedback && isCameraOn && (
        <div className={`mt-4 p-4 rounded-lg ${
          feedback.isCorrect ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'
        }`}>
          <h3 className={`font-bold mb-2 ${
            feedback.isCorrect ? 'text-green-800' : 'text-yellow-800'
          }`}>
            {feedback.isCorrect ? '✓ 좋은 자세입니다!' : '⚠ 자세 교정이 필요합니다'}
          </h3>
          
          {feedback.messages && feedback.messages.length > 0 && (
            <ul className="space-y-1">
              {feedback.messages.map((msg, idx) => (
                <li key={idx} className="text-sm text-gray-700">
                  • {msg}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      
      {/* Error display */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">{error}</p>
        </div>
      )}
    </div>
  );
};

export default ExerciseAnalyzer;