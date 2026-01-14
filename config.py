from pathlib import Path

MDMEMO_ROOT = Path.home() / "mdmemo"  # Root directory for storing memo files

EDITOR_COMMAND = "vim -c 'cd %:p:h'"  # Supports other CLI editors like 'nano' or 'helix'
ENABLE_REMOVE = False                 # If True, adds "remove" to the available actions.
DEFAULT_ACTION = "view"               # Options: "edit", "jump", "remove", "view"

VIEW_COMMAND = 'bat --style plain --language markdown'  # Supports other CLI renderers, e.g., 'glow' or 'rich'.
# VIEW_COMMAND = 'glow'
# VIEW_COMMAND = 'rich --markdown -'

# Fzf interface options and keybindings
FZF_OPTS = ["--multi", "--height=50%"]
FZF_KEYS = {
    "edit"  : {"tab": "mark", "enter": "edit"        , "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},
    "jump"  : {"tab": "mark", "enter": "jump"        , "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},
    "list"  : {"tab": "mark", "enter": DEFAULT_ACTION, "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},
    "remove": {"tab": "mark", "enter": "remove"      , "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},
    "search": {"tab": "mark", "enter": DEFAULT_ACTION, "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},
    "view"  : {"tab": "mark", "enter": "view"        , "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},
}
