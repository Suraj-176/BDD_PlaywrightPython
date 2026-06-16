import allure
from core.logger.logger import logger

class LoginValidator:
    """
    Business logic validator for authentication and API payloads.
    Enforces the 'Zero Raw Assertions Policy' by wrapping asserts inside structured, logging validator methods.
    """

    def validate_error_message(self, actual: str, expected: str) -> None:
        """
        Validates that the login error message displayed matches the expected message.
        """
        with allure.step(f'Validate login error message is "{expected}"'):
            logger.info("Validating login error message", {"actual": actual, "expected": expected})
            try:
                assert actual == expected, f"Expected error '{expected}', but got '{actual}'"
                logger.info("✅ Validation Passed: Login error message matches expected value")
            except AssertionError as error:
                logger.error("❌ Validation Failed: Login error message does not match", {
                    "actual": actual,
                    "expected": expected,
                    "error": str(error)
                })
                raise error

    def validate_successful_login(self, current_url: str) -> None:
        """
        Validates that the page URL matches the successful dashboard page URL.
        """
        with allure.step("Validate successful login and redirection"):
            logger.info("Validating dashboard redirection URL", {"currentUrl": current_url})
            try:
                assert "/inventory.html" in current_url, f"Expected URL to contain '/inventory.html', but got '{current_url}'"
                logger.info("✅ Validation Passed: Redirection to Inventory dashboard successful")
            except AssertionError as error:
                logger.error("❌ Validation Failed: Dashboard redirection URL mismatch", {
                    "currentUrl": current_url,
                    "error": str(error)
                })
                raise error

    def validate_api_status(self, actual: int, expected: int) -> None:
        """
        Validates the HTTP response status code.
        """
        with allure.step(f"Validate API HTTP Status matches {expected}"):
            logger.info("Validating HTTP status code", {"actual": actual, "expected": expected})
            try:
                assert actual == expected, f"Expected status {expected}, but got {actual}"
                logger.info("✅ Validation Passed: API Status matches")
            except AssertionError as error:
                logger.error("❌ Validation Failed: API Status mismatch", {
                    "actual": actual,
                    "expected": expected,
                    "error": str(error)
                })
                raise error

    def validate_api_token(self, token: str) -> None:
        """
        Validates that a valid token exists in the API response data.
        """
        with allure.step("Validate response contains a valid token"):
            logger.info("Validating authentication token format", {"token": token})
            try:
                assert token is not None, "Token is None"
                assert len(token) > 0, "Token is empty"
                logger.info("✅ Validation Passed: Token is valid and non-empty")
            except AssertionError as error:
                logger.error("❌ Validation Failed: Token is invalid", {"error": str(error)})
                raise error

    def validate_api_error(self, actual: str, expected: str) -> None:
        """
        Validates the API error payload.
        """
        with allure.step(f'Validate API Error matches "{expected}"'):
            logger.info("Validating API error payload", {"actual": actual, "expected": expected})
            try:
                assert actual == expected, f"Expected API error '{expected}', but got '{actual}'"
                logger.info("✅ Validation Passed: API error matches expected value")
            except AssertionError as error:
                logger.error("❌ Validation Failed: API error mismatch", {
                    "actual": actual,
                    "expected": expected,
                    "error": str(error)
                })
                raise error

    def validate_api_transaction_id(self, tx_id: any) -> None:
        """
        Validates that a valid transaction ID exists in the API response data.
        """
        with allure.step("Validate response contains a valid transaction ID"):
            logger.info("Validating transaction ID format", {"id": tx_id})
            try:
                assert tx_id is not None, "Transaction ID is None"
                assert int(tx_id) > 0, f"Expected positive numeric transaction ID, but got {tx_id}"
                logger.info("✅ Validation Passed: Transaction ID is valid and numeric")
            except (AssertionError, ValueError, TypeError) as error:
                logger.error("❌ Validation Failed: Transaction ID is invalid", {
                    "error": str(error)
                })
                raise AssertionError(f"Transaction ID {tx_id} is invalid: {str(error)}")
pass
