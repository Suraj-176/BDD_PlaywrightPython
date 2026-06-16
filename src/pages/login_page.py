from core.base.base_page import BasePage

class LoginPage(BasePage):
    """
    Page Object Model representing the SauceDemo login page.
    Extends BasePage to inherit high-reliability navigation and self-healing locators.
    """

    def __init__(self, page):
        super().__init__(page)

    # ─── 1. SELECTOR DECLARATIONS (AI HEALING COMPATIBLE) ───
    _username_field = "#user-name"
    _password_field = "#password"
    _login_button = "#login-button"
    _error_message = 'h3[data-test="error"]'

    # ─── 2. NAVIGATION METHODS ───

    def goto_login_page(self) -> 'LoginPage':
        """
        Navigates the browser to the application login page.
        """
        self.goto()
        return self

    # ─── 3. PAGE INTERACTION METHODS (SEMANTIC ACTIONS) ───

    def insert_user_details(self, username: str, password: str) -> 'LoginPage':
        """
        Securely enters the user credentials into the username and password fields.
        Automatically invokes AI self-healing fallbacks if any selector fails to render.

        :param username: Registered ICICI Pru customer or agent username.
        :param password: Confidential account password (automatically masked in logs).
        :return: The LoginPage instance for action chaining.
        """
        self.try_locators(
            [self._username_field],
            lambda l: self.fill_text(l, username),
            "username input field"
        )
        self.try_locators(
            [self._password_field],
            lambda l: self.fill_text(l, password),
            "password input field"
        )
        return self

    def click_on_submit_btn(self) -> 'LoginPage':
        """
        Clicks on the login/submit button to send the credentials.
        """
        self.try_locators(
            [self._login_button],
            lambda l: self.click(l),
            "login submit button"
        )
        return self

    # ─── 4. VALUE RETRIEVAL METHODS (VALIDATOR TARGETS) ───

    def get_login_error_message(self) -> str:
        """
        Retrieves the error message text displayed below the login form.
        """
        return self.try_locators(
            [self._error_message],
            lambda l: self.get_text(l),
            "red error message shown below login form when credentials are wrong or empty"
        )
pass
