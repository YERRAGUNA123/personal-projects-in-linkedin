import sys
import cv2
import mediapipe as mp
import pyttsx3
import numpy as np
import time

from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtCore import Qt, QTimer, QPoint

class OverlayApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 500)

        self.label = QLabel(self)
        self.label.resize(600, 500)

        self.drag_pos = QPoint()

        self.cap = cv2.VideoCapture(0)
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True, max_num_faces=1)

        self.voice = pyttsx3.init()
        self.voice.setProperty('rate', 150)

        self.not_looking_time = 0
        self.slouch_time = 0
        self.last_voice_time = time.time()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        ih, iw, _ = frame.shape

        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark
            nose = lm[1]
            chin = lm[152]
            vertical_dist = (chin.y - nose.y) * ih

            if vertical_dist < 80:
                self.slouch_time += 1 / 30
                if time.time() - self.last_voice_time > 15:
                    self.voice.say("Please sit straight")
                    self.voice.runAndWait()
                    self.last_voice_time = time.time()

            cv2.putText(frame, "Posture OK" if vertical_dist >= 80 else "Slouching!",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if vertical_dist >= 80 else (0, 0, 255), 2)

        frame = cv2.resize(frame, (600, 500))
        img = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()
        self.label.setPixmap(QPixmap.fromImage(img))

    def mousePressEvent(self, event):
        self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        self.move(event.globalPos() - self.drag_pos)

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OverlayApp()
    window.show()
    sys.exit(app.exec_())
