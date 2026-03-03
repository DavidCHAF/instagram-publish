import sys
import os
import time
from playwright.sync_api import sync_playwright
import json

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        cookies_path = os.path.join("data", "cookies.json")
        context_args = {}
        if os.path.exists(cookies_path):
            context_args["storage_state"] = cookies_path
        context = browser.new_context(**context_args)
        page = context.new_page()
        page.goto("https://www.instagram.com/")
        time.sleep(5)
        
        # Output all SVGs and their parent structures
        items = page.evaluate('''() => {
            const svgs = Array.from(document.querySelectorAll('svg'));
            return svgs.map(s => {
                let parent = s.closest('a') || s.closest('div[role="button"]') || s.closest('button') || s.parentElement;
                let text = parent ? parent.innerText : '';
                return {
                    'aria_label': s.getAttribute('aria-label') || 'N/A',
                    'parent_role': parent ? parent.getAttribute('role') : 'N/A',
                    'parent_href': parent ? parent.getAttribute('href') : 'N/A',
                    'parent_text': text.replace(/\\n/g, ' ').trim()
                };
            }).filter(i => i.parent_text.length > 0 || i.aria_label !== 'N/A');
        }''')
        
        with open("sidebar_inspect.json", "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
            
        print("Dumped sidebar svg items.")
        browser.close()

if __name__ == "__main__":
    inspect()
