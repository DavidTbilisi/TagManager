Feature: Thin GUI — non-functional requirements
  As an operator or packager
  I want predictable security, footprint, and release behaviour for the optional thin GUI
  So that it stays maintainable and safe beside the CLI-first design

  Scenario: Local-only by default
    Given the thin GUI server component is started with default settings
    Then it listens only on loopback unless an explicit opt-in bind address is configured
    And documentation warns against exposing it on untrusted networks without authentication

  Scenario: Optional dependency boundary
    Given a minimal TagManager install
    When I run only CLI commands
    Then no extra Python packages are required for `tm` core commands
    And the thin GUI uses the same stdlib HTTP stack as `tm serve` (no separate GUI wheel)

  Scenario: Secrets and config
    Given the GUI reads configuration
    Then it uses the same configuration sources as the CLI where applicable
    And it does not log tag contents or paths at INFO level unless explicitly enabled for support

  Scenario: Packaging and discovery
    Given the feature ships
    Then README or docs describe how to start/stop the GUI and the default URL/port
    And CI continues to pass without launching a browser unless an explicit GUI test job is added

  Scenario: Accessibility and errors
    When an operation fails (disk, permissions, invalid tag file)
    Then the user sees a concise error derived from the same failure modes as the CLI
    And the application does not leave a zombie server process after normal quit
