Feature: Model Context Protocol (MCP) support for AI-powered tagging
  As a user or developer
  I want TagManager to support MCP for AI integration
  So that I can leverage advanced AI models for smarter tagging, search, and automation

  Scenario: AI-powered auto-tagging
    Given a file with rich content (text, image, PDF, etc.)
    When the file is added or updated
    Then TagManager uses an MCP-compatible AI model to analyze the content
    And suggests or assigns relevant tags automatically
    And the user can review, accept, or modify the suggested tags

  Scenario: Semantic search with AI
    Given a collection of tagged files
    When I perform a search using natural language or concepts
    Then TagManager uses an MCP-compatible AI model to interpret the query
    And returns files that are semantically relevant, not just by exact tag match

  Scenario: AI plugin integration
    Given a custom AI workflow (e.g., OCR, NLP, image recognition)
    When I register the workflow as an MCP plugin
    Then TagManager can invoke the plugin for specific automation tasks
    And the results are integrated into the tagging and search system

  Scenario: Extensible AI model support
    Given new AI models or services become available
    When I configure TagManager to use a new MCP endpoint
    Then the system can leverage the new model for tagging, search, or recommendations
    And users can choose or prioritize which AI models to use
