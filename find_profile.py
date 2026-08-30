import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright_engine import PlaywrightEngine, get_chrome_user_data_dir
import time

print("=" * 60)
print("FIND YOUR LOGGED-IN PROFILE")
print("=" * 60)

profiles_to_check = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5", "Profile 6", "Profile 7", "Profile 8", "Profile 9", "Profile 10"]

for profile in profiles_to_check:
    print(f"\nTesting {profile}...")
    
    try:
        engine = PlaywrightEngine(headless=False)
        engine.playwright = engine.playwright if hasattr(engine, 'playwright') and engine.playwright else __import__('playwright.sync_api', fromlist=['sync_playwright']).sync_playwright().start()
        
        user_data_dir = get_chrome_user_data_dir()
        
        context = engine.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            args=[f"--profile-directory={profile}"],
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.new_page()
        page.goto("https://x.com", wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
        
        url = page.url
        title = page.title()
        
        logged_in = "x.com" in url and "login" not in url
        status = "LOGGED IN" if logged_in else "NOT LOGGED IN"
        
        print(f"  URL: {url}")
        print(f"  Status: {status}")
        
        context.close()
        
        if logged_in:
            print(f"\n*** FOUND! Use profile: {profile} ***")
            break
            
    except Exception as e:
        print(f"  Error: {str(e)[:50]}")
        try:
            context.close()
        except:
            pass

print("\n" + "=" * 60)
