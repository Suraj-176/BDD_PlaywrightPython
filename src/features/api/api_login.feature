@APILogin @API @Sanity
Feature: Dummy Bank REST API Transaction Validation

  Scenario: Bank API returns a successful response when creating a transaction
    When the user sends an API POST request to create a transaction with title "AML Alert" and userId 1
    Then the API response status should be 201
    And the API response should contain a valid transaction id
