"""
MAXXX OS - Structured Logging System
Tracks all operations for debugging and analytics
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum


LOG_DIR = Path(__file__).parent / "logs"


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    SYSTEM = "system"
    BRAIN = "brain"
    DRAFT = "draft"
    LINT = "lint"
    VOICE = "voice"
    BROWSER = "browser"
    ANALYTICS = "analytics"
    SCHEDULER = "scheduler"
    USER = "user"


class MAXXXLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._setup_logger()
            self._event_log = []

    def _setup_logger(self):
        LOG_DIR.mkdir(exist_ok=True)
        self.logger = logging.getLogger("maxxx_os")
        self.logger.setLevel(logging.DEBUG)

        today = datetime.now().strftime("%Y-%m-%d")
        log_file = LOG_DIR / f"maxxx_{today}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _log_event(self, level: str, category: LogCategory, message: str, data: dict = None):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "category": category.value,
            "message": message,
            "data": data
        }
        self._event_log.append(entry)

        if len(self._event_log) > 1000:
            self._persist_events()
            self._event_log = []

        log_msg = f"[{category.value.upper()}] {message}"
        if data:
            log_msg += f" | {json.dumps(data)}"

        if level == "DEBUG":
            self.logger.debug(log_msg)
        elif level == "INFO":
            self.logger.info(log_msg)
        elif level == "WARNING":
            self.logger.warning(log_msg)
        elif level == "ERROR":
            self.logger.error(log_msg)
        elif level == "CRITICAL":
            self.logger.critical(log_msg)

    def _persist_events(self):
        if not self._event_log:
            return
        today = datetime.now().strftime("%Y-%m-%d")
        events_file = LOG_DIR / f"events_{today}.jsonl"
        with open(events_file, "a", encoding="utf-8") as f:
            for event in self._event_log:
                f.write(json.dumps(event) + "\n")
        self._event_log = []

    def debug(self, category: LogCategory, message: str, data: dict = None):
        self._log_event("DEBUG", category, message, data)

    def info(self, category: LogCategory, message: str, data: dict = None):
        self._log_event("INFO", category, message, data)

    def warning(self, category: LogCategory, message: str, data: dict = None):
        self._log_event("WARNING", category, message, data)

    def error(self, category: LogCategory, message: str, data: dict = None):
        self._log_event("ERROR", category, message, data)

    def critical(self, category: LogCategory, message: str, data: dict = None):
        self._log_event("CRITICAL", category, message, data)

    def log_brain_action(self, action: str, data: dict = None):
        self.info(LogCategory.BRAIN, action, data)

    def log_draft_event(self, event: str, platform: str, data: dict = None):
        draft_data = {"platform": platform}
        if data:
            draft_data.update(data)
        self.info(LogCategory.DRAFT, event, draft_data)

    def log_lint_result(self, platform: str, passed: bool, errors: list = None):
        self.info(LogCategory.LINT, "Validation complete", {
            "platform": platform,
            "passed": passed,
            "errors": errors or []
        })

    def log_browser_action(self, action: str, platform: str, data: dict = None):
        browser_data = {"platform": platform}
        if data:
            browser_data.update(data)
        self.info(LogCategory.BROWSER, action, browser_data)

    def log_voice_event(self, event: str, data: dict = None):
        self.info(LogCategory.VOICE, event, data)

    def log_user_action(self, action: str, data: dict = None):
        self.info(LogCategory.USER, action, data)

    def get_recent_logs(self, count: int = 50) -> list:
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = LOG_DIR / f"events_{today}.jsonl"
        if not log_file.exists():
            return []
        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        events = []
        for line in lines[-count:]:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return events

    def get_logs_by_category(self, category: LogCategory, count: int = 50) -> list:
        all_logs = self.get_recent_logs(count * 2)
        filtered = [log for log in all_logs if log.get("category") == category.value]
        return filtered[-count:]

    def flush(self):
        self._persist_events()


logger = MAXXXLogger()
