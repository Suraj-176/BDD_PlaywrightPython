# 🎭 ICICI Pru - Python Playwright BDD Senior Automation Engineering Instructions (GEMINI.md)

This file contains foundational mandates, workflows, and strict engineering standards for any Gemini CLI agent operating in this repository. These instructions take absolute precedence over general defaults.

---

## 🚀 THE INLINE DRAFT, REVIEW & UNDO WORKFLOW

To ensure you have full visibility and control over all code modifications, every file edit must strictly follow this **Interactive Inline suggestion & Undo** workflow.

### 🔄 Workflow Process:

#### Step 1: Create a Secure Backup
Before modifying any existing file (such as page objects, steps, validators, or helpers), you **MUST** create a local backup copy of that file on disk.
*   **Backup naming convention:** `[filepath].bak` (e.g., `src/pages/login_page.py` $\rightarrow$ `src/pages/login_page.py.bak`).
*   This backup must be maintained until the user explicitly accepts or rejects the changes.

#### Step 2: Inject Inline Draft into the File
You must write the proposed changes directly into the target file. Structure the edited area so both the proposed code and the original code are visible side-by-side:
1.  **Keep the new code ACTIVE** (runnable).
2.  **Comment out the old original code** inside multiline docstrings (`""" ... """`).
3.  **Wrap both blocks in high-visibility markup comments**:

```python
# ⏩ GEMINI PROPOSED START (Active Code)
def validate_kyc(customer_id: str) -> bool:
    logger.info('Performing automated KYC validation for PEP customer', {"customerId": customer_id})
    status = kyc_api.check(customer_id)
    return status == 'VERIFIED'
# ⏸️ GEMINI ORIGINAL CODE (COMMENTED OUT)
"""
def validate_kyc(customer_id: str) -> bool:
    return True # placeholder
"""
# ⏩ GEMINI PROPOSED END
```

#### Step 3: Present Review Prompt
Once the draft is written to the file, you **MUST** pause and ask the user to review the file directly in their editor using a structured multiple-choice `ask_user` call:
*   **Header:** `Review changes`
*   **Question:** `"I have inserted the proposed changes directly into [filepath] with side-by-side annotations. Please review the changes in your editor. What would you like to do?"`
*   **Options:**
    *   `[Accept]` $\rightarrow$ Permanently apply these changes.
    *   `[Undo / Reject]` $\rightarrow$ Revert the file back to its original state.

#### Step 4: Finalize the File & Run Code Quality Checks
*   **If the user chooses `[Accept]`:**
    1.  Perform a surgical replace to remove the marker comments and the commented-out original code.
    2.  Keep only the clean, final, active proposed code in the file.
    3.  Delete the temporary backup file (`[filepath].bak`).
*   **If the user chooses `[Undo / Reject]`:**
    1.  Over-write the target file with the contents of the backup file (`[filepath].bak`).
    2.  Delete the backup file.
    3.  Confirm to the user that the file has been successfully reverted to its original state.

---

## 🛠️ SENIOR AUTOMATION ENGINEERING STANDARDS

### 1. Folder Structure & Roles
Maintain strict boundary separations:
*   `src/features/` $\rightarrow$ Gherkin `.feature` scenarios.
*   `src/steps/` $\rightarrow$ Pytest-BDD step definitions (must wrap in allure steps and log inputs).
*   `src/pages/` $\rightarrow$ Page Objects extending `BasePage` (do not modify `BasePage` or `AIService`).
*   `helpers/testdata/` $\rightarrow$ Test data factories (`UserFactory`, `config.json`).
*   `helpers/validators/` $\rightarrow$ Business logic validators (`LoginValidator`).
*   `core/database/` $\rightarrow$ Database connections and pooling.
*   `core/api/` $\rightarrow$ REST API Clients with retry engines.
*   `core/logger/` $\rightarrow$ Structured, audit-compliant logging.

### 2. POM (Page Object Model) Patterns
*   **Always extend `BasePage`** in every page class.
*   **Private Selectors:** Prepend selectors with `_` (e.g., `_username_field = "#user-name"`).
*   **Use `try_locators`** for robust clicks, text entries, and selects, utilizing Groq AI self-healing capabilities:
    ```python
    self.try_locators(
        [self._username_field],
        lambda l: self.fill_text(l, username),
        'username input field'
    )
    ```
*   Implement the **Fluent Interface Pattern**: Actions that do not navigate away must return `'PageClass'` and `return self` to allow method chaining.

### 3. Step Definition Patterns
*   **Wrap step logic inside Allure blocks:** Every step must have a descriptive allure step name using `with allure.step(...)`.
*   **Enforce logging:** Record the beginning, parameters, and successful completion of every step using `logger.info()`.
    ```python
    @when(parsers.parse('User enters "{username}" username and "{password}" password'))
    def enter_credentials(login_page, username, password):
        with allure.step(f'When User enters "{username}" username and "{password}" password'):
            logger.info('Step: Inserting user credentials', {"username": username})
            login_page.insert_user_details(username, password)
    ```

### 4. Zero Raw Assertions Policy
*   **NEVER** write raw `assert value == ...` directly inside steps.
*   **ALWAYS** use or create a specialized Validator class (under `helpers/validators/`) to assert conditions. Validators must log their checks and output structured audit results.

---

## 🚦 QUICK VERIFICATION COMMANDS

Ensure these commands run clean after any modification:
```bash
# Run all tests using Python runner
python run_tests.py

# Run sanity tests and generate/open Allure report
run_tests.bat -m Sanity --open

# Run specifically on Chrome browser
run_tests.bat -b chromium --headed
```

---

## 🔒 SECURITY & SECRETS
*   **NEVER** write, log, or commit passwords, API keys, or raw secrets.
*   Read credentials from environment variables (managed by `.env` file).
*   Mask sensitive values when outputting logs or allure reports using our dynamic Logger.
