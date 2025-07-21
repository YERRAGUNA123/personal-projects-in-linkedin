from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tempfile

def setup_driver():
    temp_profile = tempfile.mkdtemp()
    options = Options()
    options.add_argument(f"--user-data-dir={temp_profile}")
    options.add_argument("--incognito")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)