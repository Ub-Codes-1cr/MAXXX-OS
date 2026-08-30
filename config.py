"""
MAXXX OS - Configuration Management
Centralized config for all components
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


CONFIG_DIR = Path(__file__).parent / "config"
VAULT_DIR = Path(__file__).parent / "vault"


@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    primary_model: str = "qwen2.5:7b"
    fallback_model: str = "hermes3:8b"
    temperature: float = 0.3
    max_tokens: int = 2000
    timeout: int = 120


@dataclass
class VoiceConfig:
    whisper_model: str = "base"
    tts_voice: str = "en-US-GuyNeural"
    tts_rate: str = "+0%"
    sample_rate: int = 16000
    max_duration: int = 60


@dataclass
class BrowserConfig:
    headless: bool = False
    profile_directory: str = "Default"
    typing_delay: int = 50
    page_load_timeout: int = 30000
    human_like: bool = True


@dataclass
class LintConfig:
    max_revisions: int = 3
    strict_mode: bool = True
    banned_words: list = field(default_factory=lambda: [
        "game-changer", "synergy", "disrupt", "leverage", "paradigm shift",
        "unlock", "elevate", "transformative", "innovative", "cutting-edge",
        "seamless", "holistic", "ecosystem", "roi", "best-in-class",
        "world-class", "next-generation", "revolutionary", "game-changing",
        "deep dive", "thought leadership", "move the needle", "low-hanging fruit",
        "circle back", "bandwidth", "thought leader", "passionate about",
        "think outside the box", "value-add", "pillars", "synergize"
    ])


@dataclass
class SchedulerConfig:
    enabled: bool = False
    check_interval_minutes: int = 5
    max_posts_per_day: int = 20
    blackout_hours: list = field(default_factory=lambda: [0, 1, 2, 3, 4, 5])


@dataclass
class AnalyticsConfig:
    enabled: bool = True
    track_engagement: bool = True
    daily_digest: bool = True
    retention_days: int = 90


@dataclass
class AppConfig:
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    voice: VoiceConfig = field(default_factory=VoiceConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    lint: LintConfig = field(default_factory=LintConfig)
    scheduler: SchedulerConfig = field(default_factory=SchedulerConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    vault_path: str = str(VAULT_DIR)
    log_level: str = "INFO"
    debug: bool = False


class ConfigManager:
    _instance = None
    _config: Optional[AppConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = AppConfig()
            self._load_config()

    def _load_config(self):
        config_file = CONFIG_DIR / "config.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                self._update_from_dict(data)
            except Exception:
                pass

    def _update_from_dict(self, data: dict):
        if "ollama" in data:
            for k, v in data["ollama"].items():
                if hasattr(self._config.ollama, k):
                    setattr(self._config.ollama, k, v)
        if "voice" in data:
            for k, v in data["voice"].items():
                if hasattr(self._config.voice, k):
                    setattr(self._config.voice, k, v)
        if "browser" in data:
            for k, v in data["browser"].items():
                if hasattr(self._config.browser, k):
                    setattr(self._config.browser, k, v)
        if "lint" in data:
            for k, v in data["lint"].items():
                if hasattr(self._config.lint, k):
                    setattr(self._config.lint, k, v)
        if "scheduler" in data:
            for k, v in data["scheduler"].items():
                if hasattr(self._config.scheduler, k):
                    setattr(self._config.scheduler, k, v)
        if "analytics" in data:
            for k, v in data["analytics"].items():
                if hasattr(self._config.analytics, k):
                    setattr(self._config.analytics, k, v)

    def get(self) -> AppConfig:
        return self._config

    def save(self):
        CONFIG_DIR.mkdir(exist_ok=True)
        config_file = CONFIG_DIR / "config.json"
        data = {
            "ollama": {
                "base_url": self._config.ollama.base_url,
                "primary_model": self._config.ollama.primary_model,
                "fallback_model": self._config.ollama.fallback_model,
                "temperature": self._config.ollama.temperature,
                "max_tokens": self._config.ollama.max_tokens,
            },
            "voice": {
                "whisper_model": self._config.voice.whisper_model,
                "tts_voice": self._config.voice.tts_voice,
                "tts_rate": self._config.voice.tts_rate,
            },
            "browser": {
                "headless": self._config.browser.headless,
                "profile_directory": self._config.browser.profile_directory,
                "typing_delay": self._config.browser.typing_delay,
                "human_like": self._config.browser.human_like,
            },
            "lint": {
                "max_revisions": self._config.lint.max_revisions,
                "strict_mode": self._config.lint.strict_mode,
            },
            "scheduler": {
                "enabled": self._config.scheduler.enabled,
                "max_posts_per_day": self._config.scheduler.max_posts_per_day,
            },
            "analytics": {
                "enabled": self._config.analytics.enabled,
                "track_engagement": self._config.analytics.track_engagement,
            },
        }
        with open(config_file, "w") as f:
            json.dump(data, f, indent=2)

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        self.save()


config_manager = ConfigManager()
config = config_manager.get()
