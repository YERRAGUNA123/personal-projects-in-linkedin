# SauceDemo Selenium Automation

Automated browser testing of [SauceDemo](https://www.saucedemo.com) using Selenium & Pytest.

## 📁 Project Structure

- `tests/`: test cases
- `utils/`: browser setup
- `data/`: CSV test data
- `screenshots/`: captured images
- `requirements.txt`: dependencies

## ✅ Features

- Login test (data-driven)
- Full checkout flow
- Screenshot logging

## ▶️ Run Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```