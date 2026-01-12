#!/bin/bash

set -eu

read -p "Enter command name (default: m): " CMD
CMD=${CMD:-m}

SHARE_DIR="$HOME/.local/share/mdmemo"
BIN_DIR="$HOME/.local/bin"
COMP_DIR="$SHARE_DIR/completions"
DISPLAY_COMP_DIR="${COMP_DIR/#$HOME/\$HOME}"

if [ -e "$BIN_DIR/$CMD" ]; then
  echo "Warning: '$CMD' already exists in $BIN_DIR."
  read -p "Do you want to overwrite it? (y/N): " CONFIRM
  if [[ ! "$CONFIRM" =~ ^[yY]$ ]]; then
    echo "Installation aborted."
    exit 1
  fi
fi

mkdir -p "$SHARE_DIR" "$BIN_DIR" "$COMP_DIR"

cp mdmemo.py "$SHARE_DIR/mdmemo.py"
cp config.py "$SHARE_DIR/config.py"

cat << EOF > "$BIN_DIR/$CMD"
#!/bin/bash
python3 "$SHARE_DIR/mdmemo.py" "\$@"
EOF
chmod +x "$BIN_DIR/$CMD"

cat << EOF > "$COMP_DIR/_$CMD"
#compdef $CMD
_$CMD() {
  local MDMEMO_PATH="$SHARE_DIR/mdmemo.py"
  local -a files actions
  if (( CURRENT == 2 )); then
    files=(\${(f)"\$(MDMEMO_COMPLETION=1 python3 "\$MDMEMO_PATH")"})
    _describe 'memos' files
  elif (( CURRENT == 3 )); then
    actions=(
      'conifg:Edit configuration file'
      'edit:Open in editor'
      'jump:jump to a memo'
      'list:List all memos'
      'remove:Remove memo'
      'search:Search inside files'
      'view:View markdown'
    )
    _describe 'actions' actions
  fi
}
EOF

cat << EOF > "$COMP_DIR/mdmemo.bash"
_${CMD}_completion() {
  local cur MDMEMO_PATH
  MDMEMO_PATH="$SHARE_DIR/mdmemo.py"
  COMPREPLY=()
  cur="\${COMP_WORDS[COMP_CWORD]}"
  if [ "\$COMP_CWORD" -eq 1 ]; then
    local files=\$(MDMEMO_COMPLETION=1 python3 "\$MDMEMO_PATH")
    COMPREPLY=( \$(compgen -W "\${files}" -- "\$cur") )
  elif [ "\$COMP_CWORD" -eq 2 ]; then
    local actions="config edit jump list remove search view"
    COMPREPLY=( \$(compgen -W "\${actions}" -- "\$cur") )
  fi
}
complete -F _${CMD}_completion $CMD
EOF

echo "------------------------------------------"
echo "Installation finished!"
echo ""
echo "Add this to your ~/.zshrc"
echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "fpath=(\"$DISPLAY_COMP_DIR\" \$fpath)"
echo "autoload -Uz compinit && compinit"
echo ""
echo "Or add this to your ~/.bashrc"
echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
echo "source \"$DISPLAY_COMP_DIR/mdmemo.bash\""
echo "------------------------------------------"
