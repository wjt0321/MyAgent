from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    
    # Capture console logs
    console_logs = []
    page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
    
    # Capture page errors
    page_errors = []
    page.on('pageerror', lambda err: page_errors.append(str(err)))
    
    print("=== Test 1: Page Load & Welcome Screen ===")
    page.goto('http://127.0.0.1:8080')
    page.wait_for_load_state('networkidle')
    time.sleep(1)
    
    # Screenshot welcome screen
    page.screenshot(path='d:/MyAgent/MyAgent/test_screenshots/01_welcome.png', full_page=True)
    print("Screenshot saved: 01_welcome.png")
    
    # Check theme class on html element (should be theme-dark by default)
    theme_class = page.evaluate('() => document.documentElement.className')
    print(f"HTML theme class: {theme_class}")
    
    print("\n=== Test 2: Theme Toggle (Dark -> Light) ===")
    # Click theme toggle
    page.click('#theme-toggle')
    time.sleep(0.5)
    
    theme_class_after = page.evaluate('() => document.documentElement.className')
    print(f"HTML theme class after toggle: {theme_class_after}")
    
    page.screenshot(path='d:/MyAgent/MyAgent/test_screenshots/02_theme_light.png', full_page=True)
    print("Screenshot saved: 02_theme_light.png")
    
    # Toggle back to dark
    page.click('#theme-toggle')
    time.sleep(0.5)
    
    print("\n=== Test 3: Search Navigation UI ===")
    # Use JavaScript to click search toggle to avoid overlay issues
    page.evaluate('() => document.getElementById("search-toggle").click()')
    time.sleep(0.5)
    
    # Check if search nav buttons exist
    search_prev = page.query_selector('#search-prev')
    search_next = page.query_selector('#search-next')
    search_count = page.query_selector('#search-count')
    
    print(f"Search prev button exists: {search_prev is not None}")
    print(f"Search next button exists: {search_next is not None}")
    print(f"Search count exists: {search_count is not None}")
    
    page.screenshot(path='d:/MyAgent/MyAgent/test_screenshots/03_search_bar.png', full_page=True)
    print("Screenshot saved: 03_search_bar.png")
    
    # Close search
    page.evaluate('() => document.getElementById("search-close").click()')
    time.sleep(0.3)
    
    print("\n=== Test 4: File Browser & Parent Navigation ===")
    # Switch to files view using JavaScript
    page.evaluate('() => document.querySelector(\'[data-view="files"]\').click()')
    time.sleep(1)
    
    page.screenshot(path='d:/MyAgent/MyAgent/test_screenshots/04_file_browser.png', full_page=True)
    print("Screenshot saved: 04_file_browser.png")
    
    # Try to navigate into a directory if exists
    dirs = page.query_selector_all('.file-tree-node .file-tree-item')
    print(f"Found {len(dirs)} file tree items")
    
    # Check for parent navigation (should not show at root)
    parent_items = page.query_selector_all('.file-tree-item:has-text("..")')
    print(f"Parent '..' items at root: {len(parent_items)}")
    
    print("\n=== Test 5: Console Logs & Errors ===")
    print(f"Console logs ({len(console_logs)}):")
    for log in console_logs[:20]:
        print(f"  {log}")
    
    print(f"\nPage errors ({len(page_errors)}):")
    for err in page_errors:
        print(f"  {err}")
    
    print("\n=== Test Complete ===")
    browser.close()
