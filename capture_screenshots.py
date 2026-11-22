"""
Capture visual screenshots of the deployed Vercel web application.
"""

import time
from playwright.sync_api import sync_playwright

URL = "https://heart-disease-classifier-sepia.vercel.app"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 920})
    
    print(f"Navigating to {URL}...")
    page.goto(URL, wait_until="networkidle")
    time.sleep(2)
    
    # 1. Overview screenshot
    page.screenshot(path="figures/screenshot_app_overview.png", full_page=False)
    print("Captured figures/screenshot_app_overview.png")
    
    # 2. High-Risk preset screenshot
    page.click("button[data-preset='highrisk']")
    time.sleep(1)
    page.screenshot(path="figures/screenshot_app_highrisk.png", full_page=False)
    print("Captured figures/screenshot_app_highrisk.png")
    
    # 3. Healthy preset screenshot
    page.click("button[data-preset='healthy']")
    time.sleep(1)
    page.screenshot(path="figures/screenshot_app_healthy.png", full_page=False)
    print("Captured figures/screenshot_app_healthy.png")
    
    # 4. Scroll to methodology section
    methodology_el = page.query_selector("#methodology")
    if methodology_el:
        methodology_el.scroll_into_view_if_needed()
        time.sleep(1)
        page.screenshot(path="figures/screenshot_app_methodology.png", full_page=False)
        print("Captured figures/screenshot_app_methodology.png")
        
    browser.close()
    print("All live screenshots captured successfully!")
