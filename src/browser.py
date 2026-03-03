import os
import random
from typing import Optional
from playwright.sync_api import sync_playwright, BrowserContext, Page
from playwright_stealth import Stealth

class InstagramBrowser:
    def __init__(self, headless: bool = False, mobile_emulation: bool = True):
        self.headless = headless
        self.mobile_emulation = mobile_emulation
        self.playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # We will store state in the data directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.state_file = os.path.join(base_dir, 'data', 'cookies.json')
        
    def start(self) -> Page:
        self.playwright = sync_playwright().start()
        
        # We use standard typical arguments to decrease detection
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
        ]
        
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=browser_args
        )
        
        # Setup context
        context_options = {
            'viewport': {'width': 390, 'height': 844} if self.mobile_emulation else {'width': 1280, 'height': 720},
            'user_agent': self._get_user_agent(),
            'device_scale_factor': 3 if self.mobile_emulation else 1,
            'is_mobile': self.mobile_emulation,
            'has_touch': self.mobile_emulation,
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
        }
        
        # Load saved session if exists
        if os.path.exists(self.state_file):
            print(f"Loading existing session state from {self.state_file}")
            context_options['storage_state'] = self.state_file
            
        self.context = self.browser.new_context(**context_options)
        
        # Apply extra stealth mechanisms
        self.page = self.context.new_page()
        Stealth().apply_stealth_sync(self.page)
        
        return self.page
        
    def _get_user_agent(self) -> str:
        if self.mobile_emulation:
            # Typical iPhone user agent
            return "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
        else:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
    def save_state(self):
        if self.context:
            self.context.storage_state(path=self.state_file)
            print(f"Session state saved to {self.state_file}")
            
    def close(self):
        if self.context:
            self.save_state()
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
