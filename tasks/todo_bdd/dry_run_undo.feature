Feature: Dry-run and undo for all destructive operations
  As a user
  I want to preview changes and undo batch operations
  So that I can avoid accidental data loss and recover from mistakes

  Scenario: Dry-run for batch tag removal
    Given a batch operation to remove tags from many files
    When I run the command with --dry-run
    Then no changes are made
    And I see a detailed preview of what would happen

  Scenario: Undo last batch operation
    Given a previous batch operation that changed tags
    When I run the undo command
    Then all changes from that operation are reverted
    And the user is notified of the result
