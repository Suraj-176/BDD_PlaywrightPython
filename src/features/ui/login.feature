@LoginPage
Feature: Verify login page scenarios

Background:
Given user navigates to the application

@InvalidCredentials @Sanity
Scenario Outline: User attempts login with username "<username>" and password "<password>"
  When User enters "<username>" username and "<password>" password
  And Click on the login button
  Then User encounter an error message "<error_message>"

  Examples:
    | username        | password     | error_message                                                             |
    | prasad          | secret_sauce | Epic sadface: Username and password do not match any user in this service |
    | problem_user    | prasad       | Epic sadface: Username and password do not match any user in this service |
    | problem_user    |              | Epic sadface: Password is required                                        |
    |                 | secret_sauce | Epic sadface: Username is required                                        |
    | locked_out_user | secret_sauce | Epic sadface: Sorry, this user has been locked out.                       |
