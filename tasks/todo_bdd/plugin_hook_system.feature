Feature: Plugin or hook system for custom automation
  As a power user or developer
  I want to define custom scripts or hooks for auto-tagging, integration, or notifications
  So that I can extend TagManager's automation to fit my workflow

  Scenario: Register a custom hook
    Given a user-defined script or plugin
    When I register it as a hook for a specific event (e.g., file added, tag changed)
    Then the script is executed automatically when the event occurs
    And the user can see logs or results of the hook execution

  Scenario: Auto-tagging with a plugin
    Given a plugin that analyzes file content
    When a new file is added
    Then the plugin suggests or assigns tags automatically
