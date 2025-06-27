import sys
import time
import cv2
import numpy as np
import pyautogui
import mediapipe as mp
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPoint


class HandTrackingThread(QThread):
    update_frame = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.running = True
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils

        self.key_width, self.key_height = 80, 80
        self.previous_pressed_key = None
        self.last_switch_time = 0
        self.switch_delay = 1
        self.output_text = ""
        self.layout_type = "letters"
        self.shift_mode = False
        self.FINGER_TIPS = [4, 8, 12, 16, 20]
        self.last_keypress_time = time.time()
        self.keypress_cooldown = 0.5

        self.dragging_group = None
        self.drag_offset = (0, 0)
        self.keyboard_layout_cache = self._default_layout()
        self.group_positions = self._default_group_positions()

    def _default_layout(self):
        return {
            "row1": ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            "col_left": ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', '"'],
            "col_right": ['z', 'x', 'c', 'v', 'b', 'n', 'm'],
            "bottom": ['SHIFT', 'SWITCH', 'SPACE', 'BACK', 'ENTER']
        }

    def _default_group_positions(self):
        return {
            "row1": (300, 200),
            "col_left": (100, 300),
            "col_right": (150, 300),
            "bottom": (500, 900)
        }

    def _generate_keyboard_layout(self):
        layout = []
        for group, keys in self.keyboard_layout_cache.items():
            gx, gy = self.group_positions[group]
            for i, key in enumerate(keys):
                display_key = key.upper() if self.shift_mode and len(key) == 1 and key.isalpha() else key.lower() if len(key) == 1 and key.isalpha() else key
                width = self.key_width * (5 if key == 'SPACE' else 2 if key in ['ENTER', 'SHIFT', 'BACK', 'SWITCH'] else 1)
                if group == 'row1':
                    x = gx + i * (self.key_width + 10)
                    y = gy
                elif group == 'col_left' or group == 'col_right':
                    x = gx
                    y = gy + i * (self.key_height + 10)
                elif group == 'bottom':
                    x = gx + i * (width + 10)
                    y = gy
                layout.append((display_key, (x, y, width, self.key_height), group))
        return layout

    def run(self):
        while self.running:
            success, img = self.cap.read()
            if not success:
                continue

            img = cv2.flip(img, 1)
            transparent = np.zeros((img.shape[0], img.shape[1], 4), dtype=np.uint8)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            result = self.hands.process(img_rgb)
            keyboard_layout = self._generate_keyboard_layout()
            current_pressed_key = None

            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    h, w, _ = img.shape
                    for tip_id in self.FINGER_TIPS:
                        tip = hand_landmarks.landmark[tip_id]
                        tip_x, tip_y = int(tip.x * w), int(tip.y * h)

                        for key, (x, y, kw, kh), _ in keyboard_layout:
                            if x < tip_x < x + kw and y < tip_y < y + kh:
                                current_pressed_key = key
                                break

                    hand_overlay = np.zeros((img.shape[0], img.shape[1], 3), dtype=np.uint8)
                    self.mp_draw.draw_landmarks(hand_overlay, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    hand_overlay_rgba = cv2.cvtColor(hand_overlay, cv2.COLOR_BGR2BGRA)
                    alpha_mask = cv2.cvtColor(hand_overlay, cv2.COLOR_BGR2GRAY)
                    hand_overlay_rgba[:, :, 3] = np.where(alpha_mask > 0, 255, 0)
                    transparent = cv2.addWeighted(transparent, 1.0, hand_overlay_rgba, 1.0, 0)

            current_time = time.time()
            if current_pressed_key and (current_time - self.last_keypress_time) > self.keypress_cooldown:
                if current_pressed_key == "SWITCH" and (current_time - self.last_switch_time) > self.switch_delay:
                    self.layout_type = "numbers" if self.layout_type == "letters" else "letters"
                    self.keyboard_layout_cache = self._default_layout()
                    self.last_switch_time = current_time
                elif current_pressed_key == "SPACE":
                    self.output_text += " "
                    pyautogui.press("space")
                elif current_pressed_key == "ENTER":
                    self.output_text += "\n"
                    pyautogui.press("enter")
                elif current_pressed_key == "BACK":
                    self.output_text = self.output_text[:-1]
                    pyautogui.press("backspace")
                elif current_pressed_key == "SHIFT":
                    self.shift_mode = not self.shift_mode
                elif current_pressed_key not in ["SWITCH"]:
                    key_to_type = current_pressed_key.upper() if self.shift_mode else current_pressed_key.lower()
                    self.output_text += key_to_type
                    pyautogui.typewrite(key_to_type)
                self.last_keypress_time = current_time

            for key, (x, y, kw, kh), _ in keyboard_layout:
                button_color = (0, 0, 0, 180)
                text_color = (255, 255, 255, 255)
                cv2.rectangle(transparent, (x, y), (x + kw, y + kh), button_color, -1)
                cv2.rectangle(transparent, (x, y), (x + kw, y + kh), text_color, 2)
                font_scale = 0.7
                text_size = cv2.getTextSize(key, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
                text_x = x + (kw - text_size[0]) // 2
                text_y = y + (kh + text_size[1]) // 2
                cv2.putText(transparent, key, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 2)

            self.update_frame.emit(transparent)

        self.cap.release()


class VirtualKeyboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, 1920, 1080)

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 1920, 1080)

        self.thread = HandTrackingThread()
        self.thread.update_frame.connect(self.update_image)
        self.thread.start()

    def update_image(self, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGBA8888)
        self.label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        self.thread.running = False
        self.thread.quit()
        self.thread.wait()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = (event.x(), event.y())
            for key, (x, y, w, h), group in self.thread._generate_keyboard_layout():
                if x <= pos[0] <= x + w and y <= pos[1] <= y + h:
                    self.thread.dragging_group = group
                    self.thread.drag_offset = (pos[0] - self.thread.group_positions[group][0], pos[1] - self.thread.group_positions[group][1])
                    break

    def mouseMoveEvent(self, event):
        if self.thread.dragging_group:
            pos = (event.x(), event.y())
            new_x = pos[0] - self.thread.drag_offset[0]
            new_y = pos[1] - self.thread.drag_offset[1]
            self.thread.group_positions[self.thread.dragging_group] = (new_x, new_y)

    def mouseReleaseEvent(self, event):
        self.thread.dragging_group = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VirtualKeyboardWindow()
    window.show()
    sys.exit(app.exec_())
