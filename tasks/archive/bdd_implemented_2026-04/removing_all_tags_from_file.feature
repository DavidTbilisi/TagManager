Feature: Removing all tags from a file
  As a user
  I want to be able to remove all tags from a specific file in one command
  So that I can reset or clean up the tag state for that file easily

  Scenario: Remove all tags from a file
    Given a file with multiple tags assigned
    When I issue a command to remove all tags from that file
    Then the file should have no tags remaining
    And the operation should not affect tags on other files
    And the command should succeed even if the file has no tags
    And the user should receive clear feedback about the result
