# Fish completions for FileTagger (`ftag` / `filetagger`).
# Install:  cp completions/tm.fish ~/.config/fish/completions/ftag.fish
#           (or symlink). Reload the shell or run: complete -C ftag

complete -c ftag -f

set -l __ftag_cmds add remove ls path tags storage search bulk filter config alias preset export import doctor undo watch graph mcp serve gui windows mv clean stats

complete -c ftag -n '__fish_use_subcommand' -a "$__ftag_cmds"

complete -c ftag -n '__fish_seen_subcommand_from bulk' -a 'add remove retag'
complete -c ftag -n '__fish_seen_subcommand_from filter' -a 'duplicates orphans similar clusters isolated'
complete -c ftag -n '__fish_seen_subcommand_from config' -a 'get set delete list reset info export import categories validate'
complete -c ftag -n '__fish_seen_subcommand_from alias' -a 'add list remove clear'
complete -c ftag -n '__fish_seen_subcommand_from preset' -a 'save list apply delete'
complete -c ftag -n '__fish_seen_subcommand_from search' -a 'save list show delete run'
complete -c ftag -n '__fish_seen_subcommand_from windows' -a 'install-context-menu uninstall-context-menu'
