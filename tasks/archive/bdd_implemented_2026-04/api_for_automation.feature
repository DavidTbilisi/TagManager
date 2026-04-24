Feature: API or CLI for scripting/integration
  As a developer or automation tool
  I want a simple API or CLI endpoints for managing tags
  So that I can integrate TagManager with other tools and automate workflows

  Scenario: List tags for a file via API
    Given a file in the system
    When I call the API endpoint to list tags for that file
    Then I receive a list of all tags assigned to the file

  Scenario: Add tags to a file via API
    Given a file in the system
    When I call the API endpoint to add tags to that file
    Then the tags are added and the response confirms success

  Scenario: Remove tags from a file via API
    Given a file in the system
    When I call the API endpoint to remove tags from that file
    Then the tags are removed and the response confirms success
