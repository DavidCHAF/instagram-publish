import time
import random
from playwright.sync_api import Page

def randomized_sleep(min_seconds: float = 2.0, max_seconds: float = 6.0):
    """Sleeps for a random duration between min_seconds and max_seconds."""
    sleep_time = random.uniform(min_seconds, max_seconds)
    print(f"Human delay: sleeping for {sleep_time:.2f}s...")
    time.sleep(sleep_time)

def human_type(page: Page, selector: str, text: str):
    """Types into an input field with randomized delays between keystrokes."""
    page.click(selector)
    page.locator(selector).press_sequentially(text, delay=random.randint(50, 200))
        
def human_scroll(page: Page, scrolls: int = 3):
    """Simulates a human scrolling down the page."""
    for _ in range(scrolls):
        # Scroll down by a random amount
        scroll_amount = int(random.uniform(300, 800))
        page.mouse.wheel(0, scroll_amount)
        randomized_sleep(1.0, 3.5)
        
def human_move_mouse(page: Page):
    """Simulates random mouse movements across the screen."""
    # Get viewport size
    viewport = page.viewport_size
    if not viewport:
        return
        
    width = viewport['width']
    height = viewport['height']
    
    # Move to a few random points
    for _ in range(random.randint(2, 4)):
        x = random.randint(0, width)
        y = random.randint(0, height)
        # Playwright moves instantly by default, to make it somewhat smooth we could use steps (advanced)
        # For simplicity, we just teleport with delays, or rely on stealth plugins
        page.mouse.move(x, y, steps=10) 
        randomized_sleep(0.5, 1.5)
