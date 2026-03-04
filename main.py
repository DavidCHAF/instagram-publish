import os
import random
import json
from dotenv import load_dotenv

from src.browser import InstagramBrowser
from src.quota_manager import QuotaManager
from src.uploader import InstagramUploader
from src.human_behavior import randomized_sleep
from src.android_uploader import AndroidUploader

load_dotenv()

def get_random_caption():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    captions_path = os.path.join(base_dir, 'config', 'captions.txt')
    
    try:
        with open(captions_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        captions = [c.strip() for c in content.split('---') if c.strip()]
        
        if not captions:
            return "Default caption!"
            
        return random.choice(captions)
    except Exception as e:
        print(f"Error reading captions.txt: {e}")
        return "Default caption!"

def get_random_overlay():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    overlays_path = os.path.join(base_dir, 'config', 'overlays.txt')
    
    try:
        with open(overlays_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split by double newline (empty line) as defined in our file
        overlays = [o.strip() for o in content.split('\n\n') if o.strip() and not o.strip().startswith('#')]
        
        if not overlays:
            return "Test Overlay!"
            
        return random.choice(overlays)
    except Exception as e:
        print(f"Error reading overlays.txt: {e}")
        return "Test Overlay!"

def run_task(post_type: str, skip_quota: bool = False):
    print(f"--- Starting task for {post_type.upper()} ---")
    quota = QuotaManager()
    
    if not skip_quota:
        if not quota.can_publish(post_type):
            print(f"Quota reached for {post_type} today. Skipping.")
            return
        print(f"Quota check passed.")
    else:
        print(f"TEST MODE: Bypassing quota check.")
    
    caption = get_random_caption()

    if post_type == "android_reel":
        print("\n[Android Emulator Upload]")
        print("Note: The script will select the VERY FIRST (newest) video from your LDPlayer Gallery.")
        overlay_text = get_random_overlay()
        print(f"Selected random TEXT OVERLAY from config: '{overlay_text}'")
        
        uploader = AndroidUploader()
        try:
             uploader.upload_reel(video_path_not_used="", caption_overlay=overlay_text, post_description=caption)
             print("Successfully uploaded Android reel!")
        except Exception as e:
             print(f"Error during Android upload: {e}")
             import traceback
             traceback.print_exc()
             return
    elif post_type == "android_story":
        print("\n[Android Emulator Story Upload]")
        uploader = AndroidUploader()
        try:
             uploader.upload_story()
             print("Successfully uploaded Android story!")
        except Exception as e:
             print(f"Error during Android upload: {e}")
             import traceback
             traceback.print_exc()
             return
    else:
        print("Initializing browser...")
        is_mobile = (post_type == "story")
        browser = InstagramBrowser(headless=False, mobile_emulation=is_mobile)
        page = browser.start()
        
        try:
            uploader = InstagramUploader(page)
            
            page.goto("https://www.instagram.com/")
            randomized_sleep(4, 7)
            
            login_input = page.locator('input[name="username"]')
            if login_input.count() > 0 or "/accounts/login/" in page.url:
                print("Detected login page.")
                print("Please log in manually in the opened browser window.")
                input("Press Enter here in the console ONCE you have successfully logged in and are on the Instagram home page...")
                browser.save_state()
                print("Saved browser state. Logged in successfully.")
                
            print("Proceeding with upload...")
            
            print(f"\nTime to pick a {post_type} file!")
            media_path = input("Please enter the ABSOLUTE path to the real image or video file on your PC: ").strip()
            
            if media_path.startswith('"') and media_path.endswith('"'):
                media_path = media_path[1:-1]
                
            if not os.path.exists(media_path):
                print("Error: The file path provided does not exist!")
                return
                
            if post_type == "post":
                uploader.publish_post(media_path, caption)
            elif post_type == "reel":
                uploader.publish_reel(media_path, caption)
            elif post_type == "story":
                uploader.publish_story(media_path)
                
            print(f"Successfully published {post_type} from Web.")
                
        except Exception as e:
            import traceback
            print(f"An error occurred: {e}")
            traceback.print_exc()
            with open("error.txt", "w", encoding="utf-8") as err_f:
                err_f.write(traceback.format_exc())
            try:
                page.screenshot(path="error_screenshot.png")
                with open("error_page.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
            except:
                pass
        finally:
            browser.close()
            print("Browser closed.")

    # Record success
    if not skip_quota:
        quota.record_publication(post_type, "uploadedmedia")
        print(f"Successfully recorded {post_type} publication in database.")

if __name__ == "__main__":
    print("Instagram Publisher Automated System")
    
    while True:
        print("\n=== MAIN MENU ===")
        print("1. Post a Web Story")
        print("2. Post a Web Reel")
        print("3. Post a Web Standard/Carousel Post")
        print("4. Post a Reel via LDPlayer ANDROID Emulation (Native Features/Aa Text)")
        print("5. Post a Story via LDPlayer ANDROID Emulation")
        print("0. Exit")
        
        choice = input("Enter your choice (0-5): ").strip()
        
        if choice in ["1", "2", "3", "4", "5"]:
            test_mode = input("Run in TEST MODE (bypass quota limit)? (y/n): ").strip().lower() == 'y'
            
            if choice == "1":
                run_task("story", skip_quota=test_mode)
            elif choice == "2":
                run_task("reel", skip_quota=test_mode)
            elif choice == "3":
                run_task("post", skip_quota=test_mode)
            elif choice == "4":
                run_task("android_reel", skip_quota=test_mode)
            elif choice == "5":
                run_task("android_story", skip_quota=test_mode)
        elif choice == "0":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
