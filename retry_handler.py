"""
MAXXX OS - Retry Handler
Error recovery, fallback strategies, and resilience patterns
"""

import time
import random
from datetime import datetime
from pathlib import Path
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import traceback


ERROR_LOG_DIR = Path(__file__).parent / "logs" / "errors"


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    RETRY = "retry"
    RETRY_WITH_BACKOFF = "retry_with_backoff"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    CLIPBOARD_FALLBACK = "clipboard_fallback"


@dataclass
class ErrorContext:
    error: Exception
    timestamp: str
    component: str
    operation: str
    severity: ErrorSeverity
    recovery_strategy: RecoveryStrategy
    retry_count: int = 0
    max_retries: int = 3
    last_attempt: str = ""
    error_message: str = ""
    stack_trace: str = ""

    def __post_init__(self):
        self.timestamp = datetime.now().isoformat()
        self.error_message = str(self.error)
        self.stack_trace = traceback.format_exc()


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True


class RetryHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            ERROR_LOG_DIR.mkdir(exist_ok=True)
            self._error_history = []
            self._retry_configs = {}

    def _log_error(self, context: ErrorContext):
        self._error_history.append(context)
        if len(self._error_history) > 100:
            self._persist_errors()
            self._error_history = []

        error_file = ERROR_LOG_DIR / f"errors_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        error_data = {
            "timestamp": context.timestamp,
            "component": context.component,
            "operation": context.operation,
            "severity": context.severity.value,
            "error": context.error_message,
            "retry_count": context.retry_count,
            "recovery_strategy": context.recovery_strategy.value
        }
        with open(error_file, "a", encoding="utf-8") as f:
            import json
            f.write(json.dumps(error_data) + "\n")

    def _persist_errors(self):
        import json
        error_file = ERROR_LOG_DIR / f"errors_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(error_file, "a", encoding="utf-8") as f:
            for ctx in self._error_history:
                error_data = {
                    "timestamp": ctx.timestamp,
                    "component": ctx.component,
                    "operation": ctx.operation,
                    "severity": ctx.severity.value,
                    "error": ctx.error_message,
                    "retry_count": ctx.retry_count
                }
                f.write(json.dumps(error_data) + "\n")

    def _calculate_delay(self, retry_count: int, config: RetryConfig) -> float:
        delay = config.base_delay * (config.exponential_base ** retry_count)
        delay = min(delay, config.max_delay)
        if config.jitter:
            delay = delay * (0.5 + random.random())
        return delay

    def _classify_error(self, error: Exception) -> tuple:
        error_type = type(error).__name__
        error_msg = str(error).lower()

        if "connection" in error_msg or "timeout" in error_msg:
            return ErrorSeverity.MEDIUM, RecoveryStrategy.RETRY_WITH_BACKOFF
        elif "rate limit" in error_msg or "429" in error_msg:
            return ErrorSeverity.MEDIUM, RecoveryStrategy.RETRY_WITH_BACKOFF
        elif "not found" in error_msg or "404" in error_msg:
            return ErrorSeverity.LOW, RecoveryStrategy.SKIP
        elif "permission" in error_msg or "403" in error_msg:
            return ErrorSeverity.HIGH, RecoveryStrategy.ABORT
        elif "invalid" in error_msg or "validation" in error_msg:
            return ErrorSeverity.LOW, RecoveryStrategy.SKIP
        elif "browser" in error_msg or "playwright" in error_msg:
            return ErrorSeverity.MEDIUM, RecoveryStrategy.CLIPBOARD_FALLBACK
        elif "ollama" in error_msg or "llm" in error_msg:
            return ErrorSeverity.HIGH, RecoveryStrategy.RETRY
        else:
            return ErrorSeverity.MEDIUM, RecoveryStrategy.RETRY

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        component: str = "unknown",
        operation: str = "unknown",
        config: RetryConfig = None,
        fallback: Callable = None,
        **kwargs
    ) -> Any:
        if config is None:
            config = RetryConfig()

        last_error = None
        for attempt in range(config.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                severity, strategy = self._classify_error(e)

                context = ErrorContext(
                    error=e,
                    component=component,
                    operation=operation,
                    severity=severity,
                    recovery_strategy=strategy,
                    retry_count=attempt,
                    max_retries=config.max_retries
                )
                self._log_error(context)

                if attempt < config.max_retries:
                    if strategy == RecoveryStrategy.RETRY:
                        delay = self._calculate_delay(attempt, config)
                        time.sleep(delay)
                    elif strategy == RecoveryStrategy.RETRY_WITH_BACKOFF:
                        delay = self._calculate_delay(attempt, config) * 2
                        time.sleep(delay)
                    elif strategy == RecoveryStrategy.SKIP:
                        return None
                    elif strategy == RecoveryStrategy.ABORT:
                        raise
                    elif strategy == RecoveryStrategy.CLIPBOARD_FALLBACK:
                        if fallback:
                            return fallback(*args, **kwargs)
                        return None
                else:
                    if fallback:
                        return fallback(*args, **kwargs)
                    raise

        raise last_error

    def get_browser_fallback(self, platform: str, content: str) -> Callable:
        def fallback(*args, **kwargs):
            import subprocess
            try:
                process = subprocess.Popen(
                    ["clip"],
                    stdin=subprocess.PIPE,
                    shell=True
                )
                process.communicate(input=content.encode("utf-16le"))
                return {
                    "success": True,
                    "method": "clipboard",
                    "message": f"Draft copied to clipboard for {platform}. Paste manually."
                }
            except Exception as e:
                return {
                    "success": False,
                    "method": "clipboard",
                    "message": f"Clipboard fallback failed: {str(e)}"
                }
        return fallback

    def get_llm_fallback(self, prompt: str, system: str = None) -> Callable:
        def fallback(*args, **kwargs):
            return {
                "success": False,
                "response": "",
                "message": "LLM unavailable. Please try again later."
            }
        return fallback

    def get_error_history(self, count: int = 50) -> list:
        import json
        error_file = ERROR_LOG_DIR / f"errors_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        if not error_file.exists():
            return []

        lines = error_file.read_text(encoding="utf-8").strip().split("\n")
        errors = []
        for line in lines[-count:]:
            try:
                errors.append(json.loads(line))
            except json.JSONDecodeError:
                pass
        return errors

    def get_error_stats(self) -> dict:
        import json
        error_file = ERROR_LOG_DIR / f"errors_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        if not error_file.exists():
            return {"total": 0, "by_severity": {}, "by_component": {}}

        lines = error_file.read_text(encoding="utf-8").strip().split("\n")
        stats = {"total": 0, "by_severity": {}, "by_component": {}}

        for line in lines:
            if not line:
                continue
            try:
                data = json.loads(line)
                stats["total"] += 1
                severity = data.get("severity", "unknown")
                component = data.get("component", "unknown")
                stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
                stats["by_component"][component] = stats["by_component"].get(component, 0) + 1
            except json.JSONDecodeError:
                continue

        return stats

    def clear_old_errors(self, days: int = 7):
        cutoff = datetime.now().timestamp() - (days * 86400)
        for error_file in ERROR_LOG_DIR.glob("errors_*.jsonl"):
            try:
                date_str = error_file.stem.replace("errors_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d").timestamp()
                if file_date < cutoff:
                    error_file.unlink()
            except (ValueError, OSError):
                pass


retry_handler = RetryHandler()
