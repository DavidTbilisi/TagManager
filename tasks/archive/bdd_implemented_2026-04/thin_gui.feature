Feature: Thin optional GUI for TagManager
  As a user who prefers a small visual surface over the terminal
  I want an optional lightweight GUI for everyday tagging and search
  So that I can discover and edit tags without memorizing CLI flags, while power users keep the CLI as the source of truth

  Background:
    Given TagManager is installed with the same tag database the CLI uses
    And the thin GUI is an optional component (not required for core workflows)

  Scenario: Launch the thin GUI locally
    When I start the thin GUI entrypoint (e.g. a dedicated subcommand or launcher)
    Then it binds only to the local machine (default localhost)
    And I can open it in my default browser or a minimal embedded shell, as designed
    And no cloud account is required for basic local use

  Scenario: Browse and select a file
    Given the thin GUI is running
    When I pick a file or folder from a constrained file picker or path field
    Then the GUI shows the current tags for that path from the same store as `tm path`
    And paths outside an allowed root (if configured) are rejected or warned clearly

  Scenario: Add tags from the GUI
    Given a file is selected and its current tags are visible
    When I enter one or more tags and confirm an add action
    Then tags are persisted using the same rules as `tm add` (aliases, presets if offered, optional dry-run)
    And the UI reflects success or a clear error message

  Scenario: Remove tags from the GUI
    Given a file is selected with existing tags
    When I remove a tag or clear tags for that path
    Then the change matches the semantics of `tm remove` / clear-tags behaviour the product documents
    And destructive actions can require confirmation when not in dry-run

  Scenario: Search by tags from the GUI
    Given the tag database is non-empty
    When I enter tag criteria (OR / AND as exposed by the UI)
    Then results match the same semantics as `tm search` for equivalent options
    And I can open or reveal a result path where the OS allows

  Scenario: Dry-run before writes
    Given I enable dry-run or preview mode in the GUI
    When I attempt an operation that would change the tag database
    Then no persistence occurs until I explicitly confirm or disable dry-run
    And the preview explains affected paths similarly to CLI `--dry-run` where applicable

  Scenario: GUI does not fork tag logic
    Given the thin GUI is implemented
    When any mutating or read-heavy operation runs
    Then it delegates to existing TagManager services or invokes `tm` / documented APIs
    And tag merge rules, journal, and config paths stay consistent with the CLI

  Scenario: Coexistence with automation
    Given I use MCP, `--json`, or scripts concurrently
    When the GUI and another client touch the same tag file
    Then behaviour matches normal multi-process use (atomic saves; last writer wins where documented)
    And the GUI does not hold an exclusive lock that blocks the CLI
