import allure
from pytest_bdd import scenarios, given, when, then, parsers
from core.logger.logger import logger

# Symmetrical path: Moving to UI subfolder means feature is 2 levels up
scenarios('../../features/ui/login.feature')

@given('user navigates to the application')
def navigate_to_application(login_page):
    with allure.step('Given user navigates to the application'):
        logger.info('Step: Navigating to login page')
        login_page.goto_login_page()

@when(parsers.re(r'User enters "(?P<username>[^"]*)" username and "(?P<password>[^"]*)" password'))
def enter_credentials(login_page, username, password):
    # Normalize empty inputs (represented as blank cells in Gherkin table)
    # Gherkin parses empty cells in Examples as empty strings
    username_str = username if username else ""
    password_str = password if password else ""
    
    with allure.step(f'When User enters "{username_str}" username and "{password_str}" password'):
        logger.info('Step: Inserting user credentials', {"username": username_str})
        login_page.insert_user_details(username_str, password_str)

@when('Click on the login button')
def click_login_button(login_page):
    with allure.step('Step: Clicking login button'):
        logger.info('Step: Submitting login form')
        login_page.click_on_submit_btn()

@then(parsers.parse('User encounter an error message "{expected_error}"'))
def verify_error_message(login_page, login_validator, expected_error):
    with allure.step(f'Then User encounters error message: "{expected_error}"'):
        logger.info('Step: Validating login error message')
        actual_error = login_page.get_login_error_message()
        
        # Enterprise assertion using our validator (Zero Raw Assertions!)
        login_validator.validate_error_message(actual_error, expected_error)
pass
