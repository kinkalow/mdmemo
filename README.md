# MdMemo

**MdMemo** is a simple terminal-based Markdown memo manager.
It enables quick file selection through **[fzf](https://github.com/junegunn/fzf)** or shell completion, while providing enhanced terminal rendering using your preferred tool, such as [bat](https://github.com/sharkdp/bat), [glow](https://github.com/charmbracelet/glow), or [rich-cli](https://github.com/Textualize/rich-cli).


## Key Features

* **Fuzzy Navigation**: Uses `fzf` to select files via a terminal interface.
* **Terminal Rendering**: Displays Markdown content in the terminal using your choice of tool (e.g., `bat`, `glow`, or `rich-cli`).
* **Shell Completion**: Includes Zsh and Bash completion scripts for files and actions.
* **Core Actions**: Provides basic management functions:
    * `view`, `edit`: To read and write your memos.
    * `remove`, `search`: To clean up or find specific content.
    * `list`, `jump`: To browse files or go to their directories.
    * `config`: To quickly customize your environment.


## Prerequisites

* **Python 3.9+**
* **[fzf](https://github.com/junegunn/fzf)**
* **Markdown Viewer** (Default: [bat](https://github.com/sharkdp/bat). Supports any tool like [glow](https://github.com/charmbracelet/glow), [rich-cli](https://github.com/Textualize/rich-cli), or simply standard `less`/`cat`)


## Installation

First, ensure you have `fzf` and a Markdown viewer installed.

1.  Clone the repository:
    ```bash
    git clone git@github.com:kinkalow/mdmemo.git
    cd mdmemo
    ```
2.  Run the installer:
    ```bash
    bash ./install.sh
    # You will be prompted to enter a command name (default: m)
    ```
3.  Follow the printed instructions to update your `~/.zshrc` or `~/.bashrc`.


## Uninstallation

To remove MdMemo, delete the following:

```bash
rm ~/.local/bin/m
rm -rf ~/.local/share/mdmemo
```

Note: Manually remove any MdMemo related lines from your `~/.zshrc` or `~/.bashrc`.


## Usage

By default, all memos are stored in `~/mdmemo`.
You can change this location by modifying `MDMEMO_ROOT` in your `config.py` (see the `m any c` example below).

```bash
# Basic syntax
m [filename/word] [action]

# Examples
m file e      # Open "~/mdmemo/file.md" in your editor (e: shortcut for edit)
              # Default editor is vim. Change it via EDITOR in config.py.
              # Tip: Press Tab to auto-complete file names and actions.
m file v      # View "file.md" with rich formatting (v: shortcut for view)
m file l      # List files filtered by "file" in the filename (l: shortcut for list)
m file r      # Remove "file.md" (r: shortcut for remove)
              # Note: Disabled by default in config for safety.
m file j      # Jump to the directory containing file.md (j: shortcut for jump)
m dir/file e  # Handles hierarchical structures. This opens ~/mdmemo/dir/file.md.

m             # Launch fzf to browse all memos (List Action)
m file        # Runs the DEFAULT_ACTION set in your config (default: view)

m word s      # Search for "word" inside all memos and list matches in fzf (s: shortcut for search)
m any c       # Open the config.py file in your editor (c: shortcut for config)
              # Note: "any" can be any string; the 'c' action always opens config.
```
