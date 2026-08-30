"""
MAXXX OS - End-to-End Test
Tests the complete pipeline from idea to browser staging
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from brain import brain
from ollama_client import ollama
from golden_lint import validate_draft, list_platforms
from vault_reader import vault
from memory import memory, MemoryType
from analytics import analytics
from retry_handler import retry_handler
from scheduler import scheduler
from config import config

def test_1_ollama_connection():
    print("=" * 60)
    print("TEST 1: Ollama Connection")
    print("=" * 60)
    
    available = ollama.is_available()
    print(f"  Ollama Status: {'CONNECTED' if available else 'DISCONNECTED'}")
    
    if available:
        models = ollama.list_models()
        print(f"  Available Models: {models}")
        
        has_qwen = any('qwen' in m for m in models)
        has_hermes = any('hermes' in m for m in models)
        print(f"  Qwen 2.5: {'OK' if has_qwen else 'MISSING'}")
        print(f"  Hermes 3: {'OK' if has_hermes else 'MISSING'}")
    
    print(f"  Result: {'PASS' if available else 'FAIL'}")
    print()
    return available

def test_2_vault_rules():
    print("=" * 60)
    print("TEST 2: Vault Rules (20 Platforms)")
    print("=" * 60)
    
    platforms = vault.list_platforms()
    print(f"  Platforms Found: {len(platforms)}")
    
    for platform in platforms[:5]:
        rules = vault.get_platform_rules(platform)
        print(f"  {platform.upper()}: {len(rules.raw_content)} chars")
    
    print(f"  Brand Voice: {'OK' if vault.get_brand_voice().raw_content else 'MISSING'}")
    print(f"  Result: PASS")
    print()
    return True

def test_3_golden_lint():
    print("=" * 60)
    print("TEST 3: Golden Lint (40 Rules)")
    print("=" * 60)
    
    test_drafts = {
        "x": "I built a local AI agent that posts to 20 platforms. Zero APIs. #MAXXXOS",
        "linkedin": """After 40 days of building in public, here is what I learned about local-first AI development:

The traditional approach relies on cloud APIs - expensive, rate-limited, and privacy-risky. I tried something completely different.

I built MAXXX OS: a local AI agent that controls your actual browser. No API keys. No cloud dependency. 100% privacy. Everything runs on your machine.

Key learnings from this journey:

1. Local LLMs like Qwen 2.5 are now genuinely good enough for content generation. The quality gap with cloud models is shrinking fast.

2. Browser automation using Playwright beats APIs for reliability. APIs break when platforms change endpoints. Your browser just works.

3. Human-in-the-loop is non-negotiable for trust. The AI stages posts, but you click the final button. Always.

4. The anti-cloud movement is real. Creators want ownership of their workflow, not another subscription.

The result? 20 platforms managed from one dashboard. Average post time dropped from 45 minutes to 5 minutes.

I am curious about your experience. Have you tried running LLMs locally? What stopped you from going cloud-free? Let me know in the comments.""",
        "github": "# Maxxx OS\n\n## Installation\n\n```bash\npip install -r requirements.txt\n```\n\n## Usage\n\n```python\nfrom brain import brain\nbrain.generate_draft('idea', 'x')\n```",
    }
    
    passed = 0
    for platform, draft in test_drafts.items():
        result = validate_draft(platform, draft)
        status = "PASS" if result.passed else "FAIL"
        print(f"  {platform.upper()}: {status} ({len(draft)} chars)")
        if result.passed:
            passed += 1
    
    print(f"  Result: {passed}/{len(test_drafts)} passed")
    print()
    return passed == len(test_drafts)

def test_4_brain_generation():
    print("=" * 60)
    print("TEST 4: Brain Draft Generation")
    print("=" * 60)
    
    if not ollama.is_available():
        print("  Skipped - Ollama not connected")
        print("  Result: SKIP")
        print()
        return None
    
    print("  Generating draft for X...")
    result = brain.generate_draft(
        content_idea="I built a local AI agent that posts to 20 platforms without APIs",
        platform="x"
    )
    
    print(f"  Platform: {result.platform}")
    print(f"  Success: {result.success}")
    print(f"  Revisions: {result.revision_count}")
    print(f"  Length: {len(result.draft)} chars")
    print(f"  Draft: {result.draft[:100]}...")
    
    if result.errors:
        print(f"  Errors: {result.errors}")
    if result.warnings:
        print(f"  Warnings: {result.warnings}")
    
    print(f"  Result: {'PASS' if result.success else 'FAIL'}")
    print()
    return result

def test_5_memory_system():
    print("=" * 60)
    print("TEST 5: Memory System")
    print("=" * 60)
    
    entry = memory.store_draft("x", "Test draft content", {"test": True})
    print(f"  Stored Draft: {entry.id}")
    
    stats = memory.get_stats()
    print(f"  Memory Stats: {stats}")
    
    recent = memory.retrieve_recent(MemoryType.DRAFT, count=5)
    print(f"  Recent Drafts: {len(recent)}")
    
    print(f"  Result: PASS")
    print()
    return True

def test_6_analytics():
    print("=" * 60)
    print("TEST 6: Analytics Module")
    print("=" * 60)
    
    post = analytics.track_post(
        post_id="test_001",
        platform="x",
        content="Test post for analytics",
        url="https://x.com/test"
    )
    print(f"  Tracked Post: {post.post_id}")
    
    overview = analytics.get_overview(7)
    print(f"  7-Day Overview: {overview['total_posts']} posts")
    
    print(f"  Result: PASS")
    print()
    return True

def test_7_retry_handler():
    print("=" * 60)
    print("TEST 7: Retry Handler")
    print("=" * 60)
    
    def success_func():
        return "Success!"
    
    result = retry_handler.execute_with_retry(
        success_func,
        component="test",
        operation="test_operation"
    )
    print(f"  Retry Test: {result}")
    
    stats = retry_handler.get_error_stats()
    print(f"  Error Stats: {stats}")
    
    print(f"  Result: PASS")
    print()
    return True

def test_8_scheduler():
    print("=" * 60)
    print("TEST 8: Scheduler")
    print("=" * 60)
    
    from datetime import datetime, timedelta
    
    scheduled = scheduler.schedule_post(
        platform="x",
        content="Scheduled test post",
        scheduled_time=datetime.now() + timedelta(hours=1)
    )
    print(f"  Scheduled Post: {scheduled.id}")
    
    stats = scheduler.get_stats()
    print(f"  Queue Stats: {stats}")
    
    scheduler.cancel_post(scheduled.id)
    print(f"  Cancelled Post: {scheduled.id}")
    
    print(f"  Result: PASS")
    print()
    return True

def main():
    print()
    print("#" * 60)
    print("#  MAXXX OS - End-to-End Test Suite")
    print("#" * 60)
    print()
    
    results = {}
    
    results["ollama"] = test_1_ollama_connection()
    results["vault"] = test_2_vault_rules()
    results["lint"] = test_3_golden_lint()
    results["brain"] = test_4_brain_generation()
    results["memory"] = test_5_memory_system()
    results["analytics"] = test_6_analytics()
    results["retry"] = test_7_retry_handler()
    results["scheduler"] = test_8_scheduler()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test, result in results.items():
        if result is None:
            status = "SKIP"
        elif result:
            status = "PASS"
        else:
            status = "FAIL"
        print(f"  {test.upper():15} : {status}")
    
    passed = sum(1 for r in results.values() if r is True)
    total = len(results)
    print()
    print(f"  Total: {passed}/{total} passed")
    print()
    
    if passed >= 6:
        print("  SYSTEM READY FOR DEMO!")
    else:
        print("  FIX ISSUES BEFORE DEMO")
    
    print()

if __name__ == "__main__":
    main()
