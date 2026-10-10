# BizNear Telegram Business Directory

A bilingual (English/Amharic) starter Telegram bot with business submissions, admin approval, category browsing, featured listing requests, and manual payment verification.

## Files
- `bot.py` — bot application
- `requirements.txt` — Python dependency

## 1. Create a Telegram bot
1. In Telegram, open **@BotFather**.
2. Send `/newbot` and follow the prompts.
3. Copy the bot token. Do not share it or commit it to GitHub.

## 2. Get your Telegram numeric user ID
1. Start your new bot and send `/id` (or use an existing trusted ID bot).
2. Copy the numeric ID. This is your admin ID.

## 3. Deploy on FadeHost
FadeHost's current Python bot flow supports GitHub deployment and environment variables.

1. Create a new GitHub repository, for example `biznear-bot`.
2. Upload `bot.py` and `requirements.txt` to the repository root.
3. On FadeHost, go to **Bots** or **Apps** → host/create a bot/app from your repository.
4. Select Python if asked.
5. Set the start command to `python bot.py` if not detected automatically.
6. Add environment variables:
   - `BOT_TOKEN` = the token from @BotFather
   - `ADMIN_IDS` = your numeric Telegram user ID, e.g. `1477997350`
7. Deploy and check the logs for `BizNear bot starting`.

**Important:** Never put your bot token in code, screenshots, public chats, or GitHub.

## 4. Database persistence
The bot stores its SQLite database at `/data/biznear.sqlite3` when `/data` exists, and next to the code when run locally. FadeHost documents `/data` as persistent storage. If you use a different host, check its persistent-volume path before accepting real customer data.

## 5. Test
1. Open your bot and send `/start`.
2. Change language to English or Amharic.
3. Submit a test business.
4. As admin, use `/pending` and approve it.
5. Browse its category from the user menu.
6. Use `/payments` to review featured payment requests.

## Commands
- `/start` — main menu
- `/help` — help
- `/cancel` — cancel a submission
- `/id` — show your numeric Telegram ID
- `/pending` — admin-only pending business submissions
- `/payments` — admin-only payment requests

## Manual payments and safety
The bot does not collect or process money. The customer submits a payment reference/note, and an admin must independently verify the money arrived in the correct account before using **Verify & feature**. The note alone is not proof of payment. Never ask for a customer's PIN, password, OTP, or full card details.

The current starter version is a prototype. Before scaling, add rate limiting, stronger moderation, backups, clear pricing/terms, privacy notice, and a reliable payment integration. Featured placement currently stays active until an admin removes it manually; there is no automatic expiry yet.
