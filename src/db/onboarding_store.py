import aiosqlite

class OnboardingStore:
    """
    Хранилище: отмечаем, что пользователь написал первое сообщение.
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
                CREATE TABLE IF NOT EXISTS first_words (
                    guild_id INTEGER NOT NULL,
                    user_id  INTEGER NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                );
            """)
            await db.commit()

    async def mark_first_words(self, guild_id: int, user_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO first_words (guild_id, user_id) VALUES (?, ?)",
                (guild_id, user_id)
            )
            await db.commit()

    async def has_first_words(self, guild_id: int, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT 1 FROM first_words WHERE guild_id=? AND user_id=?",
                (guild_id, user_id)
            )
            row = await cur.fetchone()
            return row is not None
