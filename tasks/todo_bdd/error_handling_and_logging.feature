Feature: Error handling and logging for batch operations
  As a user or admin
  I want robust error handling and logging for all batch tag operations
  So that I can diagnose issues, recover from failures, and trust automation

  Scenario: Log errors during batch tag add/remove
    Given a batch operation affecting many files
    When an error occurs for a file (e.g., file not found, permission denied)
    Then the error is logged with details (file, error type, timestamp)
    And the operation continues for other files
    And the user receives a summary of successes and failures

  Scenario: View operation logs
    Given previous batch operations
    When I request the operation log
    Then I see a detailed record of actions, errors, and results
