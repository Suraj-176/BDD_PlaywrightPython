import os
import time
import inspect
import allure # Added for allure.step
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

        timeout = options.get("timeout", config.timeouts["navigation"]) # Using config timeout
        wait_until = options.get("waitUntil", "domcontentloaded")
        retries = options.get("retries", config.max_retries) # Using config retries

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
            f"URL: {target_url}\n" # Corrected target URL
            f"Last error: {str(last_error)}"
        )

    def select_element(self, locator: str, option):
        self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(locator)
        expect(element).to_be_visible(timeout=config.timeouts["action"]) # Using config timeout
        expect(element).to_be_enabled(timeout=config.timeouts["action"]) # Using config timeout
        element.select_option(option)

    def perform_mouse_action(self, action: str, locator: str) -> None:
        self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(locator)
        expect(element).to_be_visible(timeout=config.timeouts["action"]) # Using config timeout

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
        expect(element).to_be_visible(timeout=config.timeouts["action"])
        element.clear()
        element.fill(text)

    def click(self, locator: str):
        self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(locator)
        expect(element).to_be_visible(timeout=config.timeouts["action"])
        element.click()

    def get_text(self, locator: str) -> str:
        self.page.wait_for_load_state("domcontentloaded")
        element = self.page.locator(locator)
        expect(element).to_be_visible(timeout=config.timeouts["action"])
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

    def try_locators(self, locators: list[str], action, description: str = "element"):
        """
        Attempts to perform an action using a list of locators.
        If all locators fail and AI healing is enabled, it attempts to use AI to find the locator.

        :param locators: A list of Playwright locators (CSS or XPath strings).
        :param action: A callable (lambda or method) that takes a locator string and performs an action.
                       e.g., `lambda l: self.click(l)`
        :param description: A human-readable description of the element for logging and AI.
        :return: The result of the action, if any.
        :raises RuntimeError: If all locators fail and AI healing is disabled or fails.
        """
        last_error = None
        for i, locator_str in enumerate(locators):
            with allure.step(f"Attempting to find and interact with '{description}' using locator '{locator_str}' (Attempt {i+1}/{len(locators)})"):
                logger.info(f"[{self.__class__.__name__}] Attempting action on '{description}'", {
                    "locator": locator_str, "attempt": i + 1
                })
                try:
                    result = action(locator_str)
                    logger.info(f"[{self.__class__.__name__}] Action successful on '{description}' with locator '{locator_str}'")
                    return result
                except Exception as e:
                    last_error = e
                    logger.warn(f"[{self.__class__.__name__}] Action failed on '{description}' with locator '{locator_str}'", {
                        "error": str(e), "attempt": i + 1
                    })

        # All provided locators failed
        if config.enable_ai_healing:
            with allure.step(f"All standard locators failed. Attempting AI self-healing for '{description}'"):
                logger.info(f"[{self.__class__.__name__}] All standard locators failed for '{description}'. Attempting AI self-healing.")
                try:
                    ai_generated_locator = self.ai_get_locator(description)
                    if ai_generated_locator:
                        logger.info(f"[{self.__class__.__name__}] AI successfully generated locator for '{description}'", {
                            "ai_locator": ai_generated_locator
                        })
                        result = action(ai_generated_locator)
                        with allure.step(f"Action successful using AI-generated locator: '{ai_generated_locator}'"):
                            logger.info(f"[{self.__class__.__name__}] Action successful on '{description}' with AI-generated locator.")
                            return result
                    else:
                        raise RuntimeError(f"AI failed to generate a locator for '{description}'.")
                except Exception as ai_error:
                    logger.error(f"[{self.__class__.__name__}] AI self-healing failed for '{description}'", {
                        "ai_error": str(ai_error), "last_manual_error": str(last_error)
                    })
                    raise RuntimeError(
                        f"Failed to interact with '{description}' after all standard locators failed "
                        f"and AI self-healing also failed. Last manual error: {str(last_error)}. AI error: {str(ai_error)}"
                    ) from ai_error
        else:
            logger.error(f"[{self.__class__.__name__}] Failed to interact with '{description}' after all standard locators failed. AI self-healing is disabled.")
            raise RuntimeError(
                f"Failed to interact with '{description}' after all standard locators failed. "
                f"AI self-healing is disabled. Last error: {str(last_error)}"
            ) from last_error