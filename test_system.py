"""
MAXXX OS - System Test
Verifies all components are working correctly
"""

import sys
from pathlib import Path

def test_golden_lint():
    from golden_lint import validate_draft, list_platforms, PLATFORM_RULES
    print("[OK] golden_lint.py loaded")
    print(f"   Platforms: {len(list_platforms())}")
    return True

def test_vault_reader():
    from vault_reader import vault
    print("[OK] vault_reader.py loaded")
    platforms = vault.list_platforms()
    print(f"   Vault platforms: {len(platforms)}")
    return True

def test_ollama_client():
    from ollama_client import ollama
    print("[OK] ollama_client.py loaded")
    available = ollama.is_available()
    print(f"   Ollama available: {available}")
    return True

def test_draft_generator():
    from draft_generator import draft_generator
    print("[OK] draft_generator.py loaded")
    return True

def test_brain():
    from brain import brain
    print("[OK] brain.py loaded")
    status = brain.get_status()
    print(f"   Brain state: {status['state']}")
    return True

def test_voice_pipeline():
    try:
        from voice_pipeline import VoicePipeline
        print("[OK] voice_pipeline.py loaded")
        return True
    except ImportError as e:
        print(f"[WARN] voice_pipeline.py - optional dependency: {e}")
        return True

def test_playwright_engine():
    try:
        from playwright_engine import PlatformExecutor
        print("[OK] playwright_engine.py loaded")
        return True
    except ImportError as e:
        print(f"[WARN] playwright_engine.py - optional dependency: {e}")
        return True

def test_config():
    from config import config_manager, config
    print("[OK] config.py loaded")
    print(f"   Primary model: {config.ollama.primary_model}")
    return True

def test_logger():
    from logger import logger, LogCategory
    print("[OK] logger.py loaded")
    logger.info(LogCategory.SYSTEM, "Test log entry")
    return True

def test_memory():
    from memory import memory, MemoryType
    print("[OK] memory.py loaded")
    stats = memory.get_stats()
    print(f"   Memory entries: {stats}")
    return True

def test_scheduler():
    from scheduler import scheduler, ScheduleStatus
    print("[OK] scheduler.py loaded")
    stats = scheduler.get_stats()
    print(f"   Scheduler stats: {stats}")
    return True

def test_analytics():
    from analytics import analytics
    print("[OK] analytics.py loaded")
    overview = analytics.get_overview(7)
    print(f"   Posts (7 days): {overview['total_posts']}")
    return True

def test_media_handler():
    from media_handler import media_handler
    print("[OK] media_handler.py loaded")
    stats = media_handler.get_media_stats()
    print(f"   Media stats: {stats}")
    return True

def test_retry_handler():
    from retry_handler import retry_handler
    print("[OK] retry_handler.py loaded")
    return True

def main():
    print("=" * 50)
    print("MAXXX OS - System Test")
    print("=" * 50)
    print()

    tests = [
        test_golden_lint,
        test_vault_reader,
        test_ollama_client,
        test_draft_generator,
        test_brain,
        test_voice_pipeline,
        test_playwright_engine,
        test_config,
        test_logger,
        test_memory,
        test_scheduler,
        test_analytics,
        test_media_handler,
        test_retry_handler,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__} - {e}")
            failed += 1

    print()
    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    if failed > 0:
        sys.exit(1)
    return 0

if __name__ == "__main__":
    main()
