# File: src/steps/ui/login_steps.py
import allure
from pytest_bdd import scenario, given, when, then, parsers
from playwright.sync_api import expect

# Import Page Objects and Validators
from src.pages.login_page import LoginPage
from helpers.validators.login_validator import LoginValidator
from core.config.config import config # Assuming config is globally available or imported

# Define the feature file path
FEATURE_FILE = "../features/login.feature"

# Register scenarios
@scenario(FEATURE_FILE, 'Successful Login with Valid Credentials')
def test_successful_login():
    pass

@scenario(FEATURE_FILE, 'Failed Login with Invalid Credentials')
def test_failed_login_invalid_credentials():
    pass

@scenario(FEATURE_FILE, 'Failed Login with Empty Credentials')
def test_failed_login_empty_credentials():
    pass

# Step Definitions
@given("I am on the login page")
@allure.step("Navigate to the login page")
def navigate_to_login_page(login_page: LoginPage):
    """
    Navigates to the application's login page.
    """
    login_page.goto_login_page()
    expect(login_page.page).to_have_url(config.base_url) # Ensure we are on the base URL for login

@when(parsers.parse('I enter "{username}" as username and "{password}" as password'))
@allure.step("Enter username and password")
def enter_credentials(login_page: LoginPage, username: str, password: str):
    """
    Enters the provided username and password into the login form fields.
    """
    login_page.insert_user_details(username, password)

@when("I click the login button")
@allure.step("Click the login button")
def click_login_button(login_page: LoginPage):
    """
    Clicks the login button.
    """
    login_page.click_on_submit_btn()

@then("I should be navigated to the products page")
@allure.step("Verify navigation to products page")
def verify_products_page_navigation(login_page: LoginPage, login_validator: LoginValidator):
    """
    Asserts that the user has been successfully navigated to the products page.
    """
    login_validator.validate_successful_login(login_page)

@then(parsers.parse('the page title should be "{expected_title}"'))
@allure.step("Verify products page title")
def verify_products_page_title(login_page: LoginPage, expected_title: str):
    """
    Asserts that the products page displays the correct title.
    """
    actual_title = login_page.get_products_page_title()
    expect(actual_title).to_equal(expected_title)

@then(parsers.parse('I should see an error message "{expected_message}"'))
@allure.step("Verify error message displayed")
def verify_error_message(login_page: LoginPage, login_validator: LoginValidator, expected_message: str):
    """
    Asserts that an error message is displayed with the expected text.
    """
    login_validator.validate_error_message(login_page, expected_message)

@then("I should remain on the login page")
@allure.step("Verify remaining on login page")
def verify_remaining_on_login_page(login_page: LoginPage, login_validator: LoginValidator):
    """
    Asserts that the user has remained on the login page (i.e., not navigated away).
    """
    login_validator.validate_still_on_login_page(login_page)