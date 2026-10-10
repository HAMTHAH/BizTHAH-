import os
import sqlite3
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)
log = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
# FadeHost documents /data as persistent storage. Locally, use the project folder.
DATA_DIR = Path("/data") if Path("/data").exists() else Path(__file__).resolve().parent
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "biznear.sqlite3"

TEXT = {
    "en": {
        "welcome": "Welcome to BizTHAH!\nFind local businesses or submit your own listing.",
        "browse": "Browse businesses",
        "submit": "Submit my business",
        "language": "Language",
        "help": "Use the buttons below or /start to return to the menu.",
        "choose_category": "Choose a category:",
        "no_listings": "No approved businesses in this category yet. Please check again later.",
        "ask_name": "What is your business name?",
        "ask_category": "Send one category: Shop, Food, Furniture, Electronics, Clothing, Grocery, Education, Beauty, Health, Real Estate, Home Services, Repair, Transport, Professional Services, Other.",
        "ask_contact": "Send a public contact method (phone, @username, or website). Do not send passwords or private information.",
        "ask_description": "Write a short description of your business.",
        "submitted": "Thanks! Your listing was submitted for admin review. It will not appear publicly until approved.",
        "cancelled": "Cancelled. Use /start to begin again.",
        "request_feature": "Request featured placement",
        "feature_info": "Featured placement is a paid promotion. Contact the admin for the current price and payment instructions. After paying, submit your payment reference using the button below. Your listing will only be featured after the admin verifies payment.",
        "send_reference": "Send the payment reference or a short note for the admin. Do not send PINs, passwords, or full card details.",
        "reference_saved": "Your request was sent to the admin for manual verification. This is NOT a payment confirmation.",
        "admin_only": "This command is for the bot admin only.",
        "pending": "Pending business submissions",
        "none_pending": "No pending submissions.",
        "approved": "Business approved.",
        "rejected": "Business rejected.",
        "payment_pending": "Pending featured-payment requests",
        "none_payments": "No pending payment requests.",
        "payment_approved": "Payment verified and listing featured.",
        "payment_rejected": "Payment request rejected.",
        "not_found": "That item was not found or is no longer pending.",
        "unknown": "I didn't understand that. Use /start to open the menu.",
        "new_submission_admin": "New business submission #{id}\nName: {name}\nCategory: {category}\nContact: {contact}\nDescription: {description}\nUser ID: {user_id}",
        "new_payment_admin": "Featured payment request #{id}\nBusiness: {name}\nPayment reference/note: {reference}\nUser ID: {user_id}\nVerify payment outside Telegram before approving.",
        "listing": "{name}\nCategory: {category}\nContact: {contact}\n{description}",
        "back": "Back to menu",
        "admin_help": "Admin commands:\n/pending - review business submissions\n/payments - review featured-payment requests\n/businesses - manage listings and remove businesses\nUse the buttons under each item.",
    },
    "am": {
        "welcome": "ወደ BizTHAH እንኳን በደህና መጡ!\nአካባቢያዊ ንግዶችን ይፈልጉ ወይም የእርስዎን ንግድ ያስገቡ።",
        "browse": "ንግዶችን ይመልከቱ",
        "submit": "ንግዴን አስገባ",
        "language": "ቋንቋ",
        "help": "ከታች ያሉትን ቁልፎች ይጠቀሙ ወይም /start ይጫኑ።",
        "choose_category": "ምድብ ይምረጡ፦",
        "no_listings": "በዚህ ምድብ የተፈቀዱ ንግዶች ገና የሉም።",
        "ask_name": "የንግድዎ ስም ምንድነው?",
        "ask_category": "ምድብ ይላኩ፦ Shop, Food, Furniture, Electronics, Clothing, Grocery, Education, Beauty, Health, Real Estate, Home Services, Repair, Transport, Professional Services, Other።",
        "ask_contact": "ለህዝብ የሚታይ የመገናኛ መንገድ ይላኩ (ስልክ፣ @username ወይም ድረ-ገጽ)። የይለፍ ቃል አይላኩ።",
        "ask_description": "ስለ ንግድዎ አጭር መግለጫ ይጻፉ።",
        "submitted": "እናመሰግናለን! ንግድዎ ለአስተዳዳሪ ግምገማ ተልኳል። እስኪፈቀድ ድረስ ለህዝብ አይታይም።",
        "cancelled": "ተሰርዟል። እንደገና ለመጀመር /start ይጠቀሙ።",
        "choose_category": "ምድብ ይምረጡ፦",
        "request_feature": "ተለይቶ እንዲታይ ጠይቅ",
        "feature_info": "ተለይቶ መታየት የሚከፈል ማስታወቂያ ነው። ዋጋና የክፍያ መመሪያ ለማግኘት አስተዳዳሪውን ያነጋግሩ። ከከፈሉ በኋላ የክፍያ ማጣቀሻ ይላኩ። አስተዳዳሪው እስኪያረጋግጥ ድረስ አይታይም።",
        "send_reference": "የክፍያ ማጣቀሻ ወይም አጭር ማስታወሻ ይላኩ። PIN፣ የይለፍ ቃል ወይም የካርድ ዝርዝር አይላኩ።",
        "reference_saved": "ጥያቄዎ ለአስተዳዳሪ ተልኳል። ይህ የክፍያ ማረጋገጫ አይደለም።",
        "admin_only": "ይህ ትእዛዝ ለአስተዳዳሪው ብቻ ነው።",
        "pending": "የሚጠብቁ የንግድ ማመልከቻዎች",
        "none_pending": "የሚጠብቅ ማመልከቻ የለም።",
        "approved": "ንግዱ ተፈቅዷል።",
        "rejected": "ንግዱ ተከልክሏል።",
        "payment_pending": "የሚጠብቁ የክፍያ ጥያቄዎች",
        "none_payments": "የሚጠብቅ የክፍያ ጥያቄ የለም።",
        "payment_approved": "ክፍያው ተረጋግጧል፤ ንግዱ ተለይቶ ይታያል።",
        "payment_rejected": "የክፍያ ጥያቄው ተከልክሏል።",
        "not_found": "ይህ ንጥል አልተገኘም ወይም ከዚህ በፊት ተስተናግዷል።",
        "unknown": "አልገባኝም። ምናሌውን ለማየት /start ይጠቀሙ።",
        "new_submission_admin": "አዲስ የንግድ ማመልከቻ #{id}\nስም: {name}\nምድብ: {category}\nመገናኛ: {contact}\nመግለጫ: {description}\nየተጠቃሚ ID: {user_id}",
        "new_payment_admin": "የተለይቶ መታየት የክፍያ ጥያቄ #{id}\nንግድ: {name}\nየክፍያ ማጣቀሻ: {reference}\nየተጠቃሚ ID: {user_id}\nከመፍቀድዎ በፊት ክፍያውን ያረጋግጡ።",
        "listing": "{name}\nምድብ: {category}\nመገናኛ: {contact}\n{description}",
        "back": "ወደ ምናሌው ተመለስ",
        "admin_help": "የአስተዳዳሪ ትእዛዞች፦\n/pending - የንግድ ማመልከቻዎችን ይመልከቱ\n/payments - የክፍያ ጥያቄዎችን ይመልከቱ\n/businesses - ንግዶችን ያስተዳድሩ ወይም ያስወግዱ",
    }
}
CATEGORIES = ["Shop", "Food", "Furniture", "Electronics", "Clothing", "Grocery", "Education", "Beauty", "Health", "Real Estate", "Home Services", "Repair", "Transport", "Professional Services", "Other"]

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            contact TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            featured INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS payment_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reference TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT NOT NULL DEFAULT 'en'
        )""")

def lang_for(user_id):
    with db() as c:
        row = c.execute("SELECT language FROM users WHERE user_id=?", (user_id,)).fetchone()
    return row["language"] if row else "en"

def set_lang(user_id, lang):
    with db() as c:
        c.execute("INSERT INTO users(user_id, language) VALUES(?, ?) ON CONFLICT(user_id) DO UPDATE SET language=excluded.language", (user_id, lang))

def t(user_id, key):
    return TEXT[lang_for(user_id)].get(key, TEXT["en"].get(key, key))

def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_menu(uid):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t(uid, "browse"), callback_data="browse")],
        [InlineKeyboardButton(t(uid, "submit"), callback_data="submit")],
        [InlineKeyboardButton(t(uid, "language"), callback_data="language")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    context.user_data.pop("flow", None)
    await update.effective_message.reply_text(t(uid, "welcome"), reply_markup=main_menu(uid))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = t(uid, "help")
    if is_admin(uid):
        msg += "\n\n" + t(uid, "admin_help")
    await update.effective_message.reply_text(msg)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    context.user_data.pop("flow", None)
    await update.effective_message.reply_text(t(uid, "cancelled"), reply_markup=main_menu(uid))

async def pending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text(t(uid, "admin_only")); return
    with db() as c:
        rows = c.execute("SELECT * FROM businesses WHERE status='pending' ORDER BY id").fetchall()
    if not rows:
        await update.effective_message.reply_text(t(uid, "none_pending")); return
    for r in rows:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("Approve", callback_data=f"approve:{r['id']}"),
            InlineKeyboardButton("Reject", callback_data=f"reject:{r['id']}")
        ]])
        await update.effective_message.reply_text(
            t(uid, "new_submission_admin").format(id=r["id"], name=r["name"], category=r["category"],
                contact=r["contact"], description=r["description"], user_id=r["user_id"]),
            reply_markup=kb
        )

async def businesses_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text(t(uid, "admin_only")); return
    with db() as c:
        rows = c.execute("SELECT * FROM businesses WHERE status IN ('approved','pending') ORDER BY id DESC LIMIT 100").fetchall()
    if not rows:
        await update.effective_message.reply_text("No active or pending business listings."); return
    await update.effective_message.reply_text("Business listings (latest 100). Press Remove to delete a listing:")
    for r in rows:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("Remove business", callback_data=f"remove:{r['id']}")
        ]])
        await update.effective_message.reply_text(
            f"#{r['id']} — {r['name']}\nCategory: {r['category']}\nStatus: {r['status']}\nContact: {r['contact']}",
            reply_markup=kb
        )


async def payments_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.effective_message.reply_text(t(uid, "admin_only")); return
    with db() as c:
        rows = c.execute("""SELECT p.*, b.name FROM payment_requests p JOIN businesses b ON b.id=p.business_id
                            WHERE p.status='pending' ORDER BY p.id""").fetchall()
    if not rows:
        await update.effective_message.reply_text(t(uid, "none_payments")); return
    for r in rows:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("Verify & feature", callback_data=f"payapprove:{r['id']}"),
            InlineKeyboardButton("Reject", callback_data=f"payreject:{r['id']}")
        ]])
        await update.effective_message.reply_text(
            t(uid, "new_payment_admin").format(id=r["id"], name=r["name"],
                reference=r["reference"], user_id=r["user_id"]), reply_markup=kb
        )

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data or ""

    if data == "language":
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("English", callback_data="lang:en"),
            InlineKeyboardButton("አማርኛ", callback_data="lang:am")
        ]])
        await q.edit_message_text("Choose your language / ቋንቋ ይምረጡ", reply_markup=kb)
        return
    if data.startswith("lang:"):
        set_lang(uid, data.split(":", 1)[1])
        await q.edit_message_text(t(uid, "welcome"), reply_markup=main_menu(uid))
        return
    if data == "home":
        context.user_data.pop("flow", None)
        await q.edit_message_text(t(uid, "welcome"), reply_markup=main_menu(uid))
        return
    if data == "browse":
        rows = InlineKeyboardMarkup([
            [InlineKeyboardButton(cat, callback_data=f"cat:{cat}") for cat in CATEGORIES[i:i+2]]
            for i in range(0, len(CATEGORIES), 2)
        ] + [[InlineKeyboardButton(t(uid, "back"), callback_data="home")]])
        await q.edit_message_text(t(uid, "choose_category"), reply_markup=rows)
        return
    if data.startswith("cat:"):
        cat = data.split(":", 1)[1]
        with db() as c:
            rows = c.execute("""SELECT * FROM businesses WHERE status='approved' AND category=?
                                ORDER BY featured DESC, id DESC LIMIT 20""", (cat,)).fetchall()
        if not rows:
            await q.edit_message_text(t(uid, "no_listings"), reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(t(uid, "back"), callback_data="browse")]]))
            return
        for r in rows:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(t(uid, "request_feature"), callback_data=f"feature:{r['id']}")]
            ])
            await q.message.reply_text(t(uid, "listing").format(name=r["name"], category=r["category"],
                contact=r["contact"], description=r["description"]), reply_markup=kb)
        await q.message.reply_text(t(uid, "back"), reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(t(uid, "back"), callback_data="browse")]]))
        return
    if data == "submit":
        context.user_data["flow"] = {"step": "name", "business": {}}
        await q.edit_message_text(t(uid, "ask_name"), reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Cancel / ሰርዝ", callback_data="home")]]))
        return
    if data.startswith("feature:"):
        bid = int(data.split(":")[1])
        with db() as c:
            row = c.execute("SELECT * FROM businesses WHERE id=? AND status='approved'", (bid,)).fetchone()
        if not row:
            await q.message.reply_text(t(uid, "not_found")); return
        context.user_data["flow"] = {"step": "payment_reference", "business_id": bid}
        await q.message.reply_text(t(uid, "feature_info") + "\n\n" + t(uid, "send_reference"))
        return

    if data.startswith(("remove:", "removeconfirm:", "removecancel:")):
        if not is_admin(uid):
            await q.answer(t(uid, "admin_only"), show_alert=True); return
        action, sid = data.split(":", 1)
        sid = int(sid)
        if action == "remove":
            with db() as c:
                row = c.execute("SELECT name FROM businesses WHERE id=? AND status IN ('approved','pending')", (sid,)).fetchone()
            if not row:
                await q.edit_message_text(t(uid, "not_found")); return
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("Yes, delete", callback_data=f"removeconfirm:{sid}"),
                InlineKeyboardButton("Cancel", callback_data=f"removecancel:{sid}")
            ]])
            await q.edit_message_text(f"Are you sure you want to permanently remove business #{sid}: {row['name']}?", reply_markup=kb)
        elif action == "removeconfirm":
            with db() as c:
                row = c.execute("SELECT name FROM businesses WHERE id=?", (sid,)).fetchone()
                if row:
                    c.execute("DELETE FROM payment_requests WHERE business_id=?", (sid,))
                    c.execute("DELETE FROM businesses WHERE id=?", (sid,))
            await q.edit_message_text(f"Business #{sid} ({row['name']}) was removed." if row else t(uid, "not_found"))
        else:
            await q.edit_message_text("Removal cancelled.")
        return

    if data.startswith(("approve:", "reject:", "payapprove:", "payreject:")):
        if not is_admin(uid):
            await q.answer(t(uid, "admin_only"), show_alert=True); return
        action, sid = data.split(":", 1)
        sid = int(sid)
        if action == "approve":
            with db() as c:
                cur = c.execute("UPDATE businesses SET status='approved' WHERE id=? AND status='pending'", (sid,))
                row = c.execute("SELECT user_id FROM businesses WHERE id=?", (sid,)).fetchone()
            if cur.rowcount:
                await q.edit_message_reply_markup(reply_markup=None)
                await q.message.reply_text(t(uid, "approved"))
                if row:
                    try: await context.bot.send_message(row["user_id"], "Your business listing has been approved.")
                    except Exception: pass
            else: await q.message.reply_text(t(uid, "not_found"))
        elif action == "reject":
            with db() as c:
                cur = c.execute("UPDATE businesses SET status='rejected' WHERE id=? AND status='pending'", (sid,))
            await q.edit_message_reply_markup(reply_markup=None)
            await q.message.reply_text(t(uid, "rejected") if cur.rowcount else t(uid, "not_found"))
        elif action == "payapprove":
            with db() as c:
                row = c.execute("SELECT * FROM payment_requests WHERE id=? AND status='pending'", (sid,)).fetchone()
                if row:
                    c.execute("UPDATE payment_requests SET status='approved' WHERE id=?", (sid,))
                    c.execute("UPDATE businesses SET featured=1 WHERE id=? AND status='approved'", (row["business_id"],))
            await q.edit_message_reply_markup(reply_markup=None)
            if row:
                await q.message.reply_text(t(uid, "payment_approved"))
                try: await context.bot.send_message(row["user_id"], "Your featured listing payment was approved and your listing is featured.")
                except Exception: pass
            else: await q.message.reply_text(t(uid, "not_found"))
        elif action == "payreject":
            with db() as c:
                cur = c.execute("UPDATE payment_requests SET status='rejected' WHERE id=? AND status='pending'", (sid,))
            await q.edit_message_reply_markup(reply_markup=None)
            await q.message.reply_text(t(uid, "payment_rejected") if cur.rowcount else t(uid, "not_found"))
        return

async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    flow = context.user_data.get("flow")
    if not flow:
        await update.effective_message.reply_text(t(uid, "unknown"), reply_markup=main_menu(uid))
        return
    value = (update.effective_message.text or "").strip()
    if not value:
        return
    if len(value) > 1000:
        await update.effective_message.reply_text("Please keep it under 1000 characters.")
        return

    if flow["step"] == "name":
        flow["business"]["name"] = value
        flow["step"] = "category"
        await update.effective_message.reply_text(t(uid, "ask_category"))
    elif flow["step"] == "category":
        # Keep category names consistent with browse buttons, even when submitted in Amharic.
        normalized = value.strip().lower()
        aliases = {
            "shop": "Shop", "shops": "Shop", "ሱቅ": "Shop",
            "food": "Food", "restaurant": "Food", "restaurants": "Food", "ምግብ": "Food",
            "furniture": "Furniture", "furnitures": "Furniture", "ሶፋ": "Furniture", "የቤት ዕቃ": "Furniture",
            "electronics": "Electronics", "electronic": "Electronics", "ኤሌክትሮኒክስ": "Electronics",
            "clothing": "Clothing", "clothes": "Clothing", "fashion": "Clothing", "ልብስ": "Clothing",
            "grocery": "Grocery", "groceries": "Grocery", "supermarket": "Grocery", "ግሮሰሪ": "Grocery",
            "education": "Education", "ትምህርት": "Education",
            "beauty": "Beauty", "ውበት": "Beauty", "salon": "Beauty",
            "health": "Health", "medical": "Health", "clinic": "Health", "ጤና": "Health",
            "real estate": "Real Estate", "property": "Real Estate", "ቤት ኪራይ": "Real Estate",
            "home services": "Home Services", "cleaning": "Home Services", "plumbing": "Home Services",
            "repair": "Repair", "ጥገና": "Repair", "transport": "Transport", "ትራንስፖርት": "Transport",
            "professional services": "Professional Services", "legal": "Professional Services", "accounting": "Professional Services",
            "other": "Other", "ሌላ": "Other"
        }
        cat = aliases.get(normalized)
        if not cat:
            await update.effective_message.reply_text(t(uid, "ask_category")); return
        flow["business"]["category"] = cat
        flow["step"] = "contact"
        await update.effective_message.reply_text(t(uid, "ask_contact"))
    elif flow["step"] == "contact":
        flow["business"]["contact"] = value
        flow["step"] = "description"
        await update.effective_message.reply_text(t(uid, "ask_description"))
    elif flow["step"] == "description":
        b = flow["business"]
        with db() as c:
            cur = c.execute("""INSERT INTO businesses(user_id,name,category,contact,description,status)
                               VALUES(?,?,?,?,?,'pending')""",
                            (uid, b["name"], b["category"], b["contact"], value))
            bid = cur.lastrowid
        context.user_data.pop("flow", None)
        await update.effective_message.reply_text(t(uid, "submitted"), reply_markup=main_menu(uid))
        for admin in ADMIN_IDS:
            try:
                await context.bot.send_message(admin, t(admin, "new_submission_admin").format(
                    id=bid, name=b["name"], category=b["category"], contact=b["contact"],
                    description=value, user_id=uid), reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Approve", callback_data=f"approve:{bid}"),
                        InlineKeyboardButton("Reject", callback_data=f"reject:{bid}")
                    ]]))
            except Exception as e:
                log.warning("Could not notify admin %s: %s", admin, e)
    elif flow["step"] == "payment_reference":
        bid = flow["business_id"]
        with db() as c:
            row = c.execute("SELECT name FROM businesses WHERE id=? AND status='approved'", (bid,)).fetchone()
            if not row:
                context.user_data.pop("flow", None)
                await update.effective_message.reply_text(t(uid, "not_found")); return
            cur = c.execute("INSERT INTO payment_requests(business_id,user_id,reference) VALUES(?,?,?)",
                            (bid, uid, value))
            pid = cur.lastrowid
        context.user_data.pop("flow", None)
        await update.effective_message.reply_text(t(uid, "reference_saved"), reply_markup=main_menu(uid))
        for admin in ADMIN_IDS:
            try:
                await context.bot.send_message(admin, t(admin, "new_payment_admin").format(
                    id=pid, name=row["name"], reference=value, user_id=uid),
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Verify & feature", callback_data=f"payapprove:{pid}"),
                        InlineKeyboardButton("Reject", callback_data=f"payreject:{pid}")
                    ]]))
            except Exception as e:
                log.warning("Could not notify admin %s: %s", admin, e)

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(f"Your Telegram user ID is: {update.effective_user.id}")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Set it in FadeHost environment variables.")
    if not ADMIN_IDS:
        raise RuntimeError("ADMIN_IDS is missing or invalid. Add your numeric Telegram user ID.")
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("id", myid))
    app.add_handler(CommandHandler("pending", pending_cmd))
    app.add_handler(CommandHandler("payments", payments_cmd))
    app.add_handler(CommandHandler("businesses", businesses_cmd))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    log.info("BizTHAH bot starting; database: %s", DB_PATH)
    app.run_polling()

if __name__ == "__main__":
    main()
