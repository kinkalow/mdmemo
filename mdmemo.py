import importlib.util
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

# --- Configuration ---


@dataclass
class AppConfig:
    MDMEMO_ROOT: Path = Path.home() / "mdmemo"
    CONFIG_FILE: Path = Path(__file__).parent / "config.py"
    EDITOR_COMMAND: str = "vim -c 'cd %:p:h'"
    ENABLE_REMOVE: bool = False
    DEFAULT_ACTION: str = "view"
    VIEW_COMMAND: str = 'bat --style plain --language markdown'
    FZF_OPTS: list[str] = field(default_factory=lambda: ["--multi", "--height=50%"])
    FZF_KEYS: dict[str, dict[str, str]] = field(default_factory=lambda: {  # fmt: off
        "edit"  : {"tab": "mark", "enter": "edit"  , "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},  # noqa: E203
        "jump"  : {"tab": "mark", "enter": "jump"  , "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},  # noqa: E203
        "list"  : {"tab": "mark", "enter": ""      , "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},  # noqa: E203
        "remove": {"tab": "mark", "enter": "remove", "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},  # noqa: E203
        "search": {"tab": "mark", "enter": ""      , "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},  # noqa: E203
        "view"  : {"tab": "mark", "enter": "view"  , "ctrl-e": "edit", "ctrl-j": "jump", "ctrl-r": "remove", "ctrl-v": "view"},  # noqa: E203
    })  # fmt: on

    def __post_init__(self) -> None:
        self.FZF_KEYS["list"]["enter"] = self.DEFAULT_ACTION
        self.FZF_KEYS["search"]["enter"] = self.DEFAULT_ACTION


cfg = AppConfig()

if cfg.CONFIG_FILE.exists():
    spec = importlib.util.spec_from_file_location("mdmemo_config", cfg.CONFIG_FILE)
    if spec and spec.loader:
        user_conf = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(user_conf)
            for key in vars(cfg):
                if hasattr(user_conf, key):
                    user_val = getattr(user_conf, key)
                    default_val = getattr(cfg, key)
                    # FIXME: Shallow type check only
                    if isinstance(user_val, type(default_val)):
                        setattr(cfg, key, user_val)
                    else:
                        print(f"Error: Config '{key}' expected {type(default_val).__name__}, got {type(user_val).__name__}")
                        sys.exit(1)
        except Exception as e:
            print(f"Error: Failed to load config: {e}")
            sys.exit(1)

cfg.MDMEMO_ROOT.mkdir(parents=True, exist_ok=True)


# --- Core Classes ---

class FZFRunner:
    def __init__(self, config: AppConfig):
        self.cfg = config

    def run(self, paths: list[Path], current_action: str, header: str) -> Optional[tuple[str, list[Path]]]:
        if not paths:
            print("× No candidates available")
            return None

        display_map = {str(p.relative_to(self.cfg.MDMEMO_ROOT)): p for p in paths}
        action_map = self.cfg.FZF_KEYS[current_action]
        expect_keys = [k for k in action_map.keys() if k != "enter" and k != "tab"]

        help_items = []
        for k, v in action_map.items():
            if v == "remove" and not self.cfg.ENABLE_REMOVE: continue
            lbl = k.lower().replace("ctrl", "c").replace("alt", "m")
            help_items.append(f"{lbl}:{v.capitalize()}")
        header_text = f"{header}  {'  '.join(help_items)}"

        cmd = ["fzf", "--header", header_text]
        if expect_keys: cmd.append(f"--expect={','.join(expect_keys)}")
        if current_action == "list" or "search": cmd.append("--no-select-1")
        else: cmd.append("--select-1")
        cmd += self.cfg.FZF_OPTS

        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(input="\n".join(display_map.keys()))

            if process.returncode not in (0, 130):
                print(f"Error: fzf exited with return code {process.returncode}")
                if stderr: print(f"Details: {stderr.strip()}")
                print("Please check your FZF_OPTS and FZF_KEYS in config.py")
                sys.exit(1)

            if process.returncode == 130: return None  # Cancel
            lines = stdout.splitlines()
            if not lines: return None

            key = lines[0].strip() or "enter" if expect_keys else "enter"
            selected = lines[1:] if expect_keys else lines
            targets = [display_map[item] for item in selected if item in display_map]

            action_to_do = action_map.get(key)
            if action_to_do:
                return action_to_do, targets

        except FileNotFoundError:
            print("Error: fzf not found. Please install fzf.")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error while running fzf: {e}")
            sys.exit(1)

        return None


class ActionManager:
    def __init__(self, config: AppConfig, fzf: FZFRunner):
        self.cfg = config
        self.fzf = fzf

    def _ensure_md(self, name: str) -> str:
        return name if name.endswith(".md") else f"{name}.md"

    def _get_all_files_sorted(self) -> list[Path]:
        files = list(self.cfg.MDMEMO_ROOT.rglob("*.md"))
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return files

    def _handle_fzf_result(self, result: Optional[tuple[str, list[Path]]]):
        if not result:
            return
        action_type, targets = result
        if action_type == "edit": self.edit(targets)
        elif action_type == "jump": self.jump(targets)
        elif action_type == "remove": self.remove(targets)
        elif action_type == "view": self.view(targets)
        else: ValueError(f"Unknown action for key: {action_type}")

    def _run_editor(self, paths: list[Path]):
        path_args = " ".join(shlex.quote(str(p)) for p in paths)
        cmd = f"{self.cfg.EDITOR_COMMAND} {path_args}"
        try:
            subprocess.run(cmd, stderr=subprocess.PIPE, check=True, shell=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Editor Error: Return code: {e.returncode}")
            print(f"Details:\n{e.stderr.strip() if e.stderr else e}")
            print(f"Please check your EDITOR_COMMAND: {self.cfg.EDITOR_COMMAND}")
            sys.exit(1)
        except Exception as e:
            print("Unexpected Error: Could not launch the editor process")
            print(f"Details:\n{e}")
            sys.exit(1)

    def config_edit(self):
        self._run_editor([cfg.CONFIG_FILE])

    def new(self, name: str):
        path = self.cfg.MDMEMO_ROOT / self._ensure_md(name)
        if path.exists():
            print("× Already exists")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        self.edit([path])

    def edit(self, paths: list[Path]):
        if not paths: return
        self._run_editor(paths)

    def jump(self, paths: list[Path]):
        if not paths: return
        parent_dir = paths[0].parent
        print("-" * 50)
        print(f"Jumping to: {parent_dir}")
        print("Starting a new shell in this directory")
        print("Type 'exit' to return to your previous location")
        print("-" * 50)
        os.chdir(parent_dir)
        os.system(os.environ.get('SHELL', 'bash'))

    def remove(self, paths: list[Path]):
        if not self.cfg.ENABLE_REMOVE or not paths: return
        rel_paths = [str(p.relative_to(self.cfg.MDMEMO_ROOT)) for p in paths]
        if input(f"Remove {len(paths)} file(s) ({', '.join(rel_paths)})? (y/n): ").lower() == "y":
            for p in paths:
                p.unlink()
                print(f"Removed: {p.relative_to(self.cfg.MDMEMO_ROOT)}")

    def view(self, paths: list[Path]):
        if not paths: return
        terminal_size = shutil.get_terminal_size(fallback=(0, 24))
        width = terminal_size.columns
        results = []
        for i, p in enumerate(paths):
            relative_path = p.relative_to(self.cfg.MDMEMO_ROOT)
            if len(paths) > 1:
                header_text = f"<!-- File: {relative_path} -->"
                padding_length = max(0, width - len(header_text))
                results.append(f"{header_text[:-3]}{"-" * padding_length}-->")
            with open(p, "r", encoding="utf-8") as f:
                results.append(f.read())
        full_text = "\n".join(results)
        try:
            subprocess.run(cfg.VIEW_COMMAND, stderr=subprocess.PIPE, input=full_text, check=True, shell=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Viewer Error: Return code: {e.returncode}")
            print(f"Details:\n{e.stderr.strip() if e.stderr else e}")
            print(f"Please check your VIEW_COMMAND: {self.cfg.VIEW_COMMAND}")
            sys.exit(1)
        except Exception as e:
            print("Unexpected Error: Could not launch the viewer process")
            print(f"Details:\n{e}")
            sys.exit(1)

    ActionType = Literal["edit", "jump", "remove", "view"]

    def dispatch_by_action_type(self, name: str, action_type: ActionType):
        search_pat = self._ensure_md(name)
        matches = list(self.cfg.MDMEMO_ROOT.rglob(search_pat))
        if not matches:
            if action_type == "edit": self.new(name)
            else: print(f"× No file found matching '{search_pat}'")
            return

        if len(matches) == 1:
            if action_type == "edit": self.edit(matches)
            if action_type == "jump": self.jump(matches)
            elif action_type == "remove": self.remove(matches)
            else: self.view(matches)
        else:
            result = self.fzf.run(matches, action_type, f"Select files ({action_type}):")
            self._handle_fzf_result(result)

    def list(self, target_name: Optional[str] = None):
        files = self._get_all_files_sorted()
        if target_name:
            files = [f for f in files if target_name in str(f.relative_to(self.cfg.MDMEMO_ROOT))]
        result = self.fzf.run(files, "list", f"List filter:{target_name}" if target_name else "List Memos")
        self._handle_fzf_result(result)

    def search(self, query: str):
        try:
            output = subprocess.check_output(
                ["grep", "-rl", query, str(self.cfg.MDMEMO_ROOT)], text=True
            ).splitlines()
            files = [Path(f) for f in output if f.endswith(".md")]
            if not files: raise subprocess.CalledProcessError(1, "grep")
            result = self.fzf.run(files, "search", f"Search filter:{query}")
            self._handle_fzf_result(result)
        except subprocess.CalledProcessError:
            print(f"× No match for content: {query}")


# --- Initialization ---

fzf = FZFRunner(cfg)
act = ActionManager(cfg, fzf)


# --- Main Logic ---

def resolve_args(args: list[str]):
    target = args[0] if len(args) > 0 else None
    action_name = "list"

    if len(args) == 1:
        action_name = cfg.DEFAULT_ACTION
    elif len(args) >= 2:
        input_act = args[1].lower()
        available = ["config", "edit", "jump", "list", "search", "view"]
        if cfg.ENABLE_REMOVE: available.append("remove")

        for a in available:
            if a.startswith(input_act):
                action_name = a
                break
        else:
            if cfg.ENABLE_REMOVE: print(f"Error: Unknown action '{input_act}'. Available: {', '.join(available)}")
            else: print("Error: 'remove' action is disabled in your config (ENABLE_REMOVE=False)")
            sys.exit(1)

    return target, action_name


def main():

    if os.getenv("MDMEMO_COMPLETION") == "1":
        cur_input = os.getenv("MDMEMO_COMP_WORD", "")
        cur_path = Path(cur_input)
        all_files = act._get_all_files_sorted()
        candidates = set() if os.sep in cur_input else {f.stem for f in all_files if f.stem.startswith(cur_input)}
        for f in all_files:
            rel_path = f.relative_to(cfg.MDMEMO_ROOT).with_suffix("")
            if rel_path.as_posix().startswith(cur_path.as_posix()):
                f_parts = rel_path.parts
                cur_depth = len(cur_path.parts)
                if len(f_parts) > cur_depth + 1:
                    candidates.add(str(Path(*f_parts[:cur_depth + 1])) + os.sep)
                else:
                    candidates.add(str(rel_path))
        for item in sorted(candidates):
            print(item)
        return

    target, action_name = resolve_args(sys.argv[1:])

    if not target: act.list()
    elif action_name == "config": act.config_edit()
    elif action_name == "list": act.list(target)
    elif action_name == "search": act.search(target)
    else: act.dispatch_by_action_type(target, action_name)


if __name__ == "__main__":
    main()
