Feature: Composability and Unix philosophy for CLI
  As a power user or developer
  I want the CLI to support stdin/stdout piping, JSON output, quiet mode, and deterministic flags
  So that I can compose TagManager with other tools and use it in system-level automation

  Scenario: Pipe input and output between tools
    Given a list of files or tags from another tool via stdin
    When I run a TagManager command that reads from stdin
    Then it processes the input and outputs results to stdout
    And the output can be piped to another tool

  Scenario: JSON output for scripting
    Given I run a TagManager command with --json
    Then the output is in machine-readable JSON format
    And it includes all relevant data for further processing

  Scenario: Quiet mode for automation
    Given I run a TagManager command with --silent or --quiet
    Then only essential output or errors are shown
    And no extra formatting or prompts appear

  Scenario: Deterministic flags
    Given I run a command with the same flags and input
    Then the output is always the same (no random order, timestamps, etc.)
