import os
import time
import inspect
from playwright.sync_api import Page, expect
from core.ai.ai_service import AIService
from core.logger.logger import logger
from core.config.config import config

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def goto(self, url: str = None, options: dict = None):
        if options is None:
            options = {}

        timeout = options.get("timeout", 120000)
        wait_until = options.get("waitUntil", "domcontentloaded")
        retries = options.get("retries", 3)

        target_url = url or os.getenv("BASE_URL") or config.base_url
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[{self.__class__.__name__}] Navigation attempt {attempt}/{retries}", {
                    "url": target_url
                })

                self.page.goto(target_url, timeout=timeout, wait_until=wait_until)
                self.page.wait_for_load_state("domcontentloaded")

                logger.info(f"[{self.__class__.__name__}] Navigation successful", {"attempt": attempt})
                return # Success, exit
            except Exception as error:
                last_error = error
                reason = str(error)

                logger.warn(f"[{self.__class__.__name__}] Navigation attempt failed", {
                    "attempt": attempt, "reason": reason
                })

                # Fatal errors that shouldn't be retried
                fatal_errors = [
                    "ERR_NAME_NOT_RESOLVED",
                    "ERR_CONNECTION_REFUSED",
                    "ERR_INVALID_URL"
                ]
                if any(e in reason for e in fatal_errors):
                    logger.error(f"[{self.__class__.__name__}] Fatal navigation error", reason)
                    raise last_error

                # Wait before retrying (longer each attempt)
                if attempt < retries:
                    wait_ms = attempt * 2000
                    logger.info(f"[{self.__class__.__name__}] Waiting before navigation retry", {"waitMs": wait_ms})
                    self.page.wait_for_timeout(wait_ms)

        # All retries exhausted
        raise RuntimeError(
            f"[{self.__class__.__name__}] Navigation failed after {retries} attempts\n"
            f"URL: {target_url}\n"
            f"Last error: {str(last_error)}"
        )

    def select_element(self, locator: str, option):
        self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(locator)
        expect(element).to_be_visible(timeout=2000)
        expect(element).to_be_enabled(timeout=2000)
        element.select_option(option)

    def perform_mouse_action(self, action: str, locator: str) -> None:
        self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(locator)
        expect(element).to_be_visible(timeout=2000)

        action_lower = action.lower()
        if action_lower == "click":
            element.click()
        elif action_lower == "doubleclick":
            element.dblclick()
        elif action_lower == "rightclick":
            element.click(button="right")
        elif action_lower == "hover":
            element.hover()
        else:
            raise ValueError(f"Unsupported mouse action: {action}")

    def fill_text(self, locator: str, text: str):
        self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(locator)
        expect(element).to_be_visible(timeout=2000)
        element.clear()
        element.fill(text)

    def click(self, locator: str):
        self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(locator)
        expect(element).to_be_visible(timeout=2000)
        element.click()

    def get_text(self, locator: str) -> str:
        self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(locator)
        expect(element).to_be_visible(timeout=2000)
        return element.inner_text()

    # ─── AI Methods ─────────────────────────────────────────

    def ai_get_locator(self, element_description: str) -> str:
        dom = self.page.content()
        return AIService.get_locator(dom, element_description)

    def ai_fill(self, element_description: str, text: str):
        locator = self.ai_get_locator(element_description)
        self.fill_text(locator, text)

    def ai_click(self, element_description: str):
        locator = self.ai_get_locator(element_description)
        self.click(locator)

    def ai_get_text(self, element_description: str) -> str:
        locator = self.ai_get_locator(element_description)
        return self.get_text(locator)

    # ─── try_locators with AI healing ───────────────────

    def try_locators(self, locators: list, action, field_name: str):
        call_site = self._get_call_site()
        errors = []

        for locator in locators:
            try:
                return action(locator)
            except Exception as err:
                message = str(err)
                errors.append(f"  • {locator} → {message}")
                logger.warn(
                    f"[{self.__class__.__name__}] Locator failed for \"{field_name}\": {locator}"
                    f"\n  Reason: {message}"
                )

        if os.getenv("ENABLE_AI_HEALING") != "true":
            raise RuntimeError(
                f"[{self.__class__.__name__}] All locators failed for: \"{field_name}\"\n"
                f"Failures:\n" + "\n".join(errors) + "\n"
                f"Called from: {call_site}\n"
                "Set ENABLE_AI_HEALING=true to allow AI locator fallback."
            )

        logger.warn(f"[{self.__class__.__name__}] Attempting AI healing for \"{field_name}\"")
        try:
            ai_locator = self.ai_get_locator(field_name)
            return action(ai_locator)
        except Exception:
            raise RuntimeError(
                f"[{self.__class__.__name__}] All locators + AI healing failed for: \"{field_name}\"\n"
                f"Failures:\n" + "\n".join(errors) + "\n"
                f"Called from: {call_site}"
            )

    def _get_call_site(self) -> str:
        stack = inspect.stack()
        # Find first stack frame outside of core files
        for frame in stack[2:]:
            filename = frame.filename
            if "base_page" not in filename and "python" not in filename:
                return f"{os.path.basename(filename)}:{frame.lineno}"
        return "unknown"
