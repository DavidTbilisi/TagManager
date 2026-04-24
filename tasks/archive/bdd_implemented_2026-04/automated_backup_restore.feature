Feature: Automated backup and restore of tag database
  As a user
  I want to easily back up and restore my tag database
  So that I can recover from data loss or migrate my tags to another system

  Scenario: Backup tag database
    Given a set of files with tags
    When I run the backup command
    Then a backup file of the tag database is created in a safe location
    And the backup includes all tags, files, and metadata

  Scenario: Restore tag database
    Given a backup file of the tag database
    When I run the restore command
    Then all tags and associations are restored in the system
    And the user is notified of any conflicts or errors
