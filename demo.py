"""
MAXXX OS - Hackathon Demo Script
3-minute live demo flow
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from brain import brain
from ollama_client import ollama
from golden_lint import validate_draft, list_platforms
from vault_reader import vault
from memory import memory, MemoryType
from analytics import analytics

def print_header(text):
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_step(num, text):
    print(f"\n  [{num}] {text}")

def main():
    print_header("MAXXX OS - HACKATHON DEMO")
    print("  Local-First. Anti-API. 100% Privacy.")
    print()
    
    # Step 1: Show system status
    print_step(1, "SYSTEM STATUS")
    print(f"     Ollama: {'Connected' if ollama.is_available() else 'Disconnected'}")
    print(f"     Models: {ollama.list_models()}")
    print(f"     Platforms: {len(list_platforms())}")
    
    # Step 2: Classify content
    print_step(2, "AUTO-CLASSIFY CONTENT")
    idea = "I built a local AI agent that posts to 20 platforms without using any cloud APIs"
    print(f"     Input: {idea}")
    
    classification = brain.classify_input(idea)
    print(f"     Division: {classification.get('division', 'unknown')}")
    print(f"     Platform: {classification.get('platform_suggestion', 'x')}")
    
    # Step 3: Generate draft
    print_step(3, "GENERATE DRAFT (Qwen 2.5 7B)")
    result = brain.generate_draft(content_idea=idea, platform="x")
    print(f"     Success: {result.success}")
    print(f"     Revisions: {result.revision_count}")
    print(f"     Length: {len(result.draft)} chars")
    print(f"     Draft: {result.draft}")
    
    # Step 4: Validate
    print_step(4, "VALIDATE (40 Golden Rules)")
    lint = validate_draft("x", result.draft)
    print(f"     Passed: {lint.passed}")
    if lint.errors:
        print(f"     Errors: {lint.errors}")
    if lint.warnings:
        print(f"     Warnings: {lint.warnings}")
    
    # Step 5: Store in memory
    print_step(5, "STORE IN MEMORY")
    entry = memory.store_draft("x", result.draft, {"idea": idea})
    print(f"     Stored: {entry.id}")
    stats = memory.get_stats()
    print(f"     Total Drafts: {stats.get('draft', 0)}")
    
    # Step 6: Track analytics
    print_step(6, "TRACK ANALYTICS")
    post = analytics.track_post(
        post_id=entry.id,
        platform="x",
        content=result.draft
    )
    print(f"     Tracked: {post.post_id}")
    
    # Step 7: Show ready state
    print_step(7, "READY FOR BROWSER STAGING")
    print("     Browser automation ready via Playwright")
    print("     Human-in-the-loop: YOU click the final Post button")
    
    print_header("DEMO COMPLETE")
    print("  Key Points:")
    print("  - 100% local (Ollama + Qwen 2.5)")
    print("  - Zero cloud APIs")
    print("  - 20 platform support")
    print("  - Human-in-the-loop safety")
    print()
    print("  Run: streamlit run main.py")
    print("  Open: http://localhost:8501")
    print()

if __name__ == "__main__":
    main()
