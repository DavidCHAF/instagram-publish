from playwright.sync_api import Page
from .human_behavior import randomized_sleep, human_type

class InstagramUploader:
    def __init__(self, page: Page):
        self.page = page
        
    def login(self, username, password):
        """Logs into Instagram. Only needed if no valid session cookies exist."""
        print("Navigating to Instagram login...")
        self.page.goto("https://www.instagram.com/accounts/login/")
        randomized_sleep(3, 6)
        
        # Handle potential cookies before typing
        cookie_btn = self.page.get_by_role("button", name="Decline optional cookies").or_(
            self.page.get_by_role("button", name="Allow all cookies")
        )
        if (cookie_btn.count() > 0):
            cookie_btn.first.click()
            randomized_sleep(1, 3)
            
        # Wait for username input
        self.page.wait_for_selector('input[name="username"]')
        
        # Type credentials humanly
        human_type(self.page, 'input[name="username"]', username)
        randomized_sleep(1, 2)
        human_type(self.page, 'input[name="password"]', password)
        randomized_sleep(1, 2)
        
        # Submit login
        self.page.locator('input[name="password"]').press("Enter")
        
        # Wait for navigation (either to feed or save info prompt)
        self.page.wait_for_url(lambda url: "instagram.com" in url and "login" not in url, timeout=15000)
        print("Login successful.")
        randomized_sleep(4, 8)
        
    def publish_post(self, media_path: str, caption: str):
        """
        Publishes a post (and video/reel) by interacting with the Instagram desktop web interface.
        Desktop interface is more robust for posts and reels since there are no URL redirects.
        """
        print(f"Publishing post/reel: {media_path}")
        
        # 1. Navigate to home
        self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        randomized_sleep(3, 6)
        
        print("Handling potential cookie banners...")
        cookie_btn = self.page.get_by_role("button", name="Decline optional cookies").or_(
            self.page.get_by_role("button", name="Allow all cookies")
        )
        if cookie_btn.count() > 0:
            print("Cookie banner found. Dismissing...")
            cookie_btn.first.click()
            randomized_sleep(1, 3)
            
        # 2. Open Create Modal
        print("Looking for Create button...")
        create_btn = self.page.get_by_text("Créer", exact=True).or_(
            self.page.get_by_text("Create", exact=True)
        ).or_(
            self.page.locator('svg[aria-label="Nouvelle publication"]').locator("..")
        ).or_(
            self.page.locator('svg[aria-label="New post"]').locator("..")
        ).first
        
        if create_btn.count() > 0:
            create_btn.click()
            randomized_sleep(2, 4)
        else:
            print("WARNING: Could not find Create button. Continuing to check for modal anyway.")
            
        # 3. Upload file directly by triggering file chooser
        print("Waiting for file chooser...")
        select_btn = self.page.locator('button:has-text("ordinateur")').or_(
            self.page.locator('button:has-text("computer")')
        ).or_(
            self.page.get_by_role("button", name="Sélectionner sur l'ordinateur")
        ).or_(
            self.page.get_by_role("button", name="Select from computer")
        )
        
        with self.page.expect_file_chooser() as fc_info:
            select_btn.first.click()
        
        file_chooser = fc_info.value
        file_chooser.set_files(media_path)
        print("File set in FileChooser. Waiting for next step...")
        randomized_sleep(4, 7)
        
        # 4. Click Next until Share appears
        print("Waiting for creation flow to start and clicking Next...")
        modal = self.page.locator('div[role="dialog"]').last
        
        for _ in range(5):
            # Check if Share is already visible IN THE MODAL
            share_check = modal.get_by_text("Share", exact=True).or_(
                 modal.locator('div[role="button"]:has-text("Share")')
            ).or_(
                 modal.get_by_text("Partager", exact=True)
            ).or_(
                 modal.locator('div[role="button"]:has-text("Partager")')
            )
            
            if share_check.count() > 0 and share_check.first.is_visible():
                print("Share button is now visible inside the modal!")
                break
                
            next_btn = modal.get_by_text("Next", exact=True).or_(
                 modal.locator('button:has-text("Next")')
            ).or_(
                 modal.locator('div[role="button"]:has-text("Next")')
            ).or_(
                modal.get_by_text("Suivant", exact=True)
            ).or_(
                modal.locator('div[role="button"]:has-text("Suivant")')
            )
            
            if next_btn.first.count() > 0:
                print("Clicking Next/Suivant in modal...")
                next_btn.first.click(force=True)
                randomized_sleep(3, 5)
            else:
                print("No Next button found in this iteration.")
                randomized_sleep(1, 3)
        
        # 5. Type caption
        print("Typing caption...")
        caption_area = modal.locator('div[aria-label="Write a caption..."]').or_(
             modal.locator('div[aria-label="Écrire une légende..."]')
        ).or_(
             modal.locator('textarea')
        )
        
        if caption_area.count() > 0:
            caption_area.first.click(force=True)
            randomized_sleep(1, 2)
            self.page.keyboard.type(caption)
        else:
             print("Could not find caption box, proceeding to share.")
        randomized_sleep(2, 4)
        
        # 6. Click Share
        print("Clicking Share...")
        share_btn = modal.get_by_text("Share", exact=True).or_(
             modal.locator('div[role="button"]:has-text("Share")')
        ).or_(
             modal.get_by_text("Partager", exact=True)
        ).or_(
             modal.locator('div[role="button"]:has-text("Partager")')
        )
        
        if share_btn.first.count() > 0:
            share_btn.first.click(force=True)
        else:
            print("Unable to find exact Share button inside modal! It could be different.")
        
        # 7. Wait for success notification
        print("Waiting for upload to complete (this can take up to 60s for video processing)...")
        try:
            success_marker = modal.locator('text="Your reel has been shared"').or_(
                modal.locator('text="Your post has been shared"')
            ).or_(
                modal.locator('text="Votre réel a été partagé"')
            ).or_(
                modal.locator('text="Votre publication a été partagée"')
            ).or_(
                modal.locator('img[alt="Animated checkmark"]')
            ).or_(
                modal.locator('img[alt="Coche animée"]')
            ).or_(
                modal.get_by_text("shared", exact=False)
            ).or_(
                modal.get_by_text("partagé", exact=False)
            )

            success_marker.first.wait_for(state="visible", timeout=60000) 
            print("SUCCESS: Post processing finished on Instagram servers!")
            
            # Close the modal
            print("Closing the modal window...")
            close_btn = modal.locator('svg[aria-label="Close"]').or_(
                modal.locator('svg[aria-label="Fermer"]')
            ).locator("..").first
            
            if close_btn.count() > 0:
                close_btn.click(force=True)
                randomized_sleep(2, 4)
                
        except Exception as e:
            print(f"WARNING: Wait for success indicator timed out or failed: {e}")
            self.page.wait_for_timeout(10000) # Fallback wait just in case
        
        # 8. Post Verification
        print("Verifying if the post was successfully published within the last 2 minutes...")
        self.page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        self.page.wait_for_timeout(5000)
        
        profile_link = self.page.locator('a[href^="/"][role="link"]:has(img[alt*="profile picture"])').or_(
            self.page.get_by_role("link", name="Profil")
        ).or_(
            self.page.get_by_role("link", name="Profile")
        )
        
        if profile_link.count() > 0:
            my_profile_url = profile_link.first.get_attribute("href")
            print(f"Navigating to profile: {my_profile_url}")
            self.page.goto(f"https://www.instagram.com{my_profile_url}", wait_until="domcontentloaded")
            self.page.wait_for_timeout(5000)
            
            # Look for the last post
            first_post = self.page.locator('main a[href*="/p/"], main a[href*="/reel/"]').first
            if first_post.count() > 0:
                print("Found latest post on profile grid. Clicking to check metadata...")
                first_post.click()
                self.page.wait_for_timeout(3000)
                
                time_elem = self.page.locator('time')
                if time_elem.count() > 0:
                    dt_str = time_elem.first.get_attribute("datetime")
                    if dt_str:
                        from datetime import datetime, timezone, timedelta
                        try:
                            post_time = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                            now = datetime.now(timezone.utc)
                            diff = now - post_time
                            if diff <= timedelta(minutes=2):
                                print(f"VERIFIED: Post is freshly published! (Age: {diff.total_seconds():.1f} seconds)")
                            else:
                                print(f"WARNING: The latest post is older than 2 minutes! (Age: {diff.total_seconds()/60:.1f} minutes). The upload may have failed.")
                        except ValueError:
                            print(f"Could not parse datetime string: {dt_str}")
                    else:
                        print("Could not read datetime attribute.")
                else:
                    print("Could not find <time> element to verify post age.")
            else:
                 print("WARNING: Could not see any posts in the grid!")
        else:
            print("Could not locate profile button, skipping verification.")
            
        print("Post/Reel published script sequence completed.")

    def publish_story(self, media_path: str):
        """
        Publishes a story by interacting with the Instagram mobile web interface.
        """
        print(f"Publishing story: {media_path}")
        
        self.page.goto("https://www.instagram.com/")
        randomized_sleep(4, 7)
        
        print("Handling potential cookie banners...")
        cookie_btn = self.page.get_by_role("button", name="Decline optional cookies").or_(
            self.page.get_by_role("button", name="Allow all cookies")
        )
        if cookie_btn.count() > 0:
            print("Cookie banner found. Dismissing...")
            cookie_btn.first.click()
            randomized_sleep(1, 3)

        print("Uploading media...")
        # Direct file input intercept for stories.
        file_input = self.page.locator('input[type="file"]').first
        file_input.wait_for(state="attached", timeout=15000)
        file_input.set_input_files(media_path)
        randomized_sleep(5, 8)
        
        print("Waiting for story preview to load...")
        # After choosing the file, we wait for the confirmation button
        # On French it might be 'Ajouter à votre story' or similar, we use multiple selectors
        add_btn = self.page.get_by_text("Add to your story").or_(
            self.page.locator('span:has-text("Your story")')
        ).or_(
            self.page.locator('svg[aria-label="Add to your story"]').locator("..")
        ).or_(
             self.page.locator('button:has-text("Add")')
        ).first
        
        add_btn.wait_for(state="visible", timeout=15000)
        print("Clicking Add to story button...")
        add_btn.click()
        
        print("Waiting for upload to complete...")
        randomized_sleep(8, 12)
        print("Story published successfully.")

    def publish_reel(self, media_path: str, caption: str):
        """
        Publishes a reel by interacting with the Instagram web interface.
        Since Instagram's web interface unified video uploads into the Reels format, 
        this uses the same create/style upload flow.
        """
        print(f"Publishing reel: {media_path}")
        # Call the existing post publisher which handles the file input, next, next, share steps
        self.publish_post(media_path, caption)
