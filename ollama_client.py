"""
MAXXX OS - Ollama Client
Local LLM integration via Ollama API
All calls go to localhost:11434 - zero cloud dependency
"""

import json
import requests
from typing import Optional, Generator
from dataclasses import dataclass


OLLAMA_BASE_URL = "http://localhost:11434"


@dataclass
class OllamaResponse:
    model: str
    response: str
    done: bool
    total_duration: Optional[int] = None


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
        self.primary_model = "qwen2.5:7b"
        self.fallback_model = "hermes3:8b"

    def is_available(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.ConnectionError:
            return False

    def list_models(self) -> list:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
        return []

    def generate(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> OllamaResponse:
        if model is None:
            model = self.primary_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if system:
            payload["system"] = system

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            if resp.status_code == 200:
                data = resp.json()
                return OllamaResponse(
                    model=model,
                    response=data.get("response", ""),
                    done=data.get("done", False),
                    total_duration=data.get("total_duration")
                )
            else:
                if model != self.fallback_model:
                    return self.generate(
                        prompt=prompt,
                        model=self.fallback_model,
                        system=system,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                return OllamaResponse(
                    model=model,
                    response="",
                    done=False
                )
        except requests.ConnectionError:
            return OllamaResponse(
                model=model,
                response="",
                done=False
            )

    def generate_stream(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> Generator[str, None, None]:
        if model is None:
            model = self.primary_model

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        if system:
            payload["system"] = system

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=120
            )
            for line in resp.iter_lines():
                if line:
                    data = json.loads(line)
                    yield data.get("response", "")
                    if data.get("done"):
                        break
        except Exception:
            yield ""

    def classify_intent(self, user_input: str) -> dict:
        system_prompt = """You are a content classifier. Classify the user's input into:
- division: tech, media, mafia, or saas
- intent: create_post, update_profile, engage_community, or other
- platform_suggestion: suggest the best primary platform

Respond ONLY with valid JSON like:
{"division": "tech", "intent": "create_post", "platform_suggestion": "x"}"""

        response = self.generate(
            prompt=user_input,
            system=system_prompt,
            temperature=0.1
        )

        try:
            return json.loads(response.response)
        except (json.JSONDecodeError, AttributeError):
            return {
                "division": "tech",
                "intent": "create_post",
                "platform_suggestion": "x"
            }


ollama = OllamaClient()
