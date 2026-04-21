Feature: Plugin system for CLI extensibility
  As a developer or user
  I want to install, manage, and use plugins with the CLI
  So that the community can extend TagManager without waiting for core changes

  Scenario: Install a plugin
    Given a plugin package is available
    When I run 'tm plugin install <plugin>'
    Then the plugin is downloaded and registered with TagManager
    And it is available for use in commands

  Scenario: Use a plugin command
    Given a plugin is installed
    When I run 'tm <plugin-command> [args]'
    Then the plugin is invoked as part of the CLI
    And its output is integrated with the rest of the system

  Scenario: List and manage plugins
    Given multiple plugins are installed
    When I run 'tm plugin list'
    Then I see all available plugins and their status
    And I can enable, disable, or remove plugins as needed
