# exercise_analyzer.py (The Brain)

# What it does: The core logic that analyzes your exercise form
# Think of it as: A personal trainer that watches your movements and counts reps
# Can't run alone - it's a module used by other files


import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class Exercise(Enum):
    PUSHUP = "푸시업"
    SQUAT = "스쿼트"
    LEG_RAISE = "레그레이즈"
    DUMBBELL_CURL = "덤벨컬"
    ONE_ARM_ROW = "원암덤벨로우"
    PLANK = "플랭크"


@dataclass
class PostureFeedback:
    is_correct: bool
    feedback_messages: List[str]
    angle_data: Dict[str, float]
    confidence: float


class ExerciseAnalyzer:
    def __init__(self, model_path: str = 'pose_landmarker_full.task'):
        """Initialize the exercise analyzer with MediaPipe pose detection."""
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False,
        )
        self.detector = vision.PoseLandmarker.create_from_options(options)
        
        # Smoothing parameters
        self.prev_landmarks = None
        self.alpha = 0.7  # Smoothing factor
        
        # Exercise state tracking
        self.rep_count = 0
        self.target_reps = None  # Will be set from routine
        self.exercise_state = "ready"  # ready, down, up
        self.on_exercise_complete = None  # Callback when target reps reached
        
    def calculate_angle(self, a, b, c):
        """
        Calculate the angle (in degrees) between three points.
        Points should be (x, y) or (x, y, z).
        """
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)

        ba = a - b
        bc = c - b

        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return np.degrees(angle)
    
    def set_target_reps(self, target: int, callback=None):
        """Set target rep count and optional completion callback."""
        self.target_reps = target
        self.on_exercise_complete = callback
    
    def check_completion(self):
        """Check if exercise is complete and trigger callback."""
        if self.target_reps and self.rep_count >= self.target_reps:
            if self.on_exercise_complete:
                self.on_exercise_complete()
            return True
        return False
        """Calculate angle at point b given three points."""
        ba = np.array(a) - np.array(b)
        bc = np.array(c) - np.array(b)
        
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
        return np.degrees(angle)
    
    def get_landmark_coordinates(self, landmarks, idx: int) -> Tuple[float, float]:
        """Get (x, y) coordinates for a specific landmark."""
        landmark = landmarks[idx]
        return (landmark.x, landmark.y)
    
    def smooth_landmarks(self, current, previous, alpha: float):
        """Apply exponential moving average smoothing to landmarks."""
        if previous is None:
            return current
        
        smoothed = []
        for cur, prev in zip(current, previous):
            smoothed.append(
                type(cur)(
                    x=alpha * prev.x + (1 - alpha) * cur.x,
                    y=alpha * prev.y + (1 - alpha) * cur.y,
                    z=alpha * prev.z + (1 - alpha) * cur.z,
                    visibility=cur.visibility if hasattr(cur, 'visibility') else 0
                )
            )
        return smoothed
    
    def analyze_pushup(self, landmarks) -> PostureFeedback:
        """Analyze pushup form."""
        # Get key points
        left_shoulder = self.get_landmark_coordinates(landmarks, 11)
        right_shoulder = self.get_landmark_coordinates(landmarks, 12)
        left_elbow = self.get_landmark_coordinates(landmarks, 13)
        right_elbow = self.get_landmark_coordinates(landmarks, 14)
        left_wrist = self.get_landmark_coordinates(landmarks, 15)
        right_wrist = self.get_landmark_coordinates(landmarks, 16)
        left_hip = self.get_landmark_coordinates(landmarks, 23)
        right_hip = self.get_landmark_coordinates(landmarks, 24)
        left_ankle = self.get_landmark_coordinates(landmarks, 27)
        right_ankle = self.get_landmark_coordinates(landmarks, 28)
        
        feedback_messages = []
        is_correct = True
        
        # Calculate elbow angles
        left_elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
        right_elbow_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)
        avg_elbow_angle = (left_elbow_angle + right_elbow_angle) / 2
        
        # Calculate body alignment (shoulder-hip-ankle)
        mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2, 
                       (left_shoulder[1] + right_shoulder[1]) / 2)
        mid_hip = ((left_hip[0] + right_hip[0]) / 2, 
                  (left_hip[1] + right_hip[1]) / 2)
        mid_ankle = ((left_ankle[0] + right_ankle[0]) / 2, 
                    (left_ankle[1] + right_ankle[1]) / 2)
        
        body_alignment_angle = self.calculate_angle(mid_shoulder, mid_hip, mid_ankle)
        
        # Check elbow angle (should be ~90° at bottom)
        if avg_elbow_angle > 120:
            feedback_messages.append("Lower your body further - aim for 90° elbow angle")
            is_correct = False
        elif avg_elbow_angle < 70:
            feedback_messages.append("Don't go too low - maintain control")
        
        # Check body alignment (should be ~180°)
        if abs(body_alignment_angle - 180) > 15:
            if body_alignment_angle < 165:
                feedback_messages.append("Keep your hips up - maintain straight body line")
            else:
                feedback_messages.append("Lower your hips - maintain straight body line")
            is_correct = False
        
        # Track rep state
        if avg_elbow_angle < 100 and self.exercise_state != "down":
            self.exercise_state = "down"
        elif avg_elbow_angle > 150 and self.exercise_state == "down":
            self.exercise_state = "up"
            self.rep_count += 1
            self.check_completion()  # Check if target reached
        
        return PostureFeedback(
            is_correct=is_correct,
            feedback_messages=feedback_messages,
            angle_data={
                "elbow_angle": avg_elbow_angle,
                "body_alignment": body_alignment_angle,
                "rep_count": self.rep_count
            },
            confidence=min(landmarks[11].visibility, landmarks[13].visibility, 
                         landmarks[15].visibility, landmarks[23].visibility)
        )
    
    def analyze_squat(self, landmarks) -> PostureFeedback:
        """Analyze squat form."""
        # Get key points
        left_shoulder = self.get_landmark_coordinates(landmarks, 11)
        right_shoulder = self.get_landmark_coordinates(landmarks, 12)
        left_hip = self.get_landmark_coordinates(landmarks, 23)
        right_hip = self.get_landmark_coordinates(landmarks, 24)
        left_knee = self.get_landmark_coordinates(landmarks, 25)
        right_knee = self.get_landmark_coordinates(landmarks, 26)
        left_ankle = self.get_landmark_coordinates(landmarks, 27)
        right_ankle = self.get_landmark_coordinates(landmarks, 28)
        
        feedback_messages = []
        is_correct = True
        
        # Calculate knee angles
        left_knee_angle = self.calculate_angle(left_hip, left_knee, left_ankle)
        right_knee_angle = self.calculate_angle(right_hip, right_knee, right_ankle)
        avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
        
        # Check squat depth
        if avg_knee_angle > 110:
            feedback_messages.append("Go deeper - aim for 90° knee angle")
            is_correct = False
        elif avg_knee_angle < 70:
            feedback_messages.append("Don't go too deep - maintain control")
        
        # Check knee position (shouldn't go too far forward)
        if left_knee[0] < left_ankle[0] - 0.1:  # Normalized coordinates
            feedback_messages.append("Don't let knees go too far forward")
            is_correct = False
        
        # Check back straightness
        mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2, 
                       (left_shoulder[1] + right_shoulder[1]) / 2)
        mid_hip = ((left_hip[0] + right_hip[0]) / 2, 
                  (left_hip[1] + right_hip[1]) / 2)
        
        # Vertical alignment check
        shoulder_hip_x_diff = abs(mid_shoulder[0] - mid_hip[0])
        if shoulder_hip_x_diff > 0.15:
            feedback_messages.append("Keep your back straight")
            is_correct = False
        
        # Track rep state
        if avg_knee_angle < 100 and self.exercise_state != "down":
            self.exercise_state = "down"
        elif avg_knee_angle > 160 and self.exercise_state == "down":
            self.exercise_state = "up"
            self.rep_count += 1
            self.check_completion()  # Check if target reached
        
        return PostureFeedback(
            is_correct=is_correct,
            feedback_messages=feedback_messages,
            angle_data={
                "knee_angle": avg_knee_angle,
                "rep_count": self.rep_count
            },
            confidence=min(landmarks[23].visibility, landmarks[25].visibility, 
                         landmarks[27].visibility)
        )
    
    def analyze_leg_raise(self, landmarks) -> PostureFeedback:
        """Analyze leg raise form."""
        # Get key points
        left_shoulder = self.get_landmark_coordinates(landmarks, 11)
        right_shoulder = self.get_landmark_coordinates(landmarks, 12)
        left_hip = self.get_landmark_coordinates(landmarks, 23)
        right_hip = self.get_landmark_coordinates(landmarks, 24)
        left_knee = self.get_landmark_coordinates(landmarks, 25)
        right_knee = self.get_landmark_coordinates(landmarks, 26)
        left_ankle = self.get_landmark_coordinates(landmarks, 27)
        right_ankle = self.get_landmark_coordinates(landmarks, 28)
        
        feedback_messages = []
        is_correct = True
        
        # Calculate leg angle (hip to ankle)
        mid_hip = ((left_hip[0] + right_hip[0]) / 2, 
                  (left_hip[1] + right_hip[1]) / 2)
        mid_knee = ((left_knee[0] + right_knee[0]) / 2, 
                   (left_knee[1] + right_knee[1]) / 2)
        mid_ankle = ((left_ankle[0] + right_ankle[0]) / 2, 
                    (left_ankle[1] + right_ankle[1]) / 2)
        
        # Leg straightness
        leg_angle = self.calculate_angle(mid_hip, mid_knee, mid_ankle)
        if abs(leg_angle - 180) > 20:
            feedback_messages.append("Keep legs straight")
            is_correct = False
        
        # Leg elevation (vertical position)
        leg_elevation = abs(mid_ankle[1] - mid_hip[1])
        
        # Check if hips are lifting off ground
        mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2, 
                       (left_shoulder[1] + right_shoulder[1]) / 2)
        hip_shoulder_dist_change = abs(mid_hip[1] - mid_shoulder[1])
        
        if hip_shoulder_dist_change < 0.2:  # Too much hip movement
            feedback_messages.append("Keep lower back flat on ground")
            is_correct = False
        
        # Track rep state based on leg elevation
        if leg_elevation < 0.2 and self.exercise_state != "up":
            self.exercise_state = "up"
        elif leg_elevation > 0.4 and self.exercise_state == "up":
            self.exercise_state = "down"
            self.rep_count += 1
            self.check_completion()  # Check if target reached
        
        return PostureFeedback(
            is_correct=is_correct,
            feedback_messages=feedback_messages,
            angle_data={
                "leg_angle": leg_angle,
                "leg_elevation": leg_elevation,
                "rep_count": self.rep_count
            },
            confidence=min(landmarks[23].visibility, landmarks[27].visibility)
        )
    
    def analyze_dumbbell_curl(self, landmarks) -> PostureFeedback:
        """Analyze dumbbell curl form."""
        # Analyze both arms
        left_shoulder = self.get_landmark_coordinates(landmarks, 11)
        right_shoulder = self.get_landmark_coordinates(landmarks, 12)
        left_elbow = self.get_landmark_coordinates(landmarks, 13)
        right_elbow = self.get_landmark_coordinates(landmarks, 14)
        left_wrist = self.get_landmark_coordinates(landmarks, 15)
        right_wrist = self.get_landmark_coordinates(landmarks, 16)
        
        feedback_messages = []
        is_correct = True
        
        # Calculate elbow angles
        left_elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
        right_elbow_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)
        
        # Check for proper range of motion
        active_angle = min(left_elbow_angle, right_elbow_angle)  # Use the arm that's curling
        
        if active_angle > 160:
            feedback_messages.append("Start position looks good")
        elif active_angle < 40:
            feedback_messages.append("Good contraction at the top")
        elif 40 <= active_angle <= 160:
            # Check for elbow stability (shouldn't move much)
            # This is simplified - in real implementation, track elbow position over time
            feedback_messages.append("Keep upper arm still - don't swing")
        
        # Track rep state
        if active_angle < 50 and self.exercise_state != "up":
            self.exercise_state = "up"
        elif active_angle > 150 and self.exercise_state == "up":
            self.exercise_state = "down"
            self.rep_count += 1
            self.check_completion()  # Check if target reached
        
        return PostureFeedback(
            is_correct=is_correct,
            feedback_messages=feedback_messages if feedback_messages else ["Form looks good!"],
            angle_data={
                "left_elbow_angle": left_elbow_angle,
                "right_elbow_angle": right_elbow_angle,
                "active_angle": active_angle,
                "rep_count": self.rep_count
            },
            confidence=min(landmarks[11].visibility, landmarks[13].visibility, 
                         landmarks[15].visibility)
        )
    
    def analyze_one_arm_row(self, landmarks) -> PostureFeedback:
        """Analyze one-arm dumbbell row form."""
        # Detect which arm is active based on elbow position
        left_elbow = self.get_landmark_coordinates(landmarks, 13)
        right_elbow = self.get_landmark_coordinates(landmarks, 14)
        left_wrist = self.get_landmark_coordinates(landmarks, 15)
        right_wrist = self.get_landmark_coordinates(landmarks, 16)
        left_shoulder = self.get_landmark_coordinates(landmarks, 11)
        right_shoulder = self.get_landmark_coordinates(landmarks, 12)
        left_hip = self.get_landmark_coordinates(landmarks, 23)
        right_hip = self.get_landmark_coordinates(landmarks, 24)
        
        feedback_messages = []
        is_correct = True
        
        # Determine active arm (higher elbow Y position = rowing)
        if left_elbow[1] < right_elbow[1]:
            active_shoulder, active_elbow, active_wrist = left_shoulder, left_elbow, left_wrist
            side = "left"
        else:
            active_shoulder, active_elbow, active_wrist = right_shoulder, right_elbow, right_wrist
            side = "right"
        
        # Calculate elbow angle
        elbow_angle = self.calculate_angle(active_shoulder, active_elbow, active_wrist)
        
        # Check back flatness
        mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2, 
                       (left_shoulder[1] + right_shoulder[1]) / 2)
        mid_hip = ((left_hip[0] + right_hip[0]) / 2, 
                  (left_hip[1] + right_hip[1]) / 2)
        
        # Back should be relatively parallel to ground
        back_angle = abs(mid_shoulder[1] - mid_hip[1])
        if back_angle > 0.3:
            feedback_messages.append("Keep your back flat and parallel to ground")
            is_correct = False
        
        # Check elbow position at top
        if elbow_angle < 120 and active_elbow[1] < active_shoulder[1]:
            feedback_messages.append("Good elbow position at top")
        elif active_elbow[1] > active_shoulder[1]:
            feedback_messages.append("Pull elbow higher - lead with elbow, not wrist")
            is_correct = False
        
        # Track rep state
        if active_elbow[1] < active_shoulder[1] and self.exercise_state != "up":
            self.exercise_state = "up"
        elif active_elbow[1] > active_shoulder[1] + 0.1 and self.exercise_state == "up":
            self.exercise_state = "down"
            self.rep_count += 1
            self.check_completion()  # Check if target reached
        
        return PostureFeedback(
            is_correct=is_correct,
            feedback_messages=feedback_messages if feedback_messages else ["Form looks good!"],
            angle_data={
                "elbow_angle": elbow_angle,
                "active_side": side,
                "rep_count": self.rep_count
            },
            confidence=min(landmarks[active_shoulder[0]].visibility if side == "left" else landmarks[active_shoulder[1]].visibility,
                         landmarks[active_elbow[0]].visibility if side == "left" else landmarks[active_elbow[1]].visibility)
        )
    
    def analyze_plank(self, landmarks) -> PostureFeedback:
        """Analyze plank form."""
        # Get key points
        nose = self.get_landmark_coordinates(landmarks, 0)
        left_shoulder = self.get_landmark_coordinates(landmarks, 11)
        right_shoulder = self.get_landmark_coordinates(landmarks, 12)
        left_hip = self.get_landmark_coordinates(landmarks, 23)
        right_hip = self.get_landmark_coordinates(landmarks, 24)
        left_ankle = self.get_landmark_coordinates(landmarks, 27)
        right_ankle = self.get_landmark_coordinates(landmarks, 28)
        
        feedback_messages = []
        is_correct = True
        
        # Calculate body alignment
        mid_shoulder = ((left_shoulder[0] + right_shoulder[0]) / 2, 
                       (left_shoulder[1] + right_shoulder[1]) / 2)
        mid_hip = ((left_hip[0] + right_hip[0]) / 2, 
                  (left_hip[1] + right_hip[1]) / 2)
        mid_ankle = ((left_ankle[0] + right_ankle[0]) / 2, 
                    (left_ankle[1] + right_ankle[1]) / 2)
        
        body_alignment_angle = self.calculate_angle(mid_shoulder, mid_hip, mid_ankle)
        
        # Check body alignment (should be ~180°)
        if abs(body_alignment_angle - 180) > 15:
            if body_alignment_angle < 165:
                feedback_messages.append("Raise your hips - maintain straight line")
                is_correct = False
            else:
                feedback_messages.append("Lower your hips - maintain straight line")
                is_correct = False
        
        # Check head position
        head_shoulder_alignment = abs(nose[0] - mid_shoulder[0])
        if head_shoulder_alignment > 0.15:
            feedback_messages.append("Keep your head neutral - look at the ground")
            is_correct = False
        
        # Plank is a static hold, so no rep counting
        # Could add timer functionality here
        
        return PostureFeedback(
            is_correct=is_correct,
            feedback_messages=feedback_messages if feedback_messages else ["Great plank form! Keep holding!"],
            angle_data={
                "body_alignment": body_alignment_angle,
                "head_alignment": head_shoulder_alignment
            },
            confidence=min(landmarks[11].visibility, landmarks[23].visibility, 
                         landmarks[27].visibility)
        )
    
    def analyze_exercise(self, frame: np.ndarray, exercise: Exercise) -> Optional[PostureFeedback]:
        """Main method to analyze any exercise."""
        # Convert frame to MediaPipe format
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        
        # Detect pose
        detection_result = self.detector.detect(mp_image)
        
        if not detection_result.pose_landmarks:
            return None
        
        # Use first detected person
        landmarks = detection_result.pose_landmarks[0]
        
        # Apply smoothing
        if self.prev_landmarks is not None:
            landmarks = self.smooth_landmarks(landmarks, self.prev_landmarks, self.alpha)
        self.prev_landmarks = landmarks
        
        # Analyze based on exercise type
        if exercise == Exercise.PUSHUP:
            return self.analyze_pushup(landmarks)
        elif exercise == Exercise.SQUAT:
            return self.analyze_squat(landmarks)
        elif exercise == Exercise.LEG_RAISE:
            return self.analyze_leg_raise(landmarks)
        elif exercise == Exercise.DUMBBELL_CURL:
            return self.analyze_dumbbell_curl(landmarks)
        elif exercise == Exercise.ONE_ARM_ROW:
            return self.analyze_one_arm_row(landmarks)
        elif exercise == Exercise.PLANK:
            return self.analyze_plank(landmarks)
        else:
            return None
    
    def draw_landmarks(self, frame: np.ndarray, include_feedback: bool = True, 
                      feedback: Optional[PostureFeedback] = None) -> np.ndarray:
        """Draw pose landmarks on frame with optional feedback overlay."""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
        detection_result = self.detector.detect(mp_image)
        
        annotated_frame = np.copy(frame)
        
        if detection_result.pose_landmarks:
            for landmarks in detection_result.pose_landmarks:
                # Convert to proto format for drawing
                pose_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
                pose_landmarks_proto.landmark.extend([
                    landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) 
                    for landmark in landmarks
                ])
                
                solutions.drawing_utils.draw_landmarks(
                    annotated_frame,
                    pose_landmarks_proto,
                    solutions.pose.POSE_CONNECTIONS,
                    solutions.drawing_styles.get_default_pose_landmarks_style()
                )
        
        # Add feedback overlay
        if include_feedback and feedback:
            y_offset = 30
            
            # Draw feedback status
            color = (0, 255, 0) if feedback.is_correct else (0, 0, 255)
            status_text = "Good Form!" if feedback.is_correct else "Adjust Form"
            cv2.putText(annotated_frame, status_text, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            y_offset += 40
            
            # Draw feedback messages
            for msg in feedback.feedback_messages:
                cv2.putText(annotated_frame, msg, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                y_offset += 30
            
            # Draw rep count and progress if available
            if 'rep_count' in feedback.angle_data:
                rep_text = f"Reps: {int(feedback.angle_data['rep_count'])}"
                if self.target_reps:
                    rep_text += f" / {self.target_reps}"
                    # Draw progress bar
                    progress = min(feedback.angle_data['rep_count'] / self.target_reps, 1.0)
                    bar_width = 200
                    bar_height = 20
                    bar_x = frame.shape[1] - bar_width - 20
                    bar_y = 80
                    
                    # Background
                    cv2.rectangle(annotated_frame, (bar_x, bar_y), 
                                 (bar_x + bar_width, bar_y + bar_height), 
                                 (100, 100, 100), -1)
                    # Progress
                    cv2.rectangle(annotated_frame, (bar_x, bar_y), 
                                 (bar_x + int(bar_width * progress), bar_y + bar_height), 
                                 (0, 255, 0), -1)
                
                cv2.putText(annotated_frame, rep_text, 
                           (frame.shape[1] - 250, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        return annotated_frame
    
    def reset_exercise_state(self):
        """Reset exercise tracking state."""
        self.rep_count = 0
        self.exercise_state = "ready"
        self.prev_landmarks = None
        self.target_reps = None
        self.on_exercise_complete = None


# Example usage with routine integration
def process_exercise_with_routine(video_source, exercise: Exercise, target_reps: int):
    """
    Process exercise with target reps from routine.
    
    Args:
        video_source: Can be video path (str) or camera index (int)
        exercise: Exercise type
        target_reps: Target number of reps from routine
    
    Returns:
        bool: True if completed successfully
    """
    analyzer = ExerciseAnalyzer()
    
    # Set target reps
    completed = False
    def on_complete():
        nonlocal completed
        completed = True
        print(f"\n✓ Exercise complete! Reached {target_reps} reps!")
    
    analyzer.set_target_reps(target_reps, on_complete)
    
    # Open video source
    cap = cv2.VideoCapture(video_source)
    
    print(f"Starting {exercise.value} - Target: {target_reps} reps")
    print("Press 'q' to quit early")
    
    frame_count = 0
    while cap.isOpened() and not completed:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize for consistent processing
        frame = cv2.resize(frame, (640, 480))
        
        # Skip frames for performance
        frame_count += 1
        if frame_count % 2 != 0:
            continue
        
        # Analyze exercise
        feedback = analyzer.analyze_exercise(frame, exercise)
        
        # Draw annotated frame
        annotated_frame = analyzer.draw_landmarks(frame, include_feedback=True, feedback=feedback)
        
        # Display
        cv2.imshow(f'{exercise.value} Analysis', annotated_frame)
        
        # Check for early quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\nExercise terminated early")
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    return completed


# Example usage function
def process_video(video_path: str, exercise: Exercise, output_path: Optional[str] = None):
    """Process a video file for exercise analysis."""
    analyzer = ExerciseAnalyzer()
    cap = cv2.VideoCapture(video_path)
    
    # Get video properties for output
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Create video writer if output path specified
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Skip frames for performance (process every 2nd frame)
        frame_count += 1
        if frame_count % 2 != 0:
            continue
        
        # Analyze exercise
        feedback = analyzer.analyze_exercise(frame, exercise)
        
        # Draw annotated frame
        annotated_frame = analyzer.draw_landmarks(frame, include_feedback=True, feedback=feedback)
        
        # Display or write frame
        cv2.imshow(f'{exercise.value} Analysis', annotated_frame)
        if output_path:
            out.write(annotated_frame)
        
        # Break on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    if output_path:
        out.release()
    cv2.destroyAllWindows()
    
    print(f"Final rep count: {analyzer.rep_count}")


def process_webcam(exercise: Exercise):
    """Process webcam feed for real-time exercise analysis."""
    analyzer = ExerciseAnalyzer()
    cap = cv2.VideoCapture(0)  # Use default webcam
    
    print(f"Starting {exercise.value} analysis. Press 'q' to quit, 'r' to reset count.")
    
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Resize for consistent processing
        frame = cv2.resize(frame, (640, 480))
        
        # Skip frames for performance
        frame_count += 1
        if frame_count % 2 != 0:
            continue
        
        # Analyze exercise
        feedback = analyzer.analyze_exercise(frame, exercise)
        
        # Draw annotated frame
        annotated_frame = analyzer.draw_landmarks(frame, include_feedback=True, feedback=feedback)
        
        # Display
        cv2.imshow(f'{exercise.value} Analysis', annotated_frame)
        
        # Handle key press
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            analyzer.reset_exercise_state()
            print("Reset rep count")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"Final rep count: {analyzer.rep_count}")


if __name__ == "__main__":
    # Example: Process a video file
    # process_video("path/to/video.mp4", Exercise.SQUAT, "output_analyzed.mp4")
    
    # Example: Use webcam
    process_webcam(Exercise.PUSHUP)