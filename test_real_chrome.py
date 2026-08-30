import sys
sys.stdout.reconfigure(encoding='utf-8')

from playwright_engine import PlatformExecutor, get_chrome_executable, get_chrome_user_data_dir

print("Chrome executable:", get_chrome_executable())
print("User data dir:", get_chrome_user_data_dir())

print("\nLaunching real Chrome...")
executor = PlatformExecutor(headless=False)
success = executor.launch()

if success:
    print("SUCCESS! Browser launched!")
    page = executor.page
    
    print("\nNavigating to X...")
    page.goto("https://x.com", wait_until="domcontentloaded", timeout=60000)
    
    import time
    time.sleep(5)
    
    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")
    
    if "login" in page.url.lower():
        print("Status: NOT LOGGED IN")
    else:
        print("Status: LOGGED IN!")
        
    print("\nTaking screenshot...")
    page.screenshot(path="screenshot_test.png")
    print("Screenshot saved to screenshot_test.png")
    
    input("\nPress Enter to close...")
    executor.close()
else:
    print("FAILED to launch browser")
