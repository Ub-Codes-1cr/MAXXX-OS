"""
MAXXX OS - Quick Browser Test
Tests browser launch and basic navigation
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright_engine import PlatformExecutor

print("Launching browser with your Chrome profile...")
executor = PlatformExecutor(headless=False)
success = executor.launch()

if not success:
    print("Failed to launch browser")
    sys.exit(1)

print("Browser launched!")
page = executor.page

# Test navigation to a fast site first
print("\nTesting navigation to Google...")
try:
    page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=15000)
    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")
    print("Google: OK")
except Exception as e:
    print(f"Google error: {e}")

# Test X navigation with longer timeout
print("\nNavigating to X (Twitter)...")
try:
    page.goto("https://x.com", wait_until="domcontentloaded", timeout=60000)
    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")
    
    if "x.com" in page.url and "login" not in page.url:
        print("X: LOGGED IN!")
    elif "login" in page.url:
        print("X: NOT LOGGED IN (redirected to login)")
    else:
        print(f"X: Current URL - {page.url}")
except Exception as e:
    print(f"X navigation: {e}")

print("\nBrowser is open. Check your screen.")
print("Press Enter in this terminal to close browser...")

try:
    input()
except EOFError:
    pass

executor.close()
print("Browser closed.")
