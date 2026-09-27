# File: src/features/login.feature
Feature: User Login Functionality

  As a user of the SauceDemo application,
  I want to be able to log in
  So that I can access the product catalog.

  @ui @login @positive
  Scenario: Successful Login with Valid Credentials
    Given I am on the login page
    When I enter "standard_user" as username and "secret_sauce" as password
    And I click the login button
    Then I should be navigated to the products page
    And the page title should be "Products"

  @ui @login @negative
  Scenario: Failed Login with Invalid Credentials
    Given I am on the login page
    When I enter "locked_out_user" as username and "secret_sauce" as password
    And I click the login button
    Then I should see an error message "Epic sadface: Sorry, this user has been locked out."
    And I should remain on the login page

  @ui @login @negative
  Scenario: Failed Login with Empty Credentials
    Given I am on the login page
    When I enter "" as username and "" as password
    And I click the login button
    Then I should see an error message "Epic sadface: Username is required"
    And I should remain on the login page