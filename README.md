# 🎭 ICICI Pru - Python Playwright BDD Automation Framework

This is a complete, enterprise-grade migration of the ICICI Pru TypeScript Playwright BDD automation framework to **Python + Pytest + Playwright + Pytest-BDD**. It strictly adheres to senior automation engineering standards, including the **Zero Raw Assertions Policy**, **Fluent Page Object Pattern**, and **Structured Masking Logger**.

---

## 🛠️ ARCHITECTURAL MAP

```bash
C:\Python_Playwright\
├── core\
│   ├── ai\
│   │   └── ai_service.py       # Groq & AI-based element locator healing
│   ├── api\
│   │   └── api_client.py       # REST API Client wrapper with Retry engine
│   ├── base\
│   │   └── base_page.py        # Custom high-reliability BasePage (Sync API)
│   ├── config\
│   │   └── config.py           # Environment variables & system config loader
│   ├── database\
│   │   └── db_client.py        # Database client connector & Mock pool
│   └── logger\
│       └── logger.py           # ISO-compliant audit logger with auto-masking
├── helpers\
│   ├── validators\
│   │   └── login_validator.py  # Zero Raw Assertions validator suite
│   ├── testdata\
│   │   ├── config.json         # Base URLs mapped by environment
│   │   └── user_factory.py     # SauceDemo dataset generator factory
│   └── retry.py                # Operations execution retry & SLA monitor
├── src\
│   ├── features\
│   │   ├── api\
│   │   │   └── api_login.feature  # API scenario definitions
│   │   └── ui\
│   │       └── login.feature      # UI scenario definitions
│   ├── pages\
│   │   └── login_page.py       # Fluent Interface LoginPage Class
│   └── steps\
│       ├── test_api_login.py   # Pytest-BDD API step definitions
│       └── test_login.py       # Pytest-BDD UI step definitions
├── conftest.py                 # Pytest configuration, fixtures & reporters
├── pytest.ini                  # Pytest test execution configurations
├── requirements.txt            # Python dependencies index
└── .env                        # Local execution secrets & variables (masked)
```

---

## 🚦 QUICK START GUIDE

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Environment Setup
Create a virtual environment and activate it:
```bash
# Create Virtual Environment
python -m venv .venv

# Activate Virtual Environment (Windows)
.venv\Scripts\activate

# Activate Virtual Environment (macOS/Linux)
source .venv/bin/activate
```

### 3. Install Dependencies
Install requirements and the Playwright browser binaries:
```bash
# Install packages
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium firefox webkit
```

### 4. Configure Environments (.env)
A local `.env` file has been prepared with full active settings. To enable GROQ AI healing on locator failure:
1. Obtain an API Key from Groq.
2. In your `.env` file, set `ENABLE_AI_HEALING=true` and enter your key in `AI_API_KEY`.

---

## 🏃 RUNNING TESTS

Our framework integrates an orchestration test runner `run_tests.py` and Windows batch file `run_tests.bat`. These scripts automatically handle pre-run folder cleanup, parallel process-safe scaling, dynamic report metadata injection, and automatically compile & launch the Allure dashboard in your browser window on test completion!

### 1. Basic Sequential Execution (Default Chromium)
Runs the complete test suite sequentially on Chromium, and opens the Allure report:
```bash
python run_tests.py
# OR
run_tests.bat
```

### 2. Run Specific Markers (UI / API Suites)
Run only scenarios matching specific tags (e.g., UI Sanity or backend API):
```bash
# Run only UI Sanity tests
python run_tests.py -m Sanity

# Run only backend API tests
python run_tests.py -m API
```

### 3. Run on Specific Browser Engines (Headed or Headless)
```bash
# Run on Firefox in headed mode
python run_tests.py -b firefox --headed

# Run on WebKit (Safari engine) in headless mode
python run_tests.py -b webkit --headless
```

### 4. Run in Parallel Concurrently (Process-Safe)
Concurrently scale tests across multiple workers (using `pytest-xdist`):
```bash
# Run in parallel, auto-allocating workers based on CPU cores
python run_tests.py --parallel

# Run in parallel with a specific number of workers (e.g., 4)
python run_tests.py -w 4
```

### 5. Run on Multiple Browsers Concurrently
Run and verify tests on multiple browser targets simultaneously in parallel:
```bash
python run_tests.py -b chromium -b firefox --parallel
```

### 6. Run on Device Profiles & Emulations Concurrently (Merged Reporting)
Pass any combination of desktop browsers and mobile device profiles. The runner automatically maps device targets to their correct underlying engines (e.g., `Pixel 5` $\rightarrow$ `chromium`, `iPhone 13` $\rightarrow$ `webkit`), deduplicates redundant launches, runs them in parallel, and **perfectly merges the runs under a single node** in the Allure report, displaying the combined tested models list!
```bash
# Run and merge runs on Pixel 5 and desktop Firefox
python run_tests.py -b firefox -b "Pixel 5" --parallel

# Comprehensive multi-browser and device matrix execution
python run_tests.py -b chromium -b firefox -b webkit -b edge -b "Pixel 5" -b "iPhone 13" -b "iPad Pro 11" -b "Galaxy S24" -b "Pixel 8 Pro" --parallel
```

### 7. Run Options (Clean-skipping and Headless CI)
```bash
# Skip cleaning the reports folder before execution
python run_tests.py --no-clean

# Skip automatically opening the Allure report in browser (perfect for CI/CD pipelines)
python run_tests.py --no-open
```

---

## 📊 ALLURE REPORT GENERATION

Allure reports are natively integrated into the command-line execution and the `conftest.py` hook runner.

### Automatic Generation
On test failure, the framework automatically grabs a full-page screenshot, HTML source code, console logs, and attaches them directly to the allure results directory under `reports/allure-results`.

### Manual Compilation & Viewing
If you run tests using raw `pytest` and wish to compile/open reports manually:
```bash
# Compile results into static report
allure generate reports/allure-results -o reports/allure-report --clean

# Open report in browser
allure open reports/allure-report
```

---

## 🏆 AUTOMATION STANDARDS ADHERENCE

### 1. POM (Page Object Model) Fluent Interface
All actions in `src/pages/` return `self` (Fluent Interface Pattern) to support elegant action chaining. Obvious methods do not contain unnecessary comments:
```python
def insert_user_details(self, username: str, password: str) -> 'LoginPage':
    self.try_locators([self._username_field], lambda l: self.fill_text(l, username), "username field")
    self.try_locators([self._password_field], lambda l: self.fill_text(l, password), "password field")
    return self
```

### 2. Zero Raw Assertions Policy
Test files are entirely free of raw assertions like `assert x == y`. Instead, assert calls are delegated to dedicated validator classes under `helpers/validators/`. This guarantees logging compliance and standardizes failures:
```python
# In step definition:
login_validator.validate_error_message(actual_error, expected_error)
```

### 3. Structured Masking Logger
An audit-compliant dynamic Logger rotates logs daily, auto-cleans old logs older than 7 days, and uses high-reliability regular expressions to mask credit card numbers, PAN, passwords, APIs, and credentials from printing to the console or logs:
```python
logger.info('Step: Inserting user credentials', {"username": username_str})
```
