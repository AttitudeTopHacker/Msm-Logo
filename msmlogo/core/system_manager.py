"""System interface for discovering Plymouth themes, reading status, and executing privileged operations."""

import os
import sys
import subprocess
import json
import re
from typing import List, Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QProcess


class InstalledThemeInfo:
    def __init__(self, id_name: str, display_name: str, description: str, module_name: str, plymouth_path: str, is_active: bool, is_custom: bool, thumbnail_path: Optional[str] = None):
        self.id_name = id_name
        self.display_name = display_name
        self.description = description
        self.module_name = module_name
        self.plymouth_path = plymouth_path
        self.is_active = is_active
        self.is_custom = is_custom
        self.thumbnail_path = thumbnail_path


class ApplyWorker(QObject):
    progress_updated = pyqtSignal(int, str)
    log_line = pyqtSignal(str)
    completed = pyqtSignal(bool, str)

    def __init__(self, action: str, **kwargs):
        super().__init__()
        self.action = action
        self.kwargs = kwargs
        self.process: Optional[QProcess] = None

    def start(self):
        helper_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend", "apply_helper.py"))
        
        python_bin = "/usr/bin/python3" if os.path.exists("/usr/bin/python3") else sys.executable
        args = [python_bin, helper_path, "--action", self.action]
        if self.action == "apply":
            args.extend(["--theme-dir", self.kwargs["theme_dir"], "--theme-name", self.kwargs["theme_name"]])
            if self.kwargs.get("sync_grub", False):
                args.append("--sync-grub")
        elif self.action == "switch":
            args.extend(["--plymouth-path", self.kwargs["plymouth_path"]])
            if self.kwargs.get("sync_grub", False):
                args.append("--sync-grub")
        elif self.action == "delete":
            args.extend(["--theme-name", self.kwargs["theme_name"]])

        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)

        cmd = "pkexec"
        cmd_args = args
        self.log_line.emit(f"Executing with administrative privileges: {cmd} {' '.join(cmd_args)}")
        self.process.start(cmd, cmd_args)

    def cancel(self):
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

    def _on_stdout(self):
        if not self.process:
            return
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("MSM_STATUS:"):
                try:
                    payload = json.loads(line[len("MSM_STATUS:"):])
                    msg = payload.get("message", "")
                    prog = payload.get("progress", -1)
                    if prog >= 0:
                        self.progress_updated.emit(prog, msg)
                    self.log_line.emit(f"• {msg}")
                except Exception:
                    self.log_line.emit(line)
            elif line.startswith("MSM_LOG:"):
                self.log_line.emit(line[len("MSM_LOG:"):])
            else:
                self.log_line.emit(line)

    def _on_stderr(self):
        if not self.process:
            return
        data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            line = line.strip()
            if line:
                self.log_line.emit(f"[ERR] {line}")

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus):
        success = (exit_code == 0)
        msg = "Operation completed successfully." if success else f"Operation exited with code {exit_code}."
        self.completed.emit(success, msg)


class SystemManager:
    PLYMOUTH_THEMES_DIR = "/usr/share/plymouth/themes"
    BACKUP_FILE = "/etc/msmlogo_backup.json"

    @classmethod
    def get_active_theme_path(cls) -> Optional[str]:
        try:
            res = subprocess.run(["update-alternatives", "--query", "default.plymouth"], capture_output=True, text=True, check=True)
            for line in res.stdout.splitlines():
                if line.startswith("Value:"):
                    return line.split(":", 1)[1].strip()
        except Exception as e:
            print(f"Error querying active theme: {e}")
        return None

    @classmethod
    def list_installed_themes(cls) -> List[InstalledThemeInfo]:
        active_path = cls.get_active_theme_path()
        themes = []

        if not os.path.exists(cls.PLYMOUTH_THEMES_DIR):
            return themes

        for entry in sorted(os.listdir(cls.PLYMOUTH_THEMES_DIR)):
            entry_path = os.path.join(cls.PLYMOUTH_THEMES_DIR, entry)
            if not os.path.isdir(entry_path):
                continue

            plymouth_file = os.path.join(entry_path, f"{entry}.plymouth")
            if not os.path.exists(plymouth_file):
                # Search for any .plymouth file in directory
                candidates = [f for f in os.listdir(entry_path) if f.endswith(".plymouth")]
                if candidates:
                    plymouth_file = os.path.join(entry_path, candidates[0])
                else:
                    continue

            name = entry
            description = ""
            module_name = "unknown"

            # Parse plymouth file
            try:
                with open(plymouth_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("Name=") and name == entry:
                            name = line.split("=", 1)[1].strip()
                        elif line.startswith("Description="):
                            description = line.split("=", 1)[1].strip()
                        elif line.startswith("ModuleName="):
                            module_name = line.split("=", 1)[1].strip()
            except Exception:
                pass

            is_active = (active_path == plymouth_file) or (active_path and os.path.basename(active_path) == os.path.basename(plymouth_file))
            is_custom = entry.startswith("msm-")

            # Find thumbnail preview
            thumbnail = None
            for thumb_candidate in ["preview.png", "background.png", "animation-0001.png", "watermark.png", "bgrt-fallback.png"]:
                candidate_path = os.path.join(entry_path, thumb_candidate)
                if os.path.exists(candidate_path):
                    thumbnail = candidate_path
                    break

            themes.append(InstalledThemeInfo(
                id_name=entry,
                display_name=name,
                description=description,
                module_name=module_name,
                plymouth_path=plymouth_file,
                is_active=is_active,
                is_custom=is_custom,
                thumbnail_path=thumbnail
            ))

        return themes

    @classmethod
    def get_official_default_theme_path(cls) -> Optional[str]:
        if os.path.exists(cls.BACKUP_FILE):
            try:
                with open(cls.BACKUP_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                orig = data.get("original_theme")
                if orig and os.path.exists(orig) and "msm-" not in orig:
                    return orig
            except Exception:
                pass

        candidates = [
            "/usr/share/plymouth/themes/mint-logo/mint-logo.plymouth",
            "/usr/share/plymouth/themes/bgrt/bgrt.plymouth",
            "/usr/share/plymouth/themes/ubuntu-logo/ubuntu-logo.plymouth",
            "/usr/share/plymouth/themes/spinner/spinner.plymouth",
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return None

    @classmethod
    def has_factory_backup(cls) -> bool:
        return cls.get_official_default_theme_path() is not None

    @classmethod
    def is_custom_theme_active(cls) -> bool:
        active = cls.get_active_theme_path()
        return bool(active and "msm-" in os.path.basename(active))
