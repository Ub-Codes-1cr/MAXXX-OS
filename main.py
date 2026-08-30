"""
MAXXX OS - Main Entry Point
Streamlit UI with Maskyy Orb Visualizer
Local-First AI Orchestration Agent
"""

import os
import sys
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional

import streamlit as st

from golden_lint import validate_draft, PLATFORM_RULES, list_platforms
from voice_pipeline import VoicePipeline
from playwright_engine import PlatformExecutor, clipboard_fallback
from brain import brain, TaskState
from vault_reader import vault
from ollama_client import ollama
from draft_generator import draft_generator
from config import config_manager, config
from logger import logger, LogCategory
from memory import memory, MemoryType
from scheduler import scheduler, ScheduleStatus
from analytics import analytics
from media_handler import media_handler
from retry_handler import retry_handler, RetryConfig


st.set_page_config(
    page_title="MAXXX OS",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Global Background & Text */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #333333;
    }
    
    /* Headers - Monospace Brutalist */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
        letter-spacing: -1px !important;
    }
    
    /* Buttons - Stark White */
    .stButton>button {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 0px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        font-family: 'Courier New', monospace !important;
    }
    .stButton>button:hover {
        background-color: #cccccc !important;
    }
    
    /* Text Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #111111 !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 0px !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Select boxes */
    .stSelectbox>div>div>div {
        background-color: #111111 !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 0px !important;
    }
    
    /* Radio buttons */
    .stRadio>div {
        color: #ffffff !important;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background-color: #111111 !important;
        border: 1px solid #333333 !important;
        border-radius: 0px !important;
        padding: 10px !important;
    }
    [data-testid="stMetric"] label {
        color: #888888 !important;
        font-family: 'Courier New', monospace !important;
    }
    [data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #111111 !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 0px !important;
        font-family: 'Courier New', monospace !important;
    }
    
    /* Status Orb - Grayscale */
    .orb {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #ffffff, #888888, #333333);
        box-shadow: 0 0 40px rgba(255, 255, 255, 0.3);
        animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { transform: scale(1); box-shadow: 0 0 40px rgba(255, 255, 255, 0.3); }
        50% { transform: scale(1.05); box-shadow: 0 0 60px rgba(255, 255, 255, 0.5); }
    }
    
    /* Dividers */
    hr {
        border-color: #333333 !important;
    }
    
    /* Code blocks */
    code {
        background-color: #111111 !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
    }
    
    /* Success/Warning/Error messages */
    .stAlert {
        border-radius: 0px !important;
        font-family: 'Courier New', monospace !important;
    }
</style>
""", unsafe_allow_html=True)


class MaxxxOS:
    def __init__(self):
        self.voice = None
        self.executor = None
        self._init_components()

    def _init_components(self):
        try:
            self.voice = VoicePipeline(model_size=config.voice.whisper_model)
        except Exception as e:
            logger.warning(LogCategory.SYSTEM, f"Voice pipeline not available: {e}")

        try:
            self.executor = PlatformExecutor(headless=config.browser.headless)
        except Exception as e:
            logger.warning(LogCategory.SYSTEM, f"Playwright not available: {e}")


def render_orb(status: str = "idle"):
    colors = {
        "idle": ("#6366f1", "#4f46e5"),
        "thinking": ("#fbbf24", "#f59e0b"),
        "drafting": ("#3b82f6", "#2563eb"),
        "linting": ("#f97316", "#ea580c"),
        "typing": ("#10b981", "#059669"),
        "ready": ("#22c55e", "#16a34a"),
        "error": ("#ef4444", "#dc2626"),
    }
    color1, color2 = colors.get(status, colors["idle"])

    st.markdown(f"""
    <div class="orb-container">
        <div class="orb" style="background: radial-gradient(circle at 30% 30%, {color1}, {color2});">
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    maxxx = MaxxxOS()

    st.sidebar.title("🚀 MAXXX OS")
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Local-First. Anti-API. 100% Privacy.**")

    ollama_status = "Connected" if ollama.is_available() else "Disconnected"
    st.sidebar.markdown(f"**Ollama:** {ollama_status}")

    scheduler_stats = scheduler.get_stats()
    st.sidebar.markdown(f"**Scheduled:** {scheduler_stats['pending']} pending")

    page = st.sidebar.radio(
        "Navigate",
        ["🏠 Dashboard", "🧠 Brain", "🎤 Voice Input", "✍️ Draft",
         "📋 Review & Post", "📅 Schedule", "📊 Analytics", "⚙️ Settings"]
    )

    if page == "🏠 Dashboard":
        render_dashboard(maxxx)
    elif page == "🧠 Brain":
        render_brain(maxxx)
    elif page == "🎤 Voice Input":
        render_voice_input(maxxx)
    elif page == "✍️ Draft":
        render_draft(maxxx)
    elif page == "📋 Review & Post":
        render_review(maxxx)
    elif page == "📅 Schedule":
        render_scheduler(maxxx)
    elif page == "📊 Analytics":
        render_analytics()
    elif page == "⚙️ Settings":
        render_settings()


def render_dashboard(maxxx: MaxxxOS):
    st.title("🚀 MAXXX OS Dashboard")
    st.markdown("---")

    status = brain.get_status()
    render_orb(status["state"])

    scheduler_stats = scheduler.get_stats()
    memory_stats = memory.get_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Platforms", "20", "active")
    with col2:
        st.metric("Ollama", "Connected" if ollama.is_available() else "Offline", "")
    with col3:
        st.metric("Brain State", status["state"].title(), "")
    with col4:
        st.metric("Scheduled", scheduler_stats.get("pending", 0), "pending")
    with col5:
        st.metric("Drafts", memory_stats.get("draft", 0), "total")

    st.markdown("---")
    st.subheader("Quick Actions")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🧠 Open Brain", use_container_width=True):
            st.session_state.page = "brain"
            st.rerun()
    with col2:
        if st.button("🎤 Voice Input", use_container_width=True):
            st.session_state.page = "voice"
            st.rerun()
    with col3:
        if st.button("✍️ Create Draft", use_container_width=True):
            st.session_state.page = "draft"
            st.rerun()
    with col4:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.page = "analytics"
            st.rerun()

    st.markdown("---")
    st.subheader("Platform Status")

    platforms = list_platforms()
    for i in range(0, len(platforms), 4):
        cols = st.columns(4)
        for j, col in enumerate(cols):
            if i + j < len(platforms):
                platform = platforms[i + j]
                with col:
                    st.markdown(f"""
                    <div style="padding: 10px; border-radius: 5px; background: #1a1a2e; margin: 5px 0;">
                        <strong>{platform.upper()}</strong><br>
                        <span style="color: #22c55e;">● Ready</span>
                    </div>
                    """, unsafe_allow_html=True)


def render_brain(maxxx: MaxxxOS):
    st.title("🧠 MAXXX OS Brain")
    st.markdown("---")

    status = brain.get_status()
    render_orb(status["state"])

    st.subheader("Autonomous Content Generation")
    st.markdown("Enter your content idea and let the Brain classify, draft, and validate across platforms.")

    col1, col2 = st.columns([2, 1])
    with col1:
        content_idea = st.text_area(
            "Content Idea",
            height=200,
            placeholder="Describe your content idea. The Brain will classify it and suggest the best platforms..."
        )

    with col2:
        st.markdown("### Brain Status")
        st.json({
            "state": status["state"],
            "division": status["division"],
            "platform": status["platform"],
            "error": status["error"]
        })

        st.markdown("### Auto-Classify")
        if st.button("🔍 Classify Idea", use_container_width=True):
            if content_idea:
                with st.spinner("Classifying..."):
                    render_orb("thinking")
                    logger.log_brain_action("Classifying input", {"input_length": len(content_idea)})
                    classification = brain.classify_input(content_idea)
                    st.success(f"Classified as: **{classification.get('division', 'unknown')}**")
                    st.info(f"Suggested platform: **{classification.get('platform_suggestion', 'x')}**")
                    render_orb("idle")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        platform_choice = st.selectbox(
            "Target Platform (or use auto-classify)",
            ["Auto"] + list_platforms(),
            index=0
        )

    with col2:
        generate_mode = st.radio(
            "Generation Mode",
            ["Single Platform", "Multi-Platform (Division)"],
            index=0
        )

    if st.button("🚀 Generate Draft", use_container_width=True):
        if not content_idea:
            st.error("Please enter a content idea")
            return

        if not ollama.is_available():
            st.error("Ollama is not running. Start it with `ollama serve`")
            return

        with st.spinner("Brain is thinking..."):
            render_orb("thinking")
            logger.log_brain_action("Generating draft", {"idea_length": len(content_idea)})

            if generate_mode == "Single Platform":
                platform = platform_choice if platform_choice != "Auto" else "x"

                def generate_func():
                    return brain.generate_draft(content_idea=content_idea, platform=platform)

                result = retry_handler.execute_with_retry(
                    generate_func,
                    component="brain",
                    operation="generate_draft"
                )

                if result and result.success:
                    render_orb("ready")
                    st.success("Draft generated and validated!")
                    st.session_state.draft = result.draft
                    st.session_state.platform = result.platform
                    st.text_area("Generated Draft", result.draft, height=300)

                    memory.store_draft(platform, result.draft, {"idea": content_idea})
                    logger.log_draft_event("Draft generated", platform, {"chars": len(result.draft)})
                else:
                    render_orb("error")
                    st.error("Draft failed validation")
                    if result and result.errors:
                        for error in result.errors:
                            st.error(f"- {error}")
            else:
                if platform_choice != "Auto":
                    platforms = [platform_choice]
                else:
                    platforms = None

                results = brain.generate_multi_platform(
                    content_idea=content_idea,
                    platforms=platforms
                )

                render_orb("ready")
                st.success(f"Generated {len(results)} drafts!")

                for platform, result in results.items():
                    with st.expander(f"{platform.upper()} - {'Passed' if result.success else 'Failed'}"):
                        st.text_area(f"Draft - {platform}", result.draft, height=200, key=f"draft_{platform}")
                        if not result.success:
                            for error in result.errors:
                                st.error(f"- {error}")

                        if st.button(f"Use this draft", key=f"use_{platform}"):
                            st.session_state.draft = result.draft
                            st.session_state.platform = platform
                            st.rerun()


def render_voice_input(maxxx: MaxxxOS):
    st.title("🎤 Voice Input")
    st.markdown("---")

    render_orb("thinking")

    st.markdown("""
    ### How it works:
    1. Click "Start Recording" and speak your content idea
    2. MAXXX OS transcribes your voice locally (no cloud)
    3. Edit the transcription if needed
    4. Proceed to draft generation
    """)

    col1, col2 = st.columns(2)
    with col1:
        duration = st.slider("Recording duration (seconds)", 5, 60, 10)
    with col2:
        st.markdown("**Status:** Ready to record")

    if st.button("🔴 Start Recording", use_container_width=True):
        with st.spinner("Recording..."):
            try:
                from voice_pipeline import record_audio
                logger.log_voice_event("Recording started", {"duration": duration})
                audio_path = record_audio(duration=duration)
                st.success("Recording complete!")
                logger.log_voice_event("Recording completed", {"path": audio_path})

                if maxxx.voice:
                    with st.spinner("Transcribing..."):
                        text = maxxx.voice.transcribe(audio_path)
                        st.session_state.transcription = text
                        st.text_area("Transcription", text, height=200)
                        logger.log_voice_event("Transcription completed", {"length": len(text)})
                else:
                    st.error("Voice pipeline not available")
            except Exception as e:
                st.error(f"Recording failed: {e}")
                logger.error(LogCategory.VOICE, f"Recording failed: {e}")

    if "transcription" in st.session_state:
        st.markdown("---")
        st.subheader("Edit Transcription")
        edited_text = st.text_area(
            "Edit your content",
            st.session_state.transcription,
            height=200
        )

        if st.button("➡️ Proceed to Brain", use_container_width=True):
            st.session_state.content = edited_text
            st.session_state.page = "brain"
            st.rerun()


def render_draft(maxxx: MaxxxOS):
    st.title("✍️ Create Draft")
    st.markdown("---")

    render_orb("drafting")

    col1, col2 = st.columns([2, 1])
    with col1:
        content = st.text_area(
            "Your content",
            st.session_state.get("content", ""),
            height=300,
            placeholder="Enter your content here, or use voice input..."
        )

        uploaded_file = st.file_uploader("Upload media (optional)", type=["jpg", "jpeg", "png", "gif", "mp4"])
        if uploaded_file:
            st.info(f"Uploaded: {uploaded_file.name}")

    with col2:
        platform = st.selectbox(
            "Target Platform",
            list_platforms(),
            index=0
        )

        st.markdown("### Platform Rules")
        config_data = PLATFORM_RULES.get(platform, {})
        if "max_chars" in config_data:
            st.info(f"Max characters: {config_data['max_chars']}")
        if "min_chars" in config_data:
            st.info(f"Min characters: {config_data['min_chars']}")
        if "max_words" in config_data:
            st.info(f"Max words: {config_data['max_words']}")

        for rule_name, rule_desc in config_data.get("rules", []):
            st.markdown(f"- {rule_desc}")

    if st.button("🔍 Validate Draft", use_container_width=True):
        if not content:
            st.error("Please enter content to validate")
            return

        with st.spinner("Validating..."):
            render_orb("linting")
            logger.log_lint_result(platform, False, ["Starting validation"])
            result = validate_draft(platform, content)

            if result.passed:
                st.success("Draft passed validation!")
                render_orb("ready")
                st.session_state.draft = content
                st.session_state.platform = platform
                logger.log_lint_result(platform, True)
            else:
                st.error("Draft failed validation")
                render_orb("error")
                for error in result.errors:
                    st.error(f"- {error}")
                logger.log_lint_result(platform, False, result.errors)

            for warning in result.warnings:
                st.warning(f"- {warning}")

    if st.button("➡️ Proceed to Review", use_container_width=True):
        if "draft" in st.session_state:
            st.session_state.page = "review"
            st.rerun()
        else:
            st.error("Please validate a draft first")


def render_review(maxxx: MaxxxOS):
    st.title("📋 Review & Post")
    st.markdown("---")

    render_orb("ready")

    if "draft" not in st.session_state:
        st.info("No draft ready for review. Create a draft first.")
        return

    draft = st.session_state.draft
    platform = st.session_state.platform

    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Draft Preview")
        st.markdown(f"**Platform:** {platform.upper()}")
        st.markdown(f"**Characters:** {len(draft)}")
        st.markdown("---")
        st.text_area("Content", draft, height=400, disabled=True)

    with col2:
        st.subheader("Actions")

        if st.button("✏️ Edit Draft", use_container_width=True):
            st.session_state.editing = True

        if "editing" in st.session_state and st.session_state.editing:
            edited = st.text_area("Edit content", draft, height=300)
            if st.button("💾 Save Changes", use_container_width=True):
                st.session_state.draft = edited
                st.session_state.editing = False
                st.rerun()

        st.markdown("---")

        if st.button("🌐 Open Browser & Stage", use_container_width=True):
            with st.spinner("Opening browser..."):
                render_orb("typing")
                logger.log_browser_action("Staging post", platform)

                def stage_func():
                    if maxxx.executor:
                        return maxxx.executor.stage_post(platform, draft)
                    return clipboard_fallback(platform, draft)

                result = retry_handler.execute_with_retry(
                    stage_func,
                    component="browser",
                    operation="stage_post",
                    fallback=retry_handler.get_browser_fallback(platform, draft)
                )

                if result and hasattr(result, 'staged') and result.staged:
                    st.success(f" {result.message}")
                    render_orb("ready")
                    logger.log_browser_action("Post staged", platform, {"success": True})
                elif result and isinstance(result, dict) and result.get("success"):
                    st.info(result.get("message", "Draft copied to clipboard"))
                    render_orb("ready")
                else:
                    st.error(f"Failed: {getattr(result, 'message', 'Unknown error')}")
                    render_orb("error")

        st.markdown("---")

        if st.button("📋 Copy to Clipboard", use_container_width=True):
            import subprocess
            process = subprocess.Popen(
                ["clip"],
                stdin=subprocess.PIPE,
                shell=True
            )
            process.communicate(input=draft.encode("utf-16le"))
            st.success("Copied to clipboard!")

        if st.button("📅 Schedule for Later", use_container_width=True):
            st.session_state.page = "schedule"
            st.rerun()

        st.markdown("---")
        st.markdown("### HITL Safety")
        st.markdown("MAXXX OS will **never** auto-post. You must click the final 'Post' button in the browser.")


def render_scheduler(maxxx: MaxxxOS):
    st.title("📅 Schedule Posts")
    st.markdown("---")

    render_orb("idle")

    st.subheader("Schedule New Post")

    col1, col2 = st.columns(2)
    with col1:
        platform = st.selectbox("Platform", list_platforms(), key="sched_platform")
        content = st.text_area("Content", height=150, key="sched_content")

    with col2:
        sched_date = st.date_input("Date")
        sched_time = st.time_input("Time")

    if st.button("📅 Schedule Post", use_container_width=True):
        if not content:
            st.error("Please enter content")
            return

        scheduled_time = datetime.combine(sched_date, sched_time)
        post = scheduler.schedule_post(platform, content, scheduled_time)
        st.success(f"Post scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M')}")
        logger.log_user_action("Post scheduled", {"platform": platform, "time": scheduled_time.isoformat()})

    st.markdown("---")
    st.subheader("Scheduled Posts")

    pending_posts = scheduler.get_pending_posts()
    if pending_posts:
        for post in pending_posts:
            with st.expander(f"{post.platform.upper()} - {post.scheduled_time}"):
                st.text_area("Content", post.content, height=100, disabled=True, key=f"sched_{post.id}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Cancel", key=f"cancel_{post.id}"):
                        scheduler.cancel_post(post.id)
                        st.rerun()
                with col2:
                    st.markdown(f"**Status:** {post.status.value}")
    else:
        st.info("No scheduled posts")


def render_analytics():
    st.title("📊 Analytics")
    st.markdown("---")

    render_orb("idle")

    overview = analytics.get_overview(days=30)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Posts", overview["total_posts"])
    with col2:
        st.metric("Impressions", f"{overview['total_impressions']:,}")
    with col3:
        st.metric("Engagement", f"{overview['total_engagement']:,}")
    with col4:
        st.metric("Engagement Rate", f"{overview['avg_engagement_rate']:.1f}%")

    st.markdown("---")
    st.subheader("Platform Breakdown")

    platform_stats = overview.get("platform_breakdown", {})
    if platform_stats:
        for platform, stats in platform_stats.items():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**{platform.upper()}**")
            with col2:
                st.markdown(f"Posts: {stats['posts']}")
            with col3:
                st.markdown(f"Engagement: {stats['engagement']}")
    else:
        st.info("No analytics data yet. Start posting to see stats!")

    st.markdown("---")
    st.subheader("Top Posts")

    top_posts = analytics.get_top_posts(5)
    if top_posts:
        for post in top_posts:
            st.markdown(f"- **{post.platform.upper()}**: {post.content_preview}...")
    else:
        st.info("No post data available")


def render_settings():
    st.title("⚙️ Settings")
    st.markdown("---")

    st.subheader("🧠 Brain Settings")
    models = ollama.list_models()
    if models:
        st.info(f"Available models: {', '.join(models)}")
    else:
        st.warning("No models found. Run `ollama pull qwen2.5:7b`")

    col1, col2 = st.columns(2)
    with col1:
        primary_model = st.text_input("Primary Model", value=config.ollama.primary_model)
        temperature = st.slider("Temperature", 0.0, 1.0, config.ollama.temperature)
    with col2:
        fallback_model = st.text_input("Fallback Model", value=config.ollama.fallback_model)
        max_tokens = st.number_input("Max Tokens", 100, 4000, config.ollama.max_tokens)

    st.subheader("Voice Settings")
    col1, col2 = st.columns(2)
    with col1:
        whisper_model = st.selectbox("Whisper Model", ["tiny", "base", "small", "medium", "large"],
                                     index=["tiny", "base", "small", "medium", "large"].index(config.voice.whisper_model))
    with col2:
        tts_voice = st.selectbox("TTS Voice", ["en-US-GuyNeural", "en-US-AriaNeural", "en-US-JennyNeural"],
                                 index=["en-US-GuyNeural", "en-US-AriaNeural", "en-US-JennyNeural"].index(config.voice.tts_voice))

    st.subheader("Browser Settings")
    col1, col2 = st.columns(2)
    with col1:
        headless = st.checkbox("Headless mode", value=config.browser.headless)
    with col2:
        typing_delay = st.number_input("Typing delay (ms)", 10, 200, config.browser.typing_delay)

    st.subheader("Lint Settings")
    col1, col2 = st.columns(2)
    with col1:
        max_revisions = st.number_input("Max revisions", 1, 10, config.lint.max_revisions)
    with col2:
        strict_mode = st.checkbox("Strict mode", value=config.lint.strict_mode)

    st.subheader("Privacy Settings")
    st.markdown("""
    - All LLM calls go to `localhost:11434` (Ollama)
    - No telemetry sent to external servers
    - Voice processing done locally
    - Vault isolation - only reads from `vault/`
    """)

    if st.button("💾 Save Settings", use_container_width=True):
        config.ollama.primary_model = primary_model
        config.ollama.fallback_model = fallback_model
        config.ollama.temperature = temperature
        config.ollama.max_tokens = max_tokens
        config.voice.whisper_model = whisper_model
        config.voice.tts_voice = tts_voice
        config.browser.headless = headless
        config.browser.typing_delay = typing_delay
        config.lint.max_retries = max_revisions
        config.lint.strict_mode = strict_mode
        config_manager.save()
        st.success("Settings saved!")
        logger.log_user_action("Settings saved")


if __name__ == "__main__":
    main()
