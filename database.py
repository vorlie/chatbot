import aiosqlite
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path="bot_data.db"):
        self.db_path = db_path

    async def initialize(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Table for user preferences (opt-in/opt-out)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_prefs (
                    user_id INTEGER PRIMARY KEY,
                    opt_in INTEGER DEFAULT 0
                )
            """)
            # Table for learned messages
            await db.execute("""
                CREATE TABLE IF NOT EXISTS learned_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Table for bot settings
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            # Index for faster user-based lookups
            await db.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON learned_messages(user_id)")
            # Index for timestamp if we want to fetch recent messages
            await db.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON learned_messages(timestamp)")
            await db.commit()

    async def set_opt_in(self, user_id: int, status: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO user_prefs (user_id, opt_in)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET opt_in = excluded.opt_in
            """, (user_id, 1 if status else 0))
            await db.commit()

    async def is_opted_in(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT opt_in FROM user_prefs WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return bool(row[0]) if row else False

    async def log_message(self, user_id: int, content: str):
        # Double check opt-in before logging (privacy first)
        if not await self.is_opted_in(user_id):
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO learned_messages (user_id, content)
                VALUES (?, ?)
            """, (user_id, content))
            await db.commit()

    async def get_random_learned_messages(self, limit=20):
        """Fetch random messages to provide as 'context' for the personality."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT content FROM learned_messages 
                ORDER BY RANDOM() LIMIT ?
            """, (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_stats(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Get total stats
            async with db.execute("SELECT COUNT(*) FROM user_prefs WHERE opt_in = 1") as c:
                opted_in_count = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM learned_messages") as c:
                total_messages = (await c.fetchone())[0]

            # Get top 3 contributors (returns user_id and count)
            async with db.execute("""
                SELECT user_id, COUNT(*) as msg_count 
                FROM learned_messages 
                GROUP BY user_id 
                ORDER BY msg_count DESC 
                LIMIT 3
            """) as cursor:
                top_contributors = await cursor.fetchall()
                
            return opted_in_count, total_messages, top_contributors

    async def clear_all_messages(self):
        """Delete all learned messages from the database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM learned_messages")
            await db.commit()
            logger.info("All learned messages have been cleared.")

    async def clear_messages_before(self, timestamp: str) -> int:
        """Delete messages before a specific timestamp. Returns count of deleted messages."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM learned_messages WHERE timestamp < ?", (timestamp,)) as c:
                count = (await c.fetchone())[0]
            
            await db.execute("DELETE FROM learned_messages WHERE timestamp < ?", (timestamp,))
            await db.commit()
            logger.info(f"Deleted {count} messages before {timestamp}.")
            return count

    async def clear_messages_after(self, timestamp: str) -> int:
        """Delete messages after a specific timestamp. Returns count of deleted messages."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM learned_messages WHERE timestamp > ?", (timestamp,)) as c:
                count = (await c.fetchone())[0]
            
            await db.execute("DELETE FROM learned_messages WHERE timestamp > ?", (timestamp,))
            await db.commit()
            logger.info(f"Deleted {count} messages after {timestamp}.")
            return count

    async def get_vision_enabled(self) -> bool:
        """Get whether vision processing is enabled."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT value FROM bot_settings WHERE key = 'vision_enabled'") as cursor:
                row = await cursor.fetchone()
                return bool(int(row[0])) if row else True  # Default to True

    async def set_vision_enabled(self, enabled: bool):
        """Set whether vision processing is enabled."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO bot_settings (key, value)
                VALUES ('vision_enabled', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (1 if enabled else 0,))
            await db.commit()
