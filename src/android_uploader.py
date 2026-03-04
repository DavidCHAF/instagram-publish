import time
import uiautomator2 as u2
import os
import random

class AndroidUploader:
    def __init__(self, adb_port_path=r"c:\tmp\ldplayer_port.txt"):
        try:
            with open(adb_port_path, "r") as f:
                self.port = f.read().strip()
            self.d = u2.connect(self.port)
            self.d.implicitly_wait(10.0) # 10s timeout
            print(f"[AndroidUploader] Connected to LDPlayer ADB on {self.port}")
        except FileNotFoundError:
            raise Exception("ADB port not found. Please run scan_adb.py first.")

    def launch_instagram(self):
        print("[AndroidUploader] Force-stopping Instagram to ensure a clean start...")
        self.d.app_stop("com.instagram.android")
        time.sleep(2)
        print("[AndroidUploader] Launching Instagram App...")
        self.d.app_start("com.instagram.android")
        # Ensure we are fully loaded on home screen
        time.sleep(10)
        
    def upload_reel(self, video_path_not_used, caption_overlay, post_description):
        """
        In LDPlayer, the files are already in the Gallery. We just pick the newest (first) one.
        We add the `caption_overlay` visually onto the video playing.
        We write `post_description` into the actual post caption bounding box.
        """
        
        self.launch_instagram()
        
        # 1. Open Camera/Gallery by swiping right on the Home tab
        print("[AndroidUploader] Swiping from left to right to open Camera/Gallery...")
        camera_opened = False
        for attempt in range(4):
            # Explicit drag from left edge to right edge
            self.d.swipe(10, 600, 700, 600, 0.1)
            time.sleep(2)
            # Verify if camera is open by looking for REEL tab or Gallery button
            if self.d(description="REEL").exists or self.d(text="REEL").exists or self.d(descriptionMatches="(?i)gallery").exists:
                print("[AndroidUploader] Successfully slid into the Camera screen!")
                camera_opened = True
                break
            print(f"[AndroidUploader] Slide attempt {attempt + 1} didn't trigger camera. Retrying...")
            
        if not camera_opened:
            print("[AndroidUploader] Warning: Could not verify if Camera opened. Proceeding anyway...")
        time.sleep(1)
        
        # 2. Switch to REEL tab
        print("[AndroidUploader] Switching to REEL mode...")
        if self.d(description="REEL").exists:
            self.d(description="REEL").click()
        elif self.d(text="REEL").exists:
            self.d(text="REEL").click()
        time.sleep(2)
        
        # 3. Open Gallery 
        print("[AndroidUploader] Opening Gallery...")
        if self.d(descriptionMatches="(?i)gallery").exists:
            self.d(descriptionMatches="(?i)gallery").click()
        time.sleep(3)
        
        # 3b. Switch to specific folder named 'reels'
        print("[AndroidUploader] Looking for custom 'reels' folder...")
        if self.d(resourceId="com.instagram.android:id/gallery_folder_menu_tv").exists:
            self.d(resourceId="com.instagram.android:id/gallery_folder_menu_tv").click()
            time.sleep(2)
            
            print("[AndroidUploader] Checking for 'All Albums' / 'All folders' within dropdown...")
            # Often it's "All Albums" or similar, or just scrolling is enough.
            if self.d(textMatches="(?i)all albums").exists:
                print("[AndroidUploader] Selected 'All Albums'.")
                self.d(textMatches="(?i)all albums").click()
                time.sleep(2)
            
            if self.d(textMatches="(?i)reels").exists:
                print("[AndroidUploader] Found 'reels' folder! Selecting it...")
                self.d(textMatches="(?i)reels").click()
                time.sleep(3)
            else:
                print("[AndroidUploader] scrolling to find 'reels' folder...")
                self.d.swipe_ext('up', scale=0.5)
                time.sleep(2)
                if self.d(textMatches="(?i)reels").exists:
                    print("[AndroidUploader] Found 'reels' folder! Selecting it...")
                    self.d(textMatches="(?i)reels").click()
                    time.sleep(3)
                else:
                    print("[AndroidUploader] 'reels' folder NOT found in the list. Canceling folder selection.")
                    self.d.press("back")
                    time.sleep(1)
        else:
            print("[AndroidUploader] Could not find the folder dropdown menu.")
        
        # 4. Randomly pick a video by scrolling 0 to 3 times, then picking a random grid coordinate
        scrolls = random.randint(0, 3)
        if scrolls > 0:
            print(f"[AndroidUploader] Scrolling gallery {scrolls} times to dive into older videos...")
            for _ in range(scrolls):
                self.d.swipe_ext('up', scale=0.6)
                time.sleep(1.5)
                
        # Define approximate click coordinates for the 3x3 grid
        if scrolls > 0:
            # If scrolled, the top-left slot is definitely a video, not the camera tool
            media_coords = [
                (120, 500), (360, 500), (600, 500),
                (120, 850), (360, 850), (600, 850),
                (120, 1150), (360, 1150), (600, 1150)
            ]
        else:
            # Top-left is the Camera, so we skip it to avoid launching camera mode
            media_coords = [
                (360, 542), (600, 542),
                (120, 960), (360, 960), (600, 960)
            ]
            
        target_coord = random.choice(media_coords)
        print(f"[AndroidUploader] Selecting a random video at grid coordinate {target_coord}...")
        self.d.click(*target_coord)
        time.sleep(5) # Wait for editor to load media
        
        # 4b. Dismiss any "video clip" or editor tooltips/popups
        print("[AndroidUploader] Dismissing any editor tooltips or popups...")
        for btn_text in ["OK", "Ok", "Got it", "GOT IT", "Continue", "Close"]:
            if self.d(text=btn_text).exists:
                print(f"[AndroidUploader] Found popup button '{btn_text}', clicking it...")
                self.d(text=btn_text).click()
                time.sleep(1)
                
        # Tap the center of the screen once to dismiss any non-button tooltips (e.g. "Double tap to edit clip")
        self.d.click(360, 640)
        time.sleep(2)
        
        # 4c. Add a Trending Audio Track
        print("[AndroidUploader] Checking for 'Add audio' button...")
        if self.d(resourceId="com.instagram.android:id/clips_action_bar_volume_controls_button").exists:
            self.d(resourceId="com.instagram.android:id/clips_action_bar_volume_controls_button").click()
        elif self.d(description="Add audio").exists:
            self.d(description="Add audio").click()
            
        time.sleep(3)
        
        # Switch to the Trending tab
        print("[AndroidUploader] Switching to 'Trending' audio tab...")
        if self.d(text="Trending").exists:
            self.d(text="Trending").click()
            time.sleep(2)
        
        print("[AndroidUploader] Randomizing audio selection from Trending track list...")
        # Randomly scroll down to see more trending songs
        audio_scrolls = random.randint(0, 3)
        if audio_scrolls > 0:
            print(f"[AndroidUploader] Scrolling trending audios {audio_scrolls} times...")
            for _ in range(audio_scrolls):
                self.d.swipe_ext('up', scale=0.5)
                time.sleep(1.5)
                
        # Wait for the track list to load
        if self.d(resourceId="com.instagram.android:id/track_container").wait(timeout=5.0):
            # Get all track containers and filter only those that are currently visible on screen
            visible_tracks = []
            for track in self.d(resourceId="com.instagram.android:id/track_container"):
                bounds = track.info.get('bounds')
                # Check if the track is within the visible screen area (Y between 500 and 1250 is typical for the audio sheet)
                if bounds and bounds.get('top') >= 300 and bounds.get('bottom') <= 1270:
                    visible_tracks.append(track)
                    
            if len(visible_tracks) > 0:
                random_track_idx = random.randint(0, len(visible_tracks) - 1)
                selected_track = visible_tracks[random_track_idx]
                print(f"[AndroidUploader] Clicked trending track (Visible Slot #{random_track_idx + 1})")
                selected_track.click()
                time.sleep(3)
                
                # We must click the select arrow (bottom right) to confirm the track!
                print("[AndroidUploader] Clicking the 'Select' arrow to confirm audio...")
                if self.d(resourceId="com.instagram.android:id/select_button_tap_target").exists:
                    self.d(resourceId="com.instagram.android:id/select_button_tap_target").click()
                    time.sleep(3)
                    
                # If a trimmer screen appears, click "Done" in the top right
                if self.d(resourceId="com.instagram.android:id/music_editor_done_button").exists:
                    print("[AndroidUploader] Clicking 'Done' on the audio trimmer...")
                    self.d(resourceId="com.instagram.android:id/music_editor_done_button").click()
                elif self.d(resourceId="com.instagram.android:id/done_button").exists:
                    self.d(resourceId="com.instagram.android:id/done_button").click()
                elif self.d(text="Done").exists:
                    self.d(text="Done").click()
                time.sleep(2)
            else:
                print("[AndroidUploader] No tracks visible to select.")
                self.d.press("back")
                time.sleep(1)
        else:
            print("[AndroidUploader] Track list didn't load in time. Skipping audio...")
            # Dismiss audio menu just in case we are stuck
            self.d.press("back")
            time.sleep(1)
        
        # 5. Add Text Overlay (Aa button)
        print(f"[AndroidUploader] Adding Text Overlay: {caption_overlay}")
        if self.d(resourceId="com.instagram.android:id/clips_action_bar_add_text_button").exists:
            self.d(resourceId="com.instagram.android:id/clips_action_bar_add_text_button").click()
        elif self.d(description="Add text").exists:
            self.d(description="Add text").click()
        time.sleep(2)
        
        if self.d(className="android.widget.EditText").exists:
            self.d(className="android.widget.EditText").set_text(caption_overlay)
        else:
            print("[AndroidUploader] Warning: Could not find Text Overlay EditText.")
        time.sleep(2)
        
        # 6. Click Done to submit the text overlay
        if self.d(resourceId="com.instagram.android:id/done_button").exists:
            self.d(resourceId="com.instagram.android:id/done_button").click()
        elif self.d(text="Done").exists:
            self.d(text="Done").click()
        time.sleep(2)
        
        # 7. Click Next on Editor to reach Share Screen
        print("[AndroidUploader] Proceeding to Share screen...")
        if self.d(resourceId="com.instagram.android:id/clips_right_action_button").exists:
            self.d(resourceId="com.instagram.android:id/clips_right_action_button").click()
        elif self.d(text="Next").exists:
            self.d(text="Next").click()
        time.sleep(5) # Wait for share screen to fully render
        
        # 8. Add Post Description (Caption below video)
        print(f"[AndroidUploader] Adding Post Caption: {post_description}")
        if self.d(resourceId="com.instagram.android:id/caption_input_text_view").exists:
            # Tapping the text view usually opens a new EditText activity
            self.d(resourceId="com.instagram.android:id/caption_input_text_view").click()
            time.sleep(2)
            # Find the active edit text
            if self.d(className="android.widget.EditText").exists:
                 self.d(className="android.widget.EditText").set_text(post_description)
                 # Hide keyboard / go back
                 self.d.press("back")
                 time.sleep(1)
            
        # 9. Click Share
        print("[AndroidUploader] Executing Final Share...")
        if self.d(resourceId="com.instagram.android:id/share_button").exists:
            self.d(resourceId="com.instagram.android:id/share_button").click()
        elif self.d(text="Share").exists:
            self.d(text="Share").click()
            
        print("[AndroidUploader] Reel Upload Commenced! Waiting 20 seconds for Android OS to process upload and return to home screen...")
        time.sleep(20)
        
        # Press home just in case
        print("[AndroidUploader] Returning to Instagram Home feed.")
        if self.d(resourceId="com.instagram.android:id/feed_tab").exists:
             self.d(resourceId="com.instagram.android:id/feed_tab").click()
             
        return True

    def upload_story(self):
        """
        Automates pulling media from the specific 'story' folder in Gallery, adding a random GIF,
        and uploading to Instagram Stories.
        """
        self.launch_instagram()
        
        # 1. Slide into Camera
        print("[AndroidUploader] Swiping from left to right to open Camera/Gallery...")
        camera_open = False
        for attempt in range(4):
            self.d.swipe(10, 600, 700, 600, 0.1)
            time.sleep(3)
            # Verify we are on the camera page
            if self.d(description="STORY").exists or self.d(text="STORY").exists or self.d(resourceId="com.instagram.android:id/gallery_preview_button").exists:
                camera_open = True
                break
            else:
                print(f"[AndroidUploader] Slide attempt {attempt+1} didn't trigger camera. Retrying...")
                
        if not camera_open:
            raise Exception("Failed to open Instagram Camera. Device is stuck on feed.")
            
        print("[AndroidUploader] Successfully slid into the Camera screen!")
        
        # 2. Switch mode to STORY
        print("[AndroidUploader] Switching to STORY mode...")
        # Often default, but click if exists
        if self.d(description="STORY").exists:
            self.d(description="STORY").click()
        elif self.d(text="STORY").exists:
            self.d(text="STORY").click()
        time.sleep(2)
        
        # 3. Swipe up to open Gallery
        print("[AndroidUploader] Swiping up to open Gallery...")
        self.d.swipe(360, 1000, 360, 200, 0.2)
        time.sleep(3)
        
        # 4. Folder selection -> story
        print("[AndroidUploader] Looking for custom 'story' folder...")
        folder_selected = False
        if self.d(resourceId="com.instagram.android:id/gallery_folder_menu_tv").exists:
            self.d(resourceId="com.instagram.android:id/gallery_folder_menu_tv").click()
            time.sleep(2)
            
            # Since user might have it under All Albums
            print("[AndroidUploader] Checking for 'All Albums' / 'All folders' within dropdown...")
            if self.d(textMatches="(?i)All Albums|All folders").exists:
                self.d(textMatches="(?i)All Albums|All folders").click()
                print("[AndroidUploader] Selected 'All Albums'.")
                time.sleep(2)
            
            # Folder dropdown is open, look for "story"
            if self.d(textMatches="(?i)story").exists:
                print("[AndroidUploader] Found 'story' folder! Selecting it...")
                self.d(textMatches="(?i)story").click()
                folder_selected = True
                time.sleep(3)
            else:
                print("[AndroidUploader] Could not find a folder named 'story'. Picking from default gallery...")
                self.d.press("back") # Close menu
                time.sleep(1)
        
        # 5. Pick a random item
        print("[AndroidUploader] Selecting a random video/image from the grid...")
        if self.d(resourceId="com.instagram.android:id/gallery_grid_item_thumbnail").wait(timeout=5.0):
            thumbnails = self.d(resourceId="com.instagram.android:id/gallery_grid_item_thumbnail")
            if len(thumbnails) > 0:
                random_idx = random.randint(0, len(thumbnails) - 1)
                print(f"[AndroidUploader] Clicking thumbnail #{random_idx + 1}")
                thumbnails[random_idx].click()
            else:
                self.d.click(360, 630) # absolute center fallback
        else:
            self.d.click(360, 630)
            
        time.sleep(5) # Wait for editor
        
        # 6. Dismiss OK popups
        print("[AndroidUploader] Dismissing any editor tooltips or popups...")
        for btn_text in ["OK", "Ok", "Got it", "GOT IT", "Continue", "Close"]:
            if self.d(text=btn_text).exists:
                self.d(text=btn_text).click()
                time.sleep(1)
                
        # 7. Add GIF Sticker (Removed per user request)

        # 8. Share to Your Story
        print("[AndroidUploader] Proceeding to Share to Your Story...")
        if self.d(textMatches="(?i)Your story").exists:
             self.d(textMatches="(?i)Your story").click()
        else:
             self.d.click(160, 1210) # Fallback coord
             
        print("[AndroidUploader] Story Upload Commenced! Waiting 15 seconds for Android OS to process upload...")
        time.sleep(15)
        print("[AndroidUploader] Returning to Instagram Home feed.")
        if self.d(resourceId="com.instagram.android:id/feed_tab").exists:
             self.d(resourceId="com.instagram.android:id/feed_tab").click()
             
        return True
