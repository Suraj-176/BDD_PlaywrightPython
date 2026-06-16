import os
import sys
import allure
import pytest
from playwright.sync_api import sync_playwright
from core.logger.logger import logger
from core.config.config import config
from core.api.api_client import APIClient
from src.pages.login_page import LoginPage
from helpers.validators.login_validator import LoginValidator

# Ensure root workspace is in Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load and validate configuration once
config.validate()

# Global dynamic reporting tracking variables
FAILED_BROWSERS = set()
TESTED_BROWSERS = set()
TESTS_EXECUTED_COUNT = 0

# Set up browser context arguments matching the TS configuration
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Overrides the default browser context arguments to set viewport and enable video recording.
    """
    return {
        **browser_context_args,
        "viewport": {
            "width": 1280,
            "height": 720,
        },
        "record_video_dir": "reports/videos/",
        "ignore_https_errors": True
    }

@pytest.fixture
def console_logs(page):
    """
    Captures console logs emitted by the page during execution.
    """
    logs = []
    page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))
    yield logs

@pytest.fixture
def login_page(page, console_logs):
    """
    Provides an instantiated LoginPage helper.
    """
    return LoginPage(page)

@pytest.fixture
def login_validator():
    """
    Provides the LoginValidator to enforce Zero Raw Assertions.
    """
    return LoginValidator()

@pytest.fixture
def api_client():
    """
    Provides a standardized API client targeting JSONPlaceholder.
    """
    return APIClient("https://jsonplaceholder.typicode.com")

# Pytest Hook that dynamically overrides Allure metadata BEFORE the test is reported
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """
    Pytest hook that runs at the very beginning of test setup.
    This dynamically modifies the pytest item's markers before Allure reads them.
    Maps folders precisely to match your TypeScript Allure report hierarchy:
    - parentSuite: "API Test Suite" or "UI Test Suite"
    - suite:       "api login" or "login"
    - subSuite:    (None - completely flat, no sub-suite folder!)
    """
    nodeid = item.nodeid
    is_api_test = "steps/api" in nodeid
    
    # 1. Strip any pre-existing suite markers to avoid collisions
    item.own_markers = [
        m for m in item.own_markers
        if m.name not in ["parent_suite", "suite", "sub_suite", "allure_label"]
    ]
    
    # 2. Add exact TS-matching 2-level folder hierarchy markers using official decorators
    if "steps/ui" in nodeid:
        item.add_marker(allure.parent_suite("UI Test Suite"))
        item.add_marker(allure.suite("login"))
    elif is_api_test:
        item.add_marker(allure.parent_suite("API Test Suite"))
        item.add_marker(allure.suite("api login"))

    # 3. Track tested browser engines dynamically
    try:
        callspec = getattr(item, "callspec", None)
        if callspec and hasattr(callspec, "params") and "browser" in callspec.params:
            TESTED_BROWSERS.add(callspec.params["browser"])
        else:
            # Fallback to check command line option directly
            browser_option = item.config.getoption("--browser")
            if browser_option:
                if isinstance(browser_option, list):
                    for b in browser_option:
                        TESTED_BROWSERS.add(b)
                else:
                    TESTED_BROWSERS.add(browser_option)
            else:
                TESTED_BROWSERS.add("chromium") # default
    except Exception:
        pass

@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """
    Pytest collection modifier hook.
    Detects API tests (located inside src/steps/api/) and filters out duplicate browser parameterizations.
    This guarantees that API backend tests run exactly ONCE (on Chromium) and completely skip redundant runs on other browser engines!
    """
    # Grab and track all configured browsers from the config dynamically
    try:
        browser_option = config.getoption("--browser")
        if browser_option:
            if isinstance(browser_option, list):
                for b in browser_option:
                    TESTED_BROWSERS.add(b)
            else:
                TESTED_BROWSERS.add(browser_option)
    except Exception:
        pass

    non_duplicate_items = []
    seen_api_tests = set()
    
    for item in items:
        nodeid = item.nodeid
        if "steps/api" in nodeid:
            # Extract base node name before [browser] suffix
            base_nodeid = nodeid.split("[")[0]
            if base_nodeid in seen_api_tests:
                continue # Skip duplicate browser run for API test
            seen_api_tests.add(base_nodeid)
        non_duplicate_items.append(item)
        
    items[:] = non_duplicate_items

# Allure failure reporting hook and fixture
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook that executes after each test phase.
    Stores the report outcome on the item so fixtures can access it during teardown.
    Also tracks overall run execution count and browser failure states in real-time.
    """
    global TESTS_EXECUTED_COUNT
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

    if rep.when == "call":
        TESTS_EXECUTED_COUNT += 1
        if rep.failed:
            try:
                browser = "chromium" # default
                callspec = getattr(item, "callspec", None)
                if callspec and hasattr(callspec, "params") and "browser" in callspec.params:
                    browser = callspec.params["browser"]
                FAILED_BROWSERS.add(browser)
            except Exception:
                pass

# Tracing on failure fixture (saves full interactive browser traces only on failure)
@pytest.fixture(autouse=True)
def trace_on_failure_reporter(request, context):
    """
    Session-level fixture that starts tracing before the test execution
    and retains/discards traces based on the outcome of the test.
    """
    is_api_test = "API" in request.node.keywords or "api" in request.node.nodeid.lower()
    if not is_api_test:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield
    if not is_api_test:
        rep_call = getattr(request.node, "rep_call", None)
        if rep_call and rep_call.failed:
            try:
                trace_dir = os.path.join("reports", "traces")
                os.makedirs(trace_dir, exist_ok=True)
                # Clean filename for safety on disk
                safe_name = "".join(c for c in request.node.name if c.isalnum() or c in (" ", "_", "-")).rstrip()
                trace_path = os.path.join(trace_dir, f"{safe_name}.zip")
                context.tracing.stop(path=trace_path)
                
                # Attach to Allure
                if os.path.exists(trace_path):
                    with open(trace_path, "rb") as f:
                        allure.attach(
                            f.read(),
                            name="Interactive Failure Trace",
                            attachment_type=allure.attachment_type.ZIP
                        )
            except Exception as e:
                logger.warn(f"Failed to save and attach browser tracing: {e}")
        else:
            # Test passed: completely discard trace buffer to save memory/disk
            try:
                context.tracing.stop()
            except Exception:
                pass

@pytest.fixture(autouse=True)
def failure_attachments_reporter(request, page, console_logs):
    """
    Post-test execution fixture that runs after each test step.
    If the test failed: captures screenshots, HTML source, console logs, and videos to attach to Allure.
    If the test passed: deletes the temporary video file to save disk space and retain video ONLY on failure.
    """
    yield
    # This runs AFTER the test completes
    rep_call = getattr(request.node, "rep_call", None)
    is_api_test = "API" in request.node.keywords or "api" in request.node.nodeid.lower()
    
    video = page.video
    
    if rep_call and rep_call.failed:
        if not is_api_test:
            project_name = "chromium"
            browser_option = request.config.getoption("--browser")
            if browser_option:
                project_name = browser_option[0] if isinstance(browser_option, list) else browser_option
            
            # 1. Capture Full Page Screenshot
            try:
                screenshot_bytes = page.screenshot(full_page=True)
                allure.attach(
                    screenshot_bytes,
                    name=f"Failure Screenshot - {project_name}",
                    attachment_type=allure.attachment_type.PNG
                )
            except Exception as e:
                logger.warn(f"Failed to capture failure screenshot: {e}")

            # 2. Capture Page Source
            try:
                html_source = page.content()
                allure.attach(
                    html_source,
                    name=f"Page Source - {project_name}",
                    attachment_type=allure.attachment_type.HTML
                )
            except Exception as e:
                logger.warn(f"Failed to capture HTML source: {e}")

            # 3. Capture Console Logs
            if console_logs:
                try:
                    allure.attach(
                        "\n".join(console_logs),
                        name=f"Console Logs - {project_name}",
                        attachment_type=allure.attachment_type.TEXT
                    )
                except Exception as e:
                    logger.warn(f"Failed to attach console logs: {e}")

            # 4. Capture Failure Video (close page to flush, read path, attach)
            try:
                page.close() # Close page to flush video encoding to disk
                if video:
                    video_path = video.path()
                    if video_path and os.path.exists(video_path):
                        with open(video_path, "rb") as f:
                            allure.attach(
                                f.read(),
                                name=f"Failure Video - {project_name}",
                                attachment_type=allure.attachment_type.WEBM
                            )
            except Exception as e:
                logger.warn(f"Failed to capture failure video: {e}")
    else:
        # Test passed: clean up disk space by deleting passing recordings
        try:
            page.close()
            if video:
                video.delete() # Deletes video from disk!
        except Exception:
            pass

@pytest.fixture(scope="session", autouse=True)
def global_setup_teardown(request):
    """
    Session-level fixture executing global setup and global teardown.
    Matches global-setup.ts / global-teardown.ts from TS framework.
    Includes xdist worker-safety: Wipes reports folders ONLY on master process to avoid collisions.
    All environment and executor files generation has been cleanly consolidated in run_tests.py
    for 100% process-safe execution.
    """
    # Global Setup: Wipe and prepare report folders
    import shutil
    raw_results_dir = os.path.join(os.getcwd(), "reports", "allure-results-raw")
    merged_results_dir = os.path.join(os.getcwd(), "reports", "allure-results")

    # If running with xdist parallel workers, skip wiping folders inside worker threads!
    # Our orchestrator run_tests.py handles pre-execution wiping safely.
    is_xdist_worker = "PYTEST_XDIST_WORKER" in os.environ
    if not is_xdist_worker:
        for directory in [raw_results_dir, merged_results_dir]:
            if os.path.exists(directory):
                try:
                    shutil.rmtree(directory)
                except Exception as e:
                    print(f"[Global Setup Warning] Could not delete {directory}: {e}")
            os.makedirs(directory, exist_ok=True)

    yield # Tests execute here

    # Global Teardown: Disconnect and clean up
    # Disconnect database connection pool only on master or final teardown
    if not is_xdist_worker:
        from core.database.db_client import DatabaseClient
        DatabaseClient.disconnect()
        logger.info("\n========== TEST RUN COMPLETED ==========\n")
pass
