Feature: Exporting and importing tag data
  As a user
  I want to export all tag data to a portable format and import it later
  So that I can back up, migrate, or share my tag database

  Scenario: Export tag data
    Given a set of files with tags
    When I run the export command
    Then a file containing all tag associations is created in a standard format (e.g., JSON, CSV)
    And the export includes all tags, files, and metadata

  Scenario: Import tag data
    Given an export file with tag data
    When I run the import command
    Then all tags and associations are restored in the system
    And existing tags are merged or updated as needed
    And the user is notified of any conflicts or errors
