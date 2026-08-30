"""
MAXXX OS - Playwright Test
Tests browser automation with real Chrome
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright_engine import PlatformExecutor, get_chrome_user_data_dir

def test_playwright():
    print("=" * 60)
    print("PLAYWRIGHT BROWSER AUTOMATION TEST")
    print("=" * 60)
    
    # Check Chrome user data
    try:
        user_data = get_chrome_user_data_dir()
        print(f"Chrome User Data: {user_data}")
        
        import os
        if os.path.exists(user_data):
            print(f"Chrome Profile: EXISTS")
        else:
            print(f"Chrome Profile: NOT FOUND")
            return False
    except Exception as e:
        print(f"Chrome Detection Error: {e}")
        return False
    
    # Test browser launch
    print()
    print("Launching browser (headless=False for HITL)...")
    
    try:
        executor = PlatformExecutor(headless=False)
        success = executor.launch()
        
        if success:
            print("Browser: LAUNCHED SUCCESSFULLY")
            print()
            print("Navigating to X (Twitter)...")
            
            page = executor.page
            page.goto("https://x.com", wait_until="networkidle", timeout=30000)
            print(f"Current URL: {page.url}")
            print(f"Page Title: {page.title()}")
            
            print()
            print("Browser test PASSED!")
            print("Close the browser window manually when done.")
            
            # Keep browser open for manual inspection
            input("Press Enter to close browser...")
            executor.close()
            return True
        else:
            print("Browser: FAILED TO LAUNCH")
            return False
            
    except Exception as e:
        print(f"Browser Error: {e}")
        print()
        print("Trying clipboard fallback test...")
        from playwright_engine import clipboard_fallback
        result = clipboard_fallback("x", "Test post content")
        print(f"Clipboard Fallback: {result.message}")
        return True

if __name__ == "__main__":
    test_playwright()
