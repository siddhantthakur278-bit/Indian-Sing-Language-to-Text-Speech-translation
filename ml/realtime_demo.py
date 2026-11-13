"""
Real-time OpenCV ISL Sign Language Recognition Fallback Demo
Matches the exact state machine and inference algorithm from Page 21 of the Project Guide:
- 30-frame rolling keypoint buffer
- Model inference every 3 frames
- Normalization relative to shoulders
- Confidence threshold (0.8) and temporal consensus voting (>=4 out of 5 frames)
- Refractory cooldown period (30 frames / ~1 sec)
- IDLE gesture rejection
"""

import sys
import os
import json
import time
from collections import deque, Counter
import numpy as np
import cv2
import mediapipe as mp

from extract_keypoints import extract_keypoints
from preprocess import normalize

mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils


def run_demo(model_path: str = "isl_model.keras", classes_path: str = "data/classes.json"):
    # Load vocabulary
    if not os.path.exists(classes_path):
        print(f"Error: Classes file not found: {classes_path}")
        return

    with open(classes_path, "r") as f:
        meta = json.load(f)
    classes = meta["classes"]
    print(f"Loaded {len(classes)} classes from {classes_path}")

    # Load model or fallback mock
    model = None
    if os.path.exists(model_path):
        import tensorflow as tf
        print(f"Loading trained model from {model_path}...")
        model = tf.keras.models.load_model(model_path)
    else:
        print(f"[NOTE] Model checkpoint {model_path} not found. Running in MOCK detector mode for visualization.")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    buffer = deque(maxlen=30)
    recent = deque(maxlen=5)
    glosses = []
    last_added_frame = -999
    frame_no = 0
    THRESH = 0.80
    COOLDOWN = 30  # ~1 second at 30 fps

    print("Starting webcam feed... Press 'q' to exit.")

    with mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1
    ) as holistic:
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            frame_no += 1
            h, w, _ = frame.shape

            # Mirror view for natural interaction
            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(rgb)

            # Draw visual landmarks
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
            if results.left_hand_landmarks:
                mp_drawing.draw_landmarks(frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            if results.right_hand_landmarks:
                mp_drawing.draw_landmarks(frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)

            # Extract 258-D vector and append to buffer
            keypoints = extract_keypoints(results)
            buffer.append(keypoints)

            active_pred = "IDLE"
            active_conf = 0.0

            # Run inference when buffer is ready and step interval hits
            if len(buffer) == 30 and frame_no % 3 == 0:
                raw_seq = np.array(buffer, dtype=np.float32)
                seq = normalize(raw_seq)

                if model is not None:
                    probs = model.predict(seq[None, :, :], verbose=0)[0]
                    idx = int(np.argmax(probs))
                    conf = probs[idx]
                else:
                    # Mock detection: check if hands are raised
                    has_hands = (results.left_hand_landmarks is not None) or (results.right_hand_landmarks is not None)
                    if has_hands:
                        idx = 1  # HELLO
                        conf = 0.94
                    else:
                        idx = 0  # IDLE
                        conf = 0.99

                active_pred = classes[idx]
                active_conf = conf

                # Filter by threshold
                recent.append(idx if conf > THRESH else -1)

                # Temporal voting
                top, count = Counter(recent).most_common(1)[0]
                if (top != -1 and classes[top] != "IDLE" and count >= 4 and frame_no - last_added_frame > COOLDOWN):
                    accepted_gloss = classes[top]
                    glosses.append(accepted_gloss)
                    last_added_frame = frame_no
                    print(f"Accepted Sign: [{accepted_gloss}] (count={count}, frame={frame_no})")

            # Overlay HUD
            cv2.rectangle(frame, (10, 10), (450, 120), (20, 20, 20), -1)
            cv2.putText(frame, f"Prediction: {active_pred} ({active_conf*100:.1f}%)", (20, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 200), 2)
            cv2.putText(frame, f"Glosses: {' '.join(glosses[-5:])}", (20, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Buffer: {len(buffer)}/30 | Frame: {frame_no}", (20, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

            cv2.imshow("ISL Real-Time Translation Demo", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_demo()
