import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    token: str
    guild_id: int
    role_newborn_id: int
    role_member_id: int
    channel_first_words_id: int
    channel_journal_id: int

def load_config() -> Config:
    return Config(
        token=os.getenv("DISCORD_TOKEN"),
        guild_id=int(os.getenv("GUILD_ID")),
        role_newborn_id=int(os.getenv("ROLE_NEWBORN_ID")),
        role_member_id=int(os.getenv("ROLE_MEMBER_ID")),
        channel_first_words_id=int(os.getenv("CHANNEL_FIRST_WORDS_ID")),
        channel_journal_id=int(os.getenv("CHANNEL_JOURNAL_ID")),
    )
