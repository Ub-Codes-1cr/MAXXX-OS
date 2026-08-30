import sys
sys.stdout.reconfigure(encoding='utf-8')

# Try to read the shortcut file directly
with open(r'C:\Users\syedu\OneDrive\Desktop\UB Chrome.lnk', 'rb') as f:
    content = f.read()

# Look for Chrome executable path in the binary
text = content.decode('utf-16-le', errors='ignore')
if 'chrome' in text.lower():
    # Find chrome.exe path
    import re
    paths = re.findall(r'[A-Z]:\\[^\\]+\\chrome\.exe', text, re.IGNORECASE)
    if paths:
        print('Chrome Path:', paths[0])
    
    # Find profile directory
    profiles = re.findall(r'--profile-directory=([^\s"]+)', text)
    if profiles:
        print('Profile:', profiles[0])
    
    # Find user data dir
    userData = re.findall(r'--user-data-dir=([^\s"]+)', text)
    if userData:
        print('User Data Dir:', userData[0])

print()
print('Looking for workspace info...')
# Check for any workspace-related strings
workspace = re.findall(r'workspace[^\s"]*', text, re.IGNORECASE)
if workspace:
    print('Workspace:', workspace)

# Also look for any profile paths
profile_paths = re.findall(r'Profile \d+', text)
if profile_paths:
    print('Profiles found:', profile_paths)
