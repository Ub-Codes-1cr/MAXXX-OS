"""
MAXXX OS - Agent Tools
Tools that the Hermes agent can use to perform tasks
"""

import json
from typing import Any, Callable
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    success: bool
    output: str
    data: Any = None


class ToolRegistry:
    def __init__(self):
        self.tools: dict[str, dict] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("draft_post", "Generate a post for a specific platform", self._draft_post)
        self.register("validate_post", "Validate a post against golden lint rules", self._validate_post)
        self.register("post_to_platform", "Stage a post on a platform using browser", self._post_to_platform)
        self.register("copy_to_clipboard", "Copy text to clipboard as fallback", self._copy_to_clipboard)
        self.register("check_ollama", "Check if Ollama is running", self._check_ollama)
        self.register("get_platform_rules", "Get posting rules for a platform", self._get_platform_rules)
        self.register("list_platforms", "List all supported platforms", self._list_platforms)
        self.register("get_brand_voice", "Get brand voice guidelines", self._get_brand_voice)

    def register(self, name: str, description: str, func: Callable):
        self.tools[name] = {
            "name": name,
            "description": description,
            "func": func
        }

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        if tool_name not in self.tools:
            return ToolResult(success=False, output=f"Unknown tool: {tool_name}")
        
        try:
            # Filter to only accepted params
            import inspect
            func = self.tools[tool_name]["func"]
            sig = inspect.signature(func)
            valid_params = set(sig.parameters.keys())
            
            # Also accept 'self' param variants
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
            
            result = func(**filtered_kwargs)
            return result
        except Exception as e:
            return ToolResult(success=False, output=f"Error: {str(e)}")

    def get_tool_descriptions(self) -> str:
        lines = []
        for name, tool in self.tools.items():
            lines.append(f"- {name}: {tool['description']}")
        return "\n".join(lines)

    # Platform name aliases
    PLATFORM_ALIASES = {
        "twitter": "x",
        "twitter.com": "x",
        "x.com": "x",
        "linkedin.com": "linkedin",
        "github.com": "github",
        "reddit.com": "reddit",
        "instagram.com": "instagram",
        "youtube.com": "youtube",
        "dev.to": "devto",
        "hashnode.com": "hashnode",
        "threads.net": "threads",
        "facebook.com": "facebook",
        "substack.com": "substack",
        "telegram.org": "telegram",
        "discord.com": "discord",
        "producthunt.com": "producthunt",
        "quora.com": "quora",
        "peerlist.io": "peerlist",
        "leetcode.com": "leetcode",
        "bsky.app": "bluesky",
    }

    def _normalize_platform(self, platform: str) -> str:
        return self.PLATFORM_ALIASES.get(platform.lower(), platform.lower())

    def _clean_text(self, text: str) -> str:
        # Remove "Tool result: " prefix if present
        if text.startswith("Tool result: "):
            text = text[len("Tool result: "):]
        return text.strip()

    def _draft_post(self, platform: str = "x", content_idea: str = "", topic: str = "", idea: str = "") -> ToolResult:
        from draft_generator import draft_generator
        from brain import brain
        
        # Accept multiple parameter names
        idea_text = content_idea or topic or idea
        if not idea_text:
            return ToolResult(success=False, output="No content idea provided")
        
        # Normalize platform name
        platform_normalized = self._normalize_platform(platform)
        
        # Get brand voice
        brand_voice = brain.get_brand_voice()
        
        result = draft_generator.generate_draft(
            content_idea=idea_text,
            platform=platform_normalized,
            brand_voice_override=brand_voice
        )
        
        if result.success:
            # Return the ACTUAL draft text, not a summary
            return ToolResult(
                success=True,
                output=result.draft,
                data={"draft": result.draft, "platform": platform_normalized, "errors": result.errors}
            )
        else:
            return ToolResult(
                success=False,
                output=f"Failed to generate draft: {result.errors}",
                data={"errors": result.errors}
            )

    def _validate_post(self, platform: str = "x", draft: str = "", post: str = "", content: str = "", text: str = "") -> ToolResult:
        from golden_lint import validate_draft
        
        # Accept multiple parameter names and clean text
        draft_text = self._clean_text(draft or post or content or text)
        if not draft_text:
            return ToolResult(success=False, output="No draft content provided")
        
        # Normalize platform name
        platform_normalized = self._normalize_platform(platform)
        
        result = validate_draft(platform_normalized, draft_text)
        
        # Handle LintResult object (dataclass) or dict
        if hasattr(result, 'passed'):
            # It's a LintResult dataclass
            if result.passed:
                return ToolResult(
                    success=True,
                    output=f"VALID - Post passes all rules for {platform}",
                    data={"passed": True, "errors": result.errors if hasattr(result, 'errors') else []}
                )
            else:
                errors = result.errors if hasattr(result, 'errors') else []
                return ToolResult(
                    success=False,
                    output=f"INVALID - Errors: {'; '.join(errors)}",
                    data={"passed": False, "errors": errors}
                )
        elif isinstance(result, dict):
            # It's a dict
            if result.get("passed"):
                return ToolResult(
                    success=True,
                    output=f"VALID - Post passes all rules for {platform}",
                    data=result
                )
            else:
                errors = result.get("errors", [])
                return ToolResult(
                    success=False,
                    output=f"INVALID - Errors: {'; '.join(errors)}",
                    data=result
                )
        else:
            return ToolResult(
                success=False,
                output=f"Unexpected validation result type: {type(result)}"
            )

    def _post_to_platform(self, platform: str = "x", draft: str = "", post: str = "", content: str = "", text: str = "") -> ToolResult:
        from playwright_engine import PlatformExecutor, clipboard_fallback
        
        # Accept multiple parameter names and clean text
        draft_text = self._clean_text(draft or post or content or text)
        if not draft_text:
            return ToolResult(success=False, output="No draft content provided")
        
        # Normalize platform name
        platform_normalized = self._normalize_platform(platform)
        
        try:
            executor = PlatformExecutor(headless=False)
            if not executor.launch():
                # Fallback to clipboard
                clipboard_fallback(platform_normalized, draft_text)
                return ToolResult(
                    success=True,
                    output=f"Browser failed. Draft copied to clipboard. Paste manually on {platform}.",
                    data={"fallback": "clipboard", "draft": draft_text}
                )
            
            result = executor.stage_post(platform_normalized, draft_text)
            executor.close()
            
            if result.success:
                return ToolResult(
                    success=True,
                    output=f"Post staged on {platform}. Click Post button manually.",
                    data={"staged": True, "platform": platform_normalized, "draft": draft_text}
                )
            else:
                # Fallback to clipboard
                clipboard_fallback(platform_normalized, draft_text)
                return ToolResult(
                    success=True,
                    output=f"Browser posting failed. Draft copied to clipboard. Paste manually on {platform}.",
                    data={"fallback": "clipboard", "draft": draft_text}
                )
        except Exception as e:
            clipboard_fallback(platform_normalized, draft_text)
            return ToolResult(
                success=True,
                output=f"Error: {str(e)}. Draft copied to clipboard. Paste manually on {platform}.",
                data={"fallback": "clipboard", "error": str(e), "draft": draft_text}
            )

    def _copy_to_clipboard(self, text: str = "", content: str = "", draft: str = "") -> ToolResult:
        from playwright_engine import clipboard_fallback
        
        # Accept multiple parameter names
        text_content = text or content or draft
        if not text_content:
            return ToolResult(success=False, output="No text provided")
        
        result = clipboard_fallback("generic", text_content)
        
        if result.success:
            return ToolResult(
                success=True,
                output="Text copied to clipboard successfully",
                data={"text": text_content}
            )
        else:
            return ToolResult(
                success=False,
                output="Failed to copy to clipboard"
            )

    def _check_ollama(self) -> ToolResult:
        from ollama_client import ollama
        
        if ollama.is_available():
            models = ollama.list_models()
            return ToolResult(
                success=True,
                output=f"Ollama is running. Available models: {', '.join(models)}",
                data={"models": models}
            )
        else:
            return ToolResult(
                success=False,
                output="Ollama is not running. Please start Ollama first."
            )

    def _get_platform_rules(self, platform: str = "x") -> ToolResult:
        from vault_reader import vault
        from golden_lint import PLATFORM_RULES
        
        # Normalize platform name
        platform_normalized = self._normalize_platform(platform)
        
        # Try to get rules from golden_lint first (simpler format)
        if platform_normalized in PLATFORM_RULES:
            rules = PLATFORM_RULES[platform_normalized]
            return ToolResult(
                success=True,
                output=f"Rules for {platform}:\n{rules}",
                data={"platform": platform_normalized, "rules": rules}
            )
        
        # Fallback to vault
        rules = vault.get_platform_rules(platform_normalized)
        
        if rules:
            # Convert to string if needed
            if hasattr(rules, 'raw_content'):
                rules_str = rules.raw_content
            elif hasattr(rules, '__str__'):
                rules_str = str(rules)
            else:
                rules_str = str(rules)
            
            return ToolResult(
                success=True,
                output=f"Rules for {platform}:\n{rules_str[:500]}",
                data={"platform": platform_normalized, "rules": rules_str}
            )
        else:
            return ToolResult(
                success=False,
                output=f"No rules found for {platform}. Use: x, linkedin, github, devto, reddit, instagram, youtube"
            )

    def _list_platforms(self) -> ToolResult:
        from golden_lint import list_platforms
        
        platforms = list_platforms()
        
        return ToolResult(
            success=True,
            output=f"Supported platforms: {', '.join(platforms)}",
            data={"platforms": platforms}
        )

    def _get_brand_voice(self) -> ToolResult:
        from brain import brain
        
        voice = brain.get_brand_voice()
        
        if voice:
            return ToolResult(
                success=True,
                output=f"Brand voice:\n{voice[:500]}...",
                data={"voice": voice}
            )
        else:
            return ToolResult(
                success=False,
                output="No brand voice found"
            )


# Global instance
tool_registry = ToolRegistry()
