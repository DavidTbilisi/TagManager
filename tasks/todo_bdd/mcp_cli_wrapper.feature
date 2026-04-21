Feature: MCP/AI wrapper for TagManager CLI
  As a developer or automation tool
  I want to provide an MCP-compatible API that wraps the existing TagManager CLI
  So that I can add AI-powered features and integrate with other tools without changing the core CLI

  Scenario: AI-powered auto-tagging via wrapper
    Given a file is submitted to the MCP wrapper
    When the wrapper uses an AI model to analyze the file content
    And determines relevant tags
    Then the wrapper calls the CLI (e.g., 'tm add <file> --tags <tags>')
    And returns the result in MCP format

  Scenario: Semantic search via wrapper
    Given a user submits a natural language query to the MCP wrapper
    When the wrapper uses an AI model to interpret the query
    And determines relevant tags or search parameters
    Then the wrapper calls the CLI (e.g., 'tm search --tags <tags>')
    And returns the matching files in MCP format

  Scenario: Extensible plugin integration
    Given a new AI plugin is registered with the wrapper
    When a relevant event occurs (e.g., file added)
    Then the wrapper invokes the plugin, processes the result, and calls the CLI as needed
    And logs all actions and results for traceability
