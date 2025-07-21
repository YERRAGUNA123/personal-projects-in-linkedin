import csv
import os
import time
import threading
import numpy as np

import pytest
import cv2
import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.driver_setup import setup_driver

def take_screenshot(driver, step_name):
    os.makedirs("screenshots", exist_ok=True)
    driver.save_screenshot(f"screenshots/{step_name}.png")

def load_test_data():
    with open('data/login_data.csv', newline='') as f:
        return list(csv.DictReader(f))

def start_recording(filename):
    os.makedirs("recordings", exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    screen_size = pyautogui.size()
    out = cv2.VideoWriter(f"recordings/{filename}.avi", fourcc, 10.0, screen_size)

    def record():
        while getattr(threading.current_thread(), "do_run", True):
            img = pyautogui.screenshot()
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            out.write(frame)
        out.release()

    t = threading.Thread(target=record)
    t.start()
    return t

@pytest.mark.parametrize("data", load_test_data(), ids=lambda d: d["username"])

def test_login(data):
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)

    test_name = f"{data['username']}_{data['expected']}"
    rec_thread = start_recording(test_name)

    try:
        driver.get("https://www.saucedemo.com")
        driver.find_element(By.ID, "user-name").send_keys(data['username'])
        driver.find_element(By.ID, "password").send_keys(data['password'])
        driver.find_element(By.ID, "login-button").click()

        if data['expected'] == "success":
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "inventory_item")))
        else:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "error-message-container")))

        take_screenshot(driver, test_name)

    finally:
        driver.quit()
        rec_thread.do_run = False
        rec_thread.join()
