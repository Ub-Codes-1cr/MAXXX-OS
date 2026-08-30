"""
MAXXX OS - Draft Generator
Content generation pipeline using local LLMs
Transforms ideas into platform-specific drafts
"""

from typing import Optional
from dataclasses import dataclass

from ollama_client import ollama
from vault_reader import vault
from golden_lint import validate_draft, PLATFORM_RULES


@dataclass
class DraftResult:
    success: bool
    platform: str
    draft: str
    errors: list = None
    warnings: list = None
    revision_count: int = 0

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


PLATFORM_SYSTEM_PROMPTS = {
    "x": """You are an expert X (Twitter) content creator.

CRITICAL RULES - VIOLATION WILL REJECT YOUR OUTPUT:
- EXACTLY 280 characters maximum. Count carefully.
- Start with a contrarian hook or strong data point
- NO raw URLs in the first tweet
- NO hashtags in the main tweet (optional: 1-2 max)
- NO banned words: game-changer, synergy, disrupt, leverage, paradigm shift, unlock, elevate, transformative, innovative, cutting-edge, seamless, holistic, ecosystem, ROI, best-in-class, world-class, next-generation, revolutionary

FORMAT: Single paragraph, 1-2 sentences. Punchy. Data-driven.

Example of GOOD tweet (under 280 chars):
"I tracked 40 days of building in public. 20 platforms. Zero APIs. Here's what actually worked vs what didn't." """,

    "linkedin": """You are a professional LinkedIn content strategist.
Rules:
- 800-1,200 characters optimal
- Must contain at least 3 double-spaced line breaks
- Start with a hook (first 2 lines visible before "see more")
- End with a question to drive engagement
- Professional but authentic tone""",

    "github": """You are a technical documentation expert.
Rules:
- Must be valid Markdown with proper headings
- All code snippets must be wrapped in ``` blocks
- README must include Installation and Usage sections
- Clear, concise, developer-focused""",

    "devto": """You are a Dev.to content creator.
Rules:
- Must contain at least one H2 (##) and one H3 (###) heading
- Must include at least one code block if technical
- Use series tags for multi-part posts
- Developer-friendly, educational tone""",

    "reddit": """You are a Reddit community contributor.
Rules:
- Zero blatant self-promotion in first 2 sentences
- Title must not use clickbait
- Provide standalone value
- Be helpful, not promotional""",

    "producthunt": """You are a ProductHunt launch expert.
Rules:
- Pitch must be under 100 words
- Must include Maker's note perspective
- Must ask for specific feedback
- Be authentic and transparent""",

    "instagram": """You are an Instagram content creator.
Rules:
- Caption must end with 5-10 relevant hashtags
- First line must be a punchy hook under 50 characters
- Visual-first thinking
- Engaging, conversational tone""",
}

DEFAULT_SYSTEM_PROMPT = """You are a versatile content creator.
Adapt your style to the target platform.
Follow all platform-specific rules.
Be authentic, valuable, and engaging.
Never use buzzwords like: game-changer, synergy, disrupt, leverage, paradigm shift."""


class DraftGenerator:
    def __init__(self):
        self.max_revisions = 3

    def _build_generation_prompt(
        self,
        content_idea: str,
        platform: str,
        brand_voice: str,
        platform_rules: str
    ) -> str:
        return f"""Create a {platform} post based on this idea:

IDEA:
{content_idea}

BRAND VOICE:
{brand_voice}

PLATFORM RULES:
{platform_rules}

Generate the content now. Follow all rules strictly."""

    def _build_revision_prompt(
        self,
        current_draft: str,
        errors: list,
        platform: str
    ) -> str:
        error_text = "\n".join([f"- {e}" for e in errors])
        char_limit = PLATFORM_RULES.get(platform, {}).get("max_chars", 280)

        return f"""The following draft has validation errors. Fix them by rewriting:

CURRENT DRAFT ({len(current_draft)} chars, max allowed: {char_limit}):
{current_draft}

ERRORS TO FIX:
{error_text}

REVISION RULES:
1. Reduce content to fit within {char_limit} characters
2. Remove ALL banned words (game-changer, synergy, disrupt, leverage, ROI, etc.)
3. Maintain the core message but be more concise
4. For X/Twitter: Use ONE punchy sentence only

Output ONLY the corrected draft text, no quotes, no explanations."""

    def generate_draft(
        self,
        content_idea: str,
        platform: str,
        brand_voice_override: str = None
    ) -> DraftResult:
        platform = platform.lower().strip()

        if platform not in PLATFORM_RULES:
            return DraftResult(
                success=False,
                platform=platform,
                draft="",
                errors=[f"Unknown platform: {platform}"]
            )

        brand_voice = brand_voice_override or vault.get_brand_voice().raw_content
        platform_rules = vault.get_platform_rules(platform).raw_content
        system_prompt = PLATFORM_SYSTEM_PROMPTS.get(platform, DEFAULT_SYSTEM_PROMPT)

        prompt = self._build_generation_prompt(
            content_idea, platform, brand_voice, platform_rules
        )

        response = ollama.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.3,
            max_tokens=2000
        )

        if not response.done or not response.response:
            return DraftResult(
                success=False,
                platform=platform,
                draft="",
                errors=["LLM generation failed. Is Ollama running?"]
            )

        draft = response.response.strip()
        lint_result = validate_draft(platform, draft)

        revision_count = 0
        while not lint_result.passed and revision_count < self.max_revisions:
            revision_count += 1
            revision_prompt = self._build_revision_prompt(
                draft, lint_result.errors, platform
            )
            revision_response = ollama.generate(
                prompt=revision_prompt,
                system=system_prompt,
                temperature=0.2,
                max_tokens=2000
            )
            if revision_response.done and revision_response.response:
                draft = revision_response.response.strip()
                lint_result = validate_draft(platform, draft)

        return DraftResult(
            success=lint_result.passed,
            platform=platform,
            draft=draft,
            errors=lint_result.errors,
            warnings=lint_result.warnings,
            revision_count=revision_count
        )

    def generate_multi_platform(
        self,
        content_idea: str,
        platforms: list,
        brand_voice_override: str = None
    ) -> dict:
        results = {}
        for platform in platforms:
            results[platform] = self.generate_draft(
                content_idea, platform, brand_voice_override
            )
        return results

    def rewrite_for_platform(
        self,
        existing_draft: str,
        target_platform: str
    ) -> DraftResult:
        system_prompt = PLATFORM_SYSTEM_PROMPTS.get(target_platform, DEFAULT_SYSTEM_PROMPT)
        platform_rules = vault.get_platform_rules(target_platform).raw_content

        prompt = f"""Rewrite this content for {target_platform}:

ORIGINAL CONTENT:
{existing_draft}

PLATFORM RULES:
{platform_rules}

Rewrite the content to perfectly fit {target_platform}. Output ONLY the rewritten content."""

        response = ollama.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=0.3,
            max_tokens=2000
        )

        if not response.done or not response.response:
            return DraftResult(
                success=False,
                platform=target_platform,
                draft="",
                errors=["LLM rewrite failed"]
            )

        draft = response.response.strip()
        lint_result = validate_draft(target_platform, draft)

        return DraftResult(
            success=lint_result.passed,
            platform=target_platform,
            draft=draft,
            errors=lint_result.errors,
            warnings=lint_result.warnings
        )


draft_generator = DraftGenerator()
