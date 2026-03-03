import os
import random
import json
from dotenv import load_dotenv

from src.browser import InstagramBrowser
from src.quota_manager import QuotaManager
from src.uploader import InstagramUploader
from src.human_behavior import randomized_sleep

load_dotenv()

def get_random_caption():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    captions_path = os.path.join(base_dir, 'config', 'captions.txt')
    
    try:
        with open(captions_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split by the '---' delimiter and remove empty strings
        captions = [c.strip() for c in content.split('---') if c.strip()]
        
        if not captions:
            return "Default caption!"
            
        return random.choice(captions)
    except Exception as e:
        print(f"Error reading captions.txt: {e}")
        return "Default caption!"

def run_task(post_type: str, skip_quota: bool = False):
    print(f"--- Starting task for {post_type.upper()} ---")
    quota = QuotaManager()
    
    # Quota check
    if not skip_quota:
        if not quota.can_publish(post_type):
            print(f"Quota reached for {post_type} today. Skipping.")
            return
        print(f"Quota check passed. Initializing browser...")
    else:
        print(f"TEST MODE: Bypassing quota check. Initializing browser...")
    
    # Initialize browser (visible for testing, switch to headless=True for prod if confident)
    is_mobile = (post_type == "story")
    browser = InstagramBrowser(headless=False, mobile_emulation=is_mobile)
    page = browser.start()
    
    try:
        uploader = InstagramUploader(page)
        
        # Check if we are logged in by going to home
        page.goto("https://www.instagram.com/")
        randomized_sleep(4, 7)
        
        # Check if we need to log in
        login_input = page.locator('input[name="username"]')
        if login_input.count() > 0 or "/accounts/login/" in page.url:
            print("Detected login page.")
            print("Please log in manually in the opened browser window.")
            input("Press Enter here in the console ONCE you have successfully logged in and are on the Instagram home page...")
            
            # Save cookies after manual login
            browser.save_state()
            print("Saved browser state. Logged in successfully.")
            
        print("Proceeding with upload...")
        
        # Get REAL file from user to prevent browser rejection of mock text files
        print(f"\nTime to pick a {post_type} file!")
        media_path = input("Please enter the ABSOLUTE path to the real image or video file: ").strip()
        
        # Ensure path has no quotes from dragging and dropping in terminal
        if media_path.startswith('"') and media_path.endswith('"'):
            media_path = media_path[1:-1]
            
        if not os.path.exists(media_path):
            print("Error: The file path provided does not exist!")
            return
            
        caption = get_random_caption()
        
        if post_type == "post":
            uploader.publish_post(media_path, caption)
        elif post_type == "reel":
            uploader.publish_reel(media_path, caption)
        elif post_type == "story":
            uploader.publish_story(media_path)
            
        # Record success
        if not skip_quota:
            quota.record_publication(post_type, media_path)
            print(f"Successfully recorded {post_type} publication in database.")
        else:
            print(f"TEST MODE: Successfully published {post_type} without recording into database.")
        
    except Exception as e:
        import traceback
        print(f"An error occurred: {e}")
        traceback.print_exc()
        with open("error.txt", "w", encoding="utf-8") as err_f:
            err_f.write(traceback.format_exc())
        try:
            page.screenshot(path="error_screenshot.png")
            print("Saved error screenshot.")
            with open("error_page.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("Saved error HTML page.")
        except:
            pass
    finally:
        browser.close()
        print("Browser closed.")

if __name__ == "__main__":
    print("Instagram Publisher Automated System")
    
    while True:
        print("\n=== MAiN MENU ===")
        print("1. Post a Story")
        print("2. Post a Reel")
        print("3. Post a Standard/Carousel Post")
        print("0. Exit")
        
        choice = input("Enter your choice (0-3): ").strip()
        
        if choice in ["1", "2", "3"]:
            test_mode = input("Run in TEST MODE (bypass quota limit)? (y/n): ").strip().lower() == 'y'
            
            if choice == "1":
                run_task("story", skip_quota=test_mode)
            elif choice == "2":
                run_task("reel", skip_quota=test_mode)
            elif choice == "3":
                run_task("post", skip_quota=test_mode)
        elif choice == "0":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
