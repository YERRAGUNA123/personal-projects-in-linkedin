import os
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.driver_setup import setup_driver

def take_screenshot(driver, step_name):
    os.makedirs("screenshots", exist_ok=True)
    driver.save_screenshot(f"screenshots/{step_name}.png")

def test_full_checkout_flow():
    driver = setup_driver()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get("https://www.saucedemo.com")
        driver.find_element(By.ID, "user-name").send_keys("standard_user")
        driver.find_element(By.ID, "password").send_keys("secret_sauce")
        driver.find_element(By.ID, "login-button").click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "inventory_item")))
        take_screenshot(driver, "01_logged_in")

        wait.until(EC.element_to_be_clickable((By.ID, "add-to-cart-sauce-labs-backpack"))).click()
        take_screenshot(driver, "02_item_added")

        driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart_item")))
        take_screenshot(driver, "03_cart")

        driver.find_element(By.ID, "checkout").click()
        wait.until(EC.presence_of_element_located((By.ID, "first-name"))).send_keys("John")
        driver.find_element(By.ID, "last-name").send_keys("Doe")
        driver.find_element(By.ID, "postal-code").send_keys("12345")
        driver.find_element(By.ID, "continue").click()
        wait.until(EC.presence_of_element_located((By.ID, "finish")))
        take_screenshot(driver, "04_checkout_info")

        driver.find_element(By.ID, "finish").click()
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "complete-header")))
        take_screenshot(driver, "05_order_complete")

        driver.find_element(By.ID, "react-burger-menu-btn").click()
        wait.until(EC.element_to_be_clickable((By.ID, "logout_sidebar_link"))).click()
        wait.until(EC.presence_of_element_located((By.ID, "login-button")))
        take_screenshot(driver, "06_logged_out")

    finally:
        driver.quit()