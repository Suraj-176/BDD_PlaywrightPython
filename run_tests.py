import os
import sys
import json
import shutil
import socket
import subprocess
import argparse
import hashlib
from datetime import datetime
from dotenv import load_dotenv

# Load environmental variables from .env
load_dotenv()

# Dictionary mapping custom browser profiles and mobile devices to their underlying Playwright engines
DEVICE_TO_ENGINE = {
    "pixel 5": "chromium",
    "pixel 8 pro": "chromium",
    "galaxy s24": "chromium",
    "iphone 13": "webkit",
    "ipad pro 11": "webkit",
    "edge": "chromium",
    "chromium": "chromium",
    "firefox": "firefox",
    "webkit": "webkit"
}

def clean_reports():
    """
    Cleans previous report folders to start with a 100% clean slate.
    """
    reports_dir = os.path.join(os.getcwd(), "reports")
    results_raw = os.path.join(reports_dir, "allure-results")
    allure_report = os.path.join(reports_dir, "allure-report")

    print("🧹 Cleaning previous test reports...")
    for directory in [results_raw, allure_report]:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"   Deleted: {directory}")
            except Exception as e:
                print(f"   ⚠️ Could not delete {directory}: {e}")
        os.makedirs(directory, exist_ok=True)

def run_pytest(marker=None, browser=None, headless=None, headed=None, workers=None, parallel=False, additional_args=None):
    """
    Runs pytest command with custom variables and .env configuration fallback.
    """
    cmd = [sys.executable, "-m", "pytest"]
    
    # Configure allure-results directory
    cmd.append("--alluredir=reports/allure-results")

    if marker:
        cmd.extend(["-m", marker])

    # 1. Determine Browser(s) - Resolve mobile devices and custom engines to unique Playwright engines
    if browser:
        if isinstance(browser, list):
            pytest_browsers = set()
            for b in browser:
                resolved_engine = DEVICE_TO_ENGINE.get(b.lower(), "chromium")
                pytest_browsers.add(resolved_engine)
            for engine in pytest_browsers:
                cmd.extend(["--browser", engine])
        else:
            resolved_engine = DEVICE_TO_ENGINE.get(browser.lower(), "chromium")
            cmd.extend(["--browser", resolved_engine])

    # 2. Determine Headless/Headed State (CLI Argument overrides .env value, which defaults to True)
    env_headless = os.getenv("HEADLESS", "true").lower() == "true"
    is_headless = env_headless  # Base default from .env
    
    if headed:
        is_headless = False
    elif headless:
        is_headless = True

    # If is_headless is False, we pass --headed to pytest-playwright
    if not is_headless:
        cmd.append("--headed")

    # 3. Determine Workers/Parallel State (CLI Argument overrides .env value, which defaults to 1)
    env_workers = os.getenv("WORKERS", "1").lower()
    active_workers = env_workers  # Base default from .env
    
    if workers:
        active_workers = workers.lower()
    elif parallel:
        active_workers = "auto"

    # If active_workers is greater than 1, auto, or a positive integer, add -n to pytest cmd list
    if active_workers != "1" and active_workers != "none" and active_workers != "0":
        cmd.extend(["-n", active_workers])

    if additional_args:
        cmd.extend(additional_args)

    print(f"🚀 Executing Command: {' '.join(cmd)}")
    print(f"   ├─ Browser Target(s): {', '.join(browser) if isinstance(browser, list) else (browser if browser else 'Default (chromium)')}")
    print(f"   ├─ Headless Mode: {is_headless}")
    print(f"   └─ Parallel Workers: {active_workers if (active_workers != '1') else 'Sequential (1)'}")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ Failed to run pytest: {e}")
        return 1

def generate_allure_metadata(browser_list=None):
    """
    Dynamically generates the environment.properties and executor.json metadata files 
    directly in the master process, ensuring 100% compatibility with parallel pytest-xdist runs.
    Also post-processes raw result JSON files on disk to collapse and merge multi-browser UI runs
    and remove redundant browser parameter rows from API test reports.
    """
    results_dir = os.path.join(os.getcwd(), "reports", "allure-results")
    if not os.path.exists(results_dir):
        os.makedirs(results_dir, exist_ok=True)

    # Use specified browser/device list, or default
    raw_tested_browsers = set(browser_list) if browser_list else {"chromium"}

    # 1. Post-process raw result JSON files to surgically override Allure display metadata
    print("🧹 Post-processing raw result JSON files for clean Suite grouping...")
    executed_count = 0
    failed_browsers = set()
    
    try:
        for filename in os.listdir(results_dir):
            if filename.endswith("-result.json"):
                file_path = os.path.join(results_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    fullname = data.get("fullName", "")
                    is_api_test = "steps.api" in fullname
                    is_ui_test = "steps.ui" in fullname
                    parameters = data.get("parameters", [])

                    # Find the browser name for this specific test result file
                    browser_name = "chromium"
                    for p in parameters:
                        if p.get("name") == "browser_name":
                            browser_name = p.get("value").replace("'", "").replace('"', "")

                    # Extract Gherkin Scenario Title from the results description
                    scenario_name = "BDD Scenario"
                    description = data.get("description", "")
                    if ": " in description:
                        raw_title = description.split(": ", 1)[1]
                        
                        # Resolve parameters for Scenario Outlines dynamically using the example dict on disk
                        example_param = None
                        for p in parameters:
                            if p.get("name") == "_pytest_bdd_example":
                                try:
                                    example_dict = eval(p.get("value"))
                                    if isinstance(example_dict, dict):
                                        example_param = example_dict
                                except Exception:
                                    pass
                                    
                        if example_param:
                            for key, val in example_param.items():
                                placeholder = f'"{key}"'
                                placeholder_bracket = f'<{key}>'
                                if placeholder in raw_title:
                                    raw_title = raw_title.replace(placeholder, f'"{val}"')
                                elif placeholder_bracket in raw_title:
                                    raw_title = raw_title.replace(placeholder_bracket, f'"{val}"')
                        scenario_name = raw_title
                    else:
                        scenario_name = data.get("name", "").split("[")[0].replace("test_", "").replace("_", " ").capitalize()

                    # Calculate a stable, browser-independent history ID based on the clean scenario name
                    stable_hash = hashlib.md5(scenario_name.encode("utf-8")).hexdigest()

                    # Track executions count
                    executed_count += 1
                    
                    # Track failures
                    if data.get("status") in ["failed", "broken"]:
                        failed_browsers.add(browser_name)

                    # Apply dynamic metadata modifications directly in the JSON on disk!
                    
                    # A. Completely remove standard browser parameters to prevent Allure from splitting runs
                    data["parameters"] = [
                        p for p in parameters
                        if p.get("name") not in ["browser", "browser_name"]
                    ]
                    
                    # B. Add standardized browser parameter to represent ALL tested browsers/devices concurrently (UI only)
                    if is_ui_test:
                        tested_str = ", ".join(sorted(list(raw_tested_browsers))) if raw_tested_browsers else "chromium"
                        data["parameters"].append({"name": "browser", "value": f"'{tested_str}'"})
                    
                    # C. Set identical display names (collapses/merges runs in Allure report)
                    data["name"] = scenario_name
                    
                    # D. Force identical stable history ID
                    data["historyId"] = stable_hash
                    
                    # Save the modified JSON back to disk
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                        
                except Exception as inner_e:
                    print(f"   ⚠️ Failed to post-process Allure result file {filename}: {inner_e}")
    except Exception as e:
        print(f"   ⚠️ Failed to post-process Allure result files: {e}")

    print("📊 Writing dynamic Allure Dashboard metadata widgets...")

    # Format dashboard metadata values based on actual tested browser engines and devices
    tested_str = ", ".join(sorted(list(raw_tested_browsers))) if raw_tested_browsers else "chromium"
    failed_str = ", ".join(sorted(list(failed_browsers))) if failed_browsers else "None"
    
    # Capitalize browser engine values for display
    browser_engines_set = set()
    for b in raw_tested_browsers:
        engine = DEVICE_TO_ENGINE.get(b.lower(), "chromium")
        browser_engines_set.add(engine.capitalize())
    browser_engines = ", ".join(sorted(list(browser_engines_set))) if browser_engines_set else "Chromium"
    
    env = os.getenv("TEST_ENV", "SIT")
    build_number = os.getenv("BUILD_NUMBER", "")
    commit_hash = os.getenv("GIT_COMMIT", "")

    # Write environment.properties (100% dynamic based on actual runs!)
    try:
        properties_path = os.path.join(results_dir, "environment.properties")
        properties_content = (
            f"Project=ICICI Pru - Anti-Money Laundering\n"
            f"Environment={env}\n"
            f"Devices={tested_str}\n"
            f"Browsers={browser_engines}\n"
            f"Platform={sys.platform}\n"
            f"Framework=Playwright-BDD (Python)\n"
            f"Version=1.0.0\n"
            f"Python=v{sys.version.split()[0]}\n"
            f"BuildNumber={build_number}\n"
            f"CommitHash={commit_hash}\n"
            f"Description=BDD tags: LoginPage, InvalidCredentials, Sanity\n"
            f"Browsers Tested={tested_str}\n"
            f"Executions={executed_count}\n"
            f"Failed On={failed_str}\n"
        )
        with open(properties_path, "w", encoding="utf-8") as f:
            f.write(properties_content)
        print("   ✅ Allure environment.properties generated successfully.")
    except Exception as e:
        print(f"   ⚠️ Failed to write Allure environment.properties: {e}")

    # Write executor.json (matching TS format)
    try:
        executor_path = os.path.join(results_dir, "executor.json")
        is_ci = os.getenv("CI", "false").lower() == "true"
        build_num = os.getenv("BUILD_NUMBER") or os.getenv("GITHUB_RUN_NUMBER", "")
        build_url = os.getenv("BUILD_URL") or os.getenv("GITHUB_SERVER_URL", "")
        
        executor_data = {
            "name": "CI Runner" if is_ci else "Local Machine",
            "type": "ci" if is_ci else "pytest",
            "url": build_url,
            "buildName": env,
            "buildUrl": build_url,
            "host": socket.gethostname(),
            "timestamp": datetime.utcnow().isoformat()[:-3] + "Z"
        }
        with open(executor_path, "w", encoding="utf-8") as f:
            json.dump(executor_data, f, indent=2)
        print("   ✅ Allure executor.json generated successfully.")
    except Exception as e:
        print(f"   ⚠️ Failed to write Allure executor.json: {e}")

def generate_report():
    """
    Checks if allure is available (or falls back to npx allure) and generates the HTML report.
    Supports shell=True on Windows to avoid WinError 2 for cmd/bat scripts.
    """
    print("📊 Compiling Allure report...")
    
    is_windows = os.name == 'nt'
    
    # Check if allure exists globally
    has_global_allure = shutil.which("allure") is not None
    
    # If not global, check if npx is available to run allure
    has_npx = shutil.which("npx") is not None
    
    if not has_global_allure and not has_npx:
        print("⚠️ 'allure' command line tool and 'npx' were not found in PATH.")
        print("   Please install Allure CLI globally or configure Node.js/npx.")
        print("   Install globally on Windows using Scoop: scoop install allure")
        print("   Or run: npm install -g allure-commandline")
        print("   Raw results are written to: reports/allure-results")
        return False

    cmd = []
    if has_global_allure:
        cmd = ["allure", "generate", "reports/allure-results", "-o", "reports/allure-report", "--clean"]
    else:
        print("ℹ️ Global Allure not found. Falling back to local compilation via 'npx allure'...")
        cmd = ["npx", "allure", "generate", "reports/allure-results", "-o", "reports/allure-report", "--clean"]

    try:
        # shell=True is mandatory on Windows to execute cmd/bat script executors
        subprocess.run(cmd, check=True, shell=is_windows)
        print("✅ Allure report generated successfully inside: reports/allure-report")
        return True
    except Exception as e:
        print(f"❌ Failed to generate Allure report: {e}")
        return False

def open_report():
    """
    Automatically opens the generated Allure report in browser.
    """
    is_windows = os.name == 'nt'
    has_global_allure = shutil.which("allure") is not None
    has_npx = shutil.which("npx") is not None
    
    if not has_global_allure and not has_npx:
        return

    cmd = []
    if has_global_allure:
        cmd = ["allure", "open", "reports/allure-report"]
    else:
        cmd = ["npx", "allure", "open", "reports/allure-report"]

    print("🌐 Launching Allure report server...")
    try:
        subprocess.run(cmd, check=True, shell=is_windows)
    except KeyboardInterrupt:
        print("\n👋 Allure server stopped.")
    except Exception as e:
        print(f"❌ Failed to open Allure report: {e}")

def main():
    parser = argparse.ArgumentParser(description="ICICI Pru Python Playwright Test Runner")
    parser.add_argument("-b", "--browser", action="append", help="Target browser engine(s) or device profile(s). Can pass multiple times (e.g. -b chromium -b firefox -b 'Pixel 5')")
    parser.add_argument("-m", "--marker", help="Run tests matching specific pytest marker (e.g. Sanity, API, Smoke)")
    parser.add_argument("--headed", action="store_true", help="Force tests to run in headed mode")
    parser.add_argument("--headless", action="store_true", help="Force tests to run in headless mode")
    parser.add_argument("-p", "--parallel", action="store_true", help="Run tests in parallel (shorthand for --workers auto)")
    parser.add_argument("-w", "--workers", help="Number of parallel workers (e.g. auto, 1, 3, or 'none' for sequential)")
    parser.add_argument("--no-clean", action="store_true", help="Do not clean reports folder before running")
    parser.add_argument("--no-open", action="store_true", help="Do not automatically open the Allure report in browser after completion")
    
    args, unknown = parser.parse_known_args()

    # 1. Clean report directories
    if not args.no_clean:
        clean_reports()

    # 2. Run test suites
    exit_code = run_pytest(
        marker=args.marker,
        browser=args.browser,
        headless=args.headless,
        headed=args.headed,
        workers=args.workers,
        parallel=args.parallel,
        additional_args=unknown
    )

    # 3. Generate dynamic Allure dashboard metadata files
    generate_allure_metadata(args.browser)

    # 4. Handle reporting
    # Automatically compile and open Allure report in browser by default if NOT in CI and not disabled via --no-open
    is_ci = os.getenv("CI", "false").lower() == "true"
    
    if generate_report():
        if not is_ci and not args.no_open:
            open_report()

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
pass
