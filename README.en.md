# OlegSirotaBot

English summary of the current bot system for the “Oleg Sirota’s House” Discord server. The core idea is onboarding newcomers through “first words” before entering the main house.

**Key Features**
1. Onboarding:
   - assigns the newborn role on join;
   - sends a welcome message to the “first words” channel;
   - stores the first-words flag in the database;
   - “Leave the nursery” button with ownership check;
   - promotes to the member role and writes to the journal.
2. Per-user button:
   - button is tied to a specific message;
   - owner validation by `message_id`.
3. Logging:
   - simple log helper with `INFO/WARN/ERROR/DEBUG` levels.
4. Storage:
   - SQLite via `aiosqlite`;
   - single `onboarding_state` table for onboarding state.

**Project Structure**
1. `src/main.py` — bot entry point.
2. `src/cogs/onboarding.py` — onboarding events.
3. `src/views/enter_house.py` — “enter house” button.
4. `src/db/onboarding_store.py` — database access.
5. `src/utils/logs.py` — logging helper.

**Configuration**
Set the following environment variables:
1. `DISCORD_TOKEN`
2. `GUILD_ID`
3. `ROLE_NEWBORN_ID`
4. `ROLE_MEMBER_ID`
5. `CHANNEL_FIRST_WORDS_ID`
6. `CHANNEL_JOURNAL_ID`

**Run**
1. Install dependencies from `requirements.txt`.
2. Create `.env` based on `.env_example`.
3. Start the bot:
   - `py -m src.main`

**Notes**
1. Database file: `data.sqlite3`.
2. Logs are printed to stdout.
