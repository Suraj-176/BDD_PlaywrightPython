import pytest
import allure
from pytest_bdd import scenarios, when, then, parsers
from core.logger.logger import logger

# Symmetrical path: Moving to API subfolder means feature is 2 levels up
scenarios('../../features/api/api_login.feature')

@pytest.fixture
def api_context():
    """
    Stores shared state across BDD steps for API validations.
    """
    return {}

@when(parsers.parse('the user sends an API POST request to create a transaction with title "{title}" and userId {user_id:d}'))
def send_post_transaction(api_client, api_context, title: str, user_id: int):
    with allure.step(f'the user sends an API POST request to create a transaction with title "{title}" and userId {user_id}'):
        logger.info('Step: Executing Bank Transaction API Request', {"title": title, "userId": user_id})

        # Send a real POST request to our Core API Client
        response = api_client.post('/posts', {
            "title": title,
            "body": 'AML Compliance Alert Triggered',
            "userId": user_id,
        })
        
        # Save response context
        api_context['response'] = response

@then(parsers.parse('the API response status should be {expected_status:d}'))
def verify_api_status(api_context, login_validator, expected_status: int):
    response = api_context['response']
    actual_status = response['status']
    
    with allure.step(f'Then the API response status should be {expected_status}'):
        logger.info('Step: Validating API HTTP Status', {
            "actual": actual_status,
            "expected": expected_status,
        })

        # Enforcing our zero raw assertions mandate via the validator
        login_validator.validate_api_status(actual_status, expected_status)

@then('the API response should contain a valid transaction id')
def verify_transaction_id(api_context, login_validator):
    response = api_context['response']
    data = response['data']
    
    # In jsonplaceholder, the ID is typically returned as 'id' in the JSON body
    tx_id = data.get('id') if isinstance(data, dict) else None
    
    with allure.step('Then the API response should contain a valid transaction id'):
        logger.info('Step: Validating transaction ID', {"id": tx_id})

        login_validator.validate_api_transaction_id(tx_id)
pass
