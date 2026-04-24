Feature: Searching files by tag combinations
  As a user
  I want to search for files using combinations of tags (AND, OR, NOT)
  So that I can find files that match complex criteria

  Scenario: Search files with multiple tags (AND)
    Given files tagged with various topics
    When I search for files with tags "math" AND "guide"
    Then only files that have both tags are returned

  Scenario: Search files with alternative tags (OR)
    Given files tagged with various topics
    When I search for files with tags "math" OR "science"
    Then files with either tag are returned

  Scenario: Exclude files with a tag (NOT)
    Given files tagged with various topics
    When I search for files with tag "math" but NOT "guide"
    Then files with "math" but without "guide" are returned
