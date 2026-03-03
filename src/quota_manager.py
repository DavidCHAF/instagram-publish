import os
import sqlite3
import json
from datetime import datetime, date

class QuotaManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, 'data', 'history.sqlite')
        self.settings_path = os.path.join(base_dir, 'config', 'settings.json')
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS publications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_type TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    file_path TEXT
                )
            ''')
            conn.commit()
            
    def _get_limits(self):
        if not os.path.exists(self.settings_path):
            return {"posts": 1, "reels": 1, "stories": 1} # safe defaults
        with open(self.settings_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('daily_limits', {})
            
    def get_todays_count(self, post_type: str) -> int:
        """Returns how many items of 'post_type' were published today (local time)."""
        today_str = date.today().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # SQLite CURRENT_TIMESTAMP is UTC. We query by date. 
            # For simplicity, we just use string matching on the date part (if timestamp is saved as ISO).
            # But let's refine: Date bounds
            cursor.execute('''
                SELECT COUNT(*) FROM publications 
                WHERE post_type = ? AND date(timestamp, 'localtime') = ?
            ''', (post_type, today_str))
            count = cursor.fetchone()[0]
            return count
            
    def can_publish(self, post_type: str) -> bool:
        """Checks if we are within the limit for this post type today."""
        limits = self._get_limits()
        # Settings use plural keys (posts, reels, stories)
        plural_key = post_type + "s" if post_type in ["post", "reel"] else "stories" if post_type == "story" else post_type
        limit = limits.get(plural_key, 0)
        
        if limit <= 0:
            return False
            
        current_count = self.get_todays_count(post_type)
        return current_count < limit
        
    def record_publication(self, post_type: str, file_path: str = ""):
        """Logs a successful publication to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO publications (post_type, file_path)
                VALUES (?, ?)
            ''', (post_type, file_path))
            conn.commit()
