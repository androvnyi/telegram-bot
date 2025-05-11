import os
import hashlib
import asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from db_AN.database_AN import engine, Base, SessionLocal
from models_AN.user_model_AN import User_AN
from models_AN.subscription_model_AN import Subscription_AN
from scraper_AN.login_capture_AN import login_and_capture_schedule_AN
from models_AN.reminder_model_AN import ReminderSetting_AN
from scheduler_AN.scheduler_reminders_AN import check_upcoming_classes



load_dotenv()
TELEGRAM_TOKEN_AN = os.getenv("TELEGRAM_TOKEN")
Base.metadata.create_all(bind=engine)

# Global bot instance
bot_instance = None

# Helpers
def get_user(db, telegram_id):
    return db.query(User_AN).filter(User_AN.telegram_id == telegram_id).first()

def get_subscription(db, user_id):
    return db.query(Subscription_AN).filter(Subscription_AN.user_id == user_id).first()

def build_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Login", callback_data="login")],
        [InlineKeyboardButton("📅 My Weekly Schedule", callback_data="schedule")],
        [InlineKeyboardButton("🔔 Notifications", callback_data="notifications")],
        [InlineKeyboardButton("⏰ Reminders", callback_data="reminders")],
        [InlineKeyboardButton("🚪 Logout", callback_data="logout")],
    ])

# /start
async def start_AN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome! Choose an action:",
        reply_markup=build_main_menu()
    )

# Button callbacks
async def login_query_AN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    db = SessionLocal()
    user = get_user(db, update.effective_user.id)
    db.close()
    if user:
        await update.callback_query.message.reply_text(
            "🔥 You are already logged in!",
            reply_markup=build_main_menu()
        )
    else:
        await update.callback_query.message.reply_text(
            "Please use /login <username> <password> to sign in."
        )

async def schedule_query_AN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    db = SessionLocal()
    user = get_user(db, update.effective_user.id)
    db.close()
    if not user:
        await update.callback_query.message.reply_text("Please /login first.")
        return
    await update.callback_query.message.reply_text("Fetching your weekly schedule…")
    img_path = login_and_capture_schedule_AN(user.username, user.password)
    with open(img_path, 'rb') as photo:
        await update.callback_query.message.reply_photo(photo=photo)
    os.remove(img_path)

async def notifications_query_AN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    keyboard = [
        [InlineKeyboardButton("Subscribe 🔔", callback_data="subscribe")],
        [InlineKeyboardButton("Unsubscribe 🔕", callback_data="unsubscribe")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back")],
    ]
    await update.callback_query.message.reply_text(
        "Manage notifications:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

from models_AN.subscription_model_AN import Subscription_AN
from models_AN.reminder_model_AN import ReminderSetting_AN

async def logout_query_AN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    db = SessionLocal()
    user = get_user(db, update.effective_user.id)

    if user:
        # 🔴 Видаляємо підписку (notifications)
        sub = get_subscription(db, user.id)
        if sub:
            db.delete(sub)

        # 🔴 Видаляємо налаштування нагадувань
        setting = db.query(ReminderSetting_AN).filter_by(user_id=user.id).first()
        if setting:
            db.delete(setting)

        # 🟢 Видаляємо самого користувача
        db.delete(user)
        db.commit()

        await update.callback_query.message.reply_text("✅ You have been logged out.")
    else:
        await update.callback_query.message.reply_text("⚠️ You are not logged in.")
    db.close()

async def logout_command_AN(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    user = get_user(db, update.effective_user.id)
    if user:
        db.delete(user)
        db.commit()
        await update.message.reply_text("✅ You have been logged out.")
    else:
        await update.message.reply_text("⚠️ You are not logged in.")
    db.close()


async def subscribe_AN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    db = SessionLocal()
    user = get_user(db, update.effective_user.id)
    if not user:
        await update.callback_query.message.reply_text("Please /login first.")
        db.close()
        return
    img_path = login_and_capture_schedule_AN(user.username, user.password)
    with open(img_path, 'rb') as f:
        content = f.read()
    os.remove(img_path)
    schedule_hash = hashlib.md5(content).hexdigest()
    sub = get_subscription(db, user.id)
    if sub:
        sub.schedule_hash = schedule_hash
    else:
        sub = Subscription_AN(user_id=user.id, schedule_hash=schedule_hash)
        db.add(sub)
    db.commit()
    db.close()
    await update.callback_query.message.reply_text(
        "🔔 Subscribed to schedule changes!",
        reply_markup=build_main_menu()
    )

async def unsubscribe_AN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    db = SessionLocal()
    user = get_user(db, update.effective_user.id)
    if not user:
        await update.callback_query.message.reply_text("Please /login first.")
        db.close()
        return
    sub = get_subscription(db, user.id)
    if sub:
        db.delete(sub)
        db.commit()
        await update.callback_query.message.reply_text(
            "🔕 Unsubscribed from schedule changes.",
            reply_markup=build_main_menu()
        )
    else:
        await update.callback_query.message.reply_text(
            "You are not subscribed.",
            reply_markup=build_main_menu()
        )
    db.close()

async def back_AN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Main menu:", reply_markup=build_main_menu()
    )

# Command handlers
async def login_command_AN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /login <username> <password>")
        return
    username_AN, password_AN = args
    try:
        db = SessionLocal()
        user = get_user(db, update.effective_user.id)
        if not user:
            user = User_AN(
                telegram_id=update.effective_user.id,
                username=username_AN,
                password=password_AN,
            )
            db.add(user)
        else:
            user.username = username_AN
            user.password = password_AN
        db.commit()
        db.close()
        await update.message.reply_text(
            "You have been logged in successfully!\n"
            "Press '📅 My Weekly Schedule' to fetch your schedule.",
            reply_markup=build_main_menu()
        )
    except Exception as e:
        await update.message.reply_text(f"Login failed: {e}")

async def week_command_AN(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    db = SessionLocal()
    user = get_user(db, update.effective_user.id)
    db.close()
    if not user:
        await update.message.reply_text("Please /login first.")
        return
    await update.message.reply_text("Fetching your weekly schedule…")
    img_path = login_and_capture_schedule_AN(user.username, user.password)
    with open(img_path, 'rb') as photo:
        await update.message.reply_photo(photo=photo)
    os.remove(img_path)

# Background check (no update/context)
async def check_subscriptions():
    db = SessionLocal()
    subs = db.query(Subscription_AN).all()
    for sub in subs:
        user = db.query(User_AN).get(sub.user_id)
        if not user or not user.username or not user.password:
            db.delete(sub)  # очистка сиріт
            db.commit()
            continue

        # ⛔ Пропускаємо, якщо користувача вже нема
        if not user:
            continue

        # ⛔ Пропускаємо, якщо користувач без логіна/пароля
        if not user.username or not user.password:
            continue

        try:
            img_path = login_and_capture_schedule_AN(user.username, user.password)
            with open(img_path, 'rb') as f:
                content = f.read()
            new_hash = hashlib.md5(content).hexdigest()

            if new_hash != sub.schedule_hash:
                sub.schedule_hash = new_hash
                db.commit()
                await bot_instance.send_message(
                    chat_id=user.telegram_id,
                    text=" ❗️❗️❗️Your schedule has changed! Here's the updated version:"
                )
                with open(img_path, 'rb') as photo:
                    await bot_instance.send_photo(chat_id=user.telegram_id, photo=photo)

            os.remove(img_path)
        except Exception as e:
            print(f"Error for user {user.telegram_id}: {e}")
            continue

    db.close()


async def reminders_query_AN(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.callback_query.answer()
        keyboard = [
            [InlineKeyboardButton("🔔 10 min before", callback_data="set_10")],
            [InlineKeyboardButton("🔔 30 min before", callback_data="set_30")],
            [InlineKeyboardButton("🔔 Both", callback_data="set_both")],
            [InlineKeyboardButton("❌ Disable", callback_data="set_off")],
            [InlineKeyboardButton("⬅️ Back", callback_data="back")],
        ]
        await update.callback_query.message.reply_text(
            "Choose your reminder setting:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def set_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE, r10: int, r30: int):
    db = SessionLocal()
    user = get_user(db, update.effective_user.id)
    setting = db.query(ReminderSetting_AN).filter_by(user_id=user.id).first()
    if not setting:
        setting = ReminderSetting_AN(user_id=user.id)
        db.add(setting)
    setting.remind_10 = r10
    setting.remind_30 = r30
    db.commit()
    db.close()
    await update.callback_query.answer("✅ Settings updated.")
    await update.callback_query.message.reply_text(
        "Reminder settings saved.",
        reply_markup=build_main_menu()
    )

# Спрощення
async def set_10_AN(update, context): await set_reminder(update, context, 1, 0)
async def set_30_AN(update, context): await set_reminder(update, context, 0, 1)
async def set_both_AN(update, context): await set_reminder(update, context, 1, 1)
async def set_off_AN(update, context): await set_reminder(update, context, 0, 0)


async def set_commands_AN(application):
    global bot_instance
    bot_instance = application.bot
    await bot_instance.set_my_commands([
        BotCommand("start", "Show main menu"),
        BotCommand("login", "Log in with your USOS credentials"),
        BotCommand("logout", "Log out and clear credentials"),
        BotCommand("week", "Get this week's schedule"),
    ])

if __name__ == "__main__":
    app_AN = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN_AN)
        .post_init(set_commands_AN)
        .build()
    )

    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.add_job(check_upcoming_classes, 'interval', minutes=1)
    scheduler.add_job(lambda: asyncio.create_task(check_subscriptions()), 'interval', hours=1)
    scheduler.start()

    app_AN.add_handler(CommandHandler("start", start_AN))
    app_AN.add_handler(CommandHandler("login", login_command_AN))
    app_AN.add_handler(CommandHandler("logout", logout_command_AN))
    app_AN.add_handler(CommandHandler("week", week_command_AN))
    app_AN.add_handler(CallbackQueryHandler(login_query_AN, pattern="^login$"))
    app_AN.add_handler(CallbackQueryHandler(schedule_query_AN, pattern="^schedule$"))
    app_AN.add_handler(CallbackQueryHandler(notifications_query_AN, pattern="^notifications$"))
    app_AN.add_handler(CallbackQueryHandler(logout_query_AN, pattern="^logout$"))
    app_AN.add_handler(CallbackQueryHandler(subscribe_AN, pattern="^subscribe$"))
    app_AN.add_handler(CallbackQueryHandler(unsubscribe_AN, pattern="^unsubscribe$"))
    app_AN.add_handler(CallbackQueryHandler(back_AN, pattern="^back$"))
    app_AN.add_handler(CallbackQueryHandler(reminders_query_AN, pattern="^reminders$"))
    app_AN.add_handler(CallbackQueryHandler(set_10_AN, pattern="^set_10$"))
    app_AN.add_handler(CallbackQueryHandler(set_30_AN, pattern="^set_30$"))
    app_AN.add_handler(CallbackQueryHandler(set_both_AN, pattern="^set_both$"))
    app_AN.add_handler(CallbackQueryHandler(set_off_AN, pattern="^set_off$"))

    print("Bot is up and running with scheduler...")
    app_AN.run_polling()