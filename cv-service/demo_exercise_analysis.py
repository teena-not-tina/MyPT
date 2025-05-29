# # demo_exercise_analysis.py (Quick Test)

# # What it does: A standalone script to test everything without setting up the full system
# # Think of it as: A quick demo to check if exercise detection works
# # To run:
# # cd cv-service
# # python demo_exercise_analysis.py

# import cv2
# import sys
# from modules.exercise_analyzer import ExerciseAnalyzer, Exercise, process_video, process_webcam


# def main():
#     """Demo script to test exercise analysis with video or webcam."""
    
#     print("Exercise Posture Analysis Demo")
#     print("==============================")
#     print("\nAvailable exercises:")
#     for i, exercise in enumerate(Exercise, 1):
#         print(f"{i}. {exercise.value}")
    
#     # Get exercise choice
#     while True:
#         try:
#             choice = int(input("\nSelect exercise (1-6): "))
#             if 1 <= choice <= 6:
#                 selected_exercise = list(Exercise)[choice - 1]
#                 break
#             else:
#                 print("Please enter a number between 1 and 6")
#         except ValueError:
#             print("Please enter a valid number")
    
#     print(f"\nSelected: {selected_exercise.value}")
    
#     # Get input source
#     print("\nInput source:")
#     print("1. Webcam (real-time)")
#     print("2. Video file")
    
#     while True:
#         try:
#             source_choice = int(input("\nSelect input source (1-2): "))
#             if source_choice in [1, 2]:
#                 break
#             else:
#                 print("Please enter 1 or 2")
#         except ValueError:
#             print("Please enter a valid number")
    
#     if source_choice == 1:
#         # Use webcam
#         print("\nStarting webcam analysis...")
#         print("Press 'q' to quit, 'r' to reset rep count")
#         process_webcam(selected_exercise)
#     else:
#         # Use video file
#         video_path = input("\nEnter video file path: ").strip()
        
#         # Check if file exists
#         try:
#             cap = cv2.VideoCapture(video_path)
#             if not cap.isOpened():
#                 print(f"Error: Cannot open video file '{video_path}'")
#                 return
#             cap.release()
#         except Exception as e:
#             print(f"Error: {e}")
#             return
        
#         # Ask for output
#         save_output = input("\nSave analyzed video? (y/n): ").lower() == 'y'
#         output_path = None
        
#         if save_output:
#             output_path = input("Enter output file path (e.g., output.mp4): ").strip()
        
#         print("\nProcessing video...")
#         print("Press 'q' to quit early")
#         process_video(video_path, selected_exercise, output_path)
        
#         if save_output and output_path:
#             print(f"\nAnalyzed video saved to: {output_path}")
    
#     print("\nAnalysis complete!")


# def test_single_frame():
#     """Test function to analyze a single frame from webcam."""
#     analyzer = ExerciseAnalyzer()
#     cap = cv2.VideoCapture(0)
    
#     print("Position yourself and press SPACE to capture and analyze a frame")
#     print("Press 'q' to quit")
    
#     selected_exercise = Exercise.SQUAT  # Default to squat for testing
    
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
        
#         frame = cv2.resize(frame, (640, 480))
#         cv2.imshow("Position yourself", frame)
        
#         key = cv2.waitKey(1) & 0xFF
#         if key == ord('q'):
#             break
#         elif key == ord(' '):
#             # Analyze the frame
#             feedback = analyzer.analyze_exercise(frame, selected_exercise)
#             if feedback:
#                 print("\n--- Analysis Results ---")
#                 print(f"Form Correct: {feedback.is_correct}")
#                 print(f"Confidence: {feedback.confidence:.2f}")
#                 print("\nFeedback:")
#                 for msg in feedback.feedback_messages:
#                     print(f"  - {msg}")
#                 print("\nAngle Data:")
#                 for key, value in feedback.angle_data.items():
#                     print(f"  - {key}: {value:.2f}")
                
#                 # Show annotated frame
#                 annotated = analyzer.draw_landmarks(frame, True, feedback)
#                 cv2.imshow("Analysis Result", annotated)
#                 cv2.waitKey(3000)  # Show for 3 seconds
    
#     cap.release()
#     cv2.destroyAllWindows()


# if __name__ == "__main__":
#     if len(sys.argv) > 1 and sys.argv[1] == "--test":
#         test_single_frame()
#     else:
#         main()