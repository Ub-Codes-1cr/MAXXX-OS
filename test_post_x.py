"""
MAXXX OS - Browser Posting Test
Handles first-time login and clipboard fallback
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import time
from brain import brain
from playwright_engine import PlatformExecutor, clipboard_fallback

print("=" * 60)
print("BROWSER POSTING TEST")
print("=" * 60)

# Step 1: Generate draft
print("\n[1] Generating draft...")
result = brain.generate_draft(
    content_idea="MAXXX OS hackathon demo - local AI posting to 20 platforms without cloud APIs",
    platform="x"
)

if not result.success:
    print(f"ERROR: {result.errors}")
    sys.exit(1)

draft = result.draft
print(f"Draft ({len(draft)} chars): {draft}")

# Step 2: Launch browser
print("\n[2] Launching Chrome...")
executor = PlatformExecutor(headless=False)

if not executor.launch():
    print("ERROR: Failed to launch browser")
    print("FALLBACK: Copying draft to clipboard...")
    clipboard_fallback("x", draft)
    sys.exit(1)

page = executor.page

# Step 3: Navigate to X
print("\n[3] Navigating to X...")
page.goto("https://x.com")
time.sleep(8)  # Wait longer for page load

page.screenshot(path="screenshot_check.png")

# Check if logged in by looking for logged-in indicators
content = page.content()
url = page.url

# X shows login when not authenticated
is_logged_in = (
    "See what's happening" not in content and 
    "Happening now" not in content and
    "/login" not in url and
    "/compose" not in url  # Would redirect to login if not authed
)

# Also check for positive indicators (compose button, profile menu, etc.)
if not is_logged_in:
    logged_in_indicators = ['data-testid="SideNav_NewTweet_Button"', 'data-testid="AppTabBar_Home_Link"']
    for indicator in logged_in_indicators:
        if indicator in content:
            is_logged_in = True
            break

if is_logged_in:
    print("ALREADY LOGGED IN!")
else:
    print("\n" + "=" * 60)
    print("NOT LOGGED IN")
    print("=" * 60)
    print("Please log in to X in the browser window.")
    print("Your session will be saved for future runs.")
    print("")
    print("Waiting up to 120 seconds for login...")
    
    # Wait for login (check every 5 seconds)
    for i in range(24):
        time.sleep(5)
        content = page.content()
        url = page.url
        
        # Check for logged-in indicators
        has_login_page = "See what's happening" in content or "Happening now" in content
        has_logged_in = 'data-testid="SideNav_NewTweet_Button"' in content or 'data-testid="AppTabBar_Home_Link"' in content
        
        if has_logged_in or (not has_login_page and "/login" not in url):
            print("LOGIN DETECTED!")
            is_logged_in = True
            break
        print(f"  Waiting... ({(i+1)*5}s)")

if not is_logged_in:
    print("\nLogin timed out. Using clipboard fallback.")
    clipboard_fallback("x", draft)
    executor.close()
    sys.exit(1)

# Step 4: Navigate to compose
print("\n[4] Navigating to compose...")
page.goto("https://x.com/compose/post")
time.sleep(5)

page.screenshot(path="screenshot_compose.png")

# Step 5: Try to type
print("\n[5] Looking for text input...")
typed = False

selectors = [
    'div[data-testid="tweetTextarea_0"]',
    'div[role="textbox"]',
    'div[contenteditable="true"]',
    '.public-DraftEditor-content',
    'textarea'
]

for selector in selectors:
    try:
        el = page.locator(selector).first
        if el.is_visible(timeout=3000):
            el.click()
            time.sleep(0.5)
            page.keyboard.type(draft, delay=30)
            typed = True
            print(f"TYPED using selector: {selector}")
            break
    except:
        continue

if not typed:
    print("Trying keyboard.type directly...")
    try:
        page.keyboard.type(draft, delay=30)
        typed = True
        print("TYPED using keyboard.type")
    except Exception as e:
        print(f"Failed: {e}")

# Step 6: Final screenshot
page.screenshot(path="screenshot_final.png")

if typed:
    print("\n" + "=" * 60)
    print("SUCCESS - DRAFT IN COMPOSE BOX!")
    print("Click the Post button manually.")
    print("=" * 60)
else:
    print("\nBrowser typing failed - Using clipboard fallback")
    clipboard_fallback("x", draft)

# Cleanup
print("\nPress Enter to close browser...")
try:
    input()
except EOFError:
    time.sleep(5)

executor.close()
print("\nDone!")
