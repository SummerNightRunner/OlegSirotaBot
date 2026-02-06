import aiosqlite
from datetime import datetime

class OnboardingStore:
    """
    Хранилище: отметки о первом сообщении, а также связь кнопки и юзера
    SQLite выбран потому что:
    - без сервера
    - хранит данные между перезапусками
    """

    def __init__(self, db_path: str = "data.sqlite3"):
        self.db_path = db_path

    async def init(self) -> None:
        # создаём таблицу, если её нет
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS onboarding_state (
                    guild_id    INTEGER NOT NULL,
                    user_id     INTEGER NOT NULL,
                    message_id  INTEGER DEFAULT NULL,
                    first_words BOOL DEFAULT FALSE,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id)
                );
            """)

            await db.commit()

    async def mark_onboarding_state(self, guild_id: int, user_id: int, message_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO onboarding_state (guild_id, user_id, message_id, created_at) VALUES (?, ?, ?, ?) ON CONFLICT(guild_id, user_id) DO UPDATE SET message_id = excluded.message_id, created_at = excluded.created_at",
                (guild_id, user_id, message_id, datetime.utcnow())
            )
            await db.commit()
    
    async def mark_first_words(self, guild_id: int, user_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE onboarding_state SET first_words = TRUE WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            await db.commit()

    async def get_user_by_message(self, guild_id: int, message_id: int) -> int | None:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT user_id FROM onboarding_state WHERE guild_id = ? AND message_id = ?",
                (guild_id, message_id)
            )
            row = await cur.fetchone()
            return row[0] if row else None

    async def has_first_words(self, guild_id: int, user_id: int) -> bool | None:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT first_words FROM onboarding_state WHERE guild_id=? AND user_id=?",
                (guild_id, user_id)
            )
            row = await cur.fetchone()
            return row[0] if row else None

    async def delete_onboarding_state(self, guild_id: int, user_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM onboarding_state WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id)
            )
            await db.commit()