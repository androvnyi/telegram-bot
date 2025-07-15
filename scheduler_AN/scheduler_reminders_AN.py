import datetime
from db_AN.database_AN import SessionLocal
from models_AN.user_model_AN import User_AN
from models_AN.reminder_model_AN import ReminderSetting_AN
from scraper_AN.login_capture_AN import login_and_capture_schedule_AN
from scheduler_AN.crypto_AN import decrypt_password
from telegram import Bot
import os
from scheduler_AN.html_schedule_parser_AN import parse_schedule_html_AN

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=BOT_TOKEN)

def check_upcoming_classes():
    now = datetime.datetime.now()
    weekday_today = now.strftime("%A")
    db = SessionLocal()
    users = db.query(User_AN).all()

    for user in users:
        settings = db.query(ReminderSetting_AN).filter_by(user_id=user.id).first()
        if not settings or not (settings.remind_10 or settings.remind_30):
            continue

        try:
            real_password = decrypt_password(user.password)
            html = login_and_capture_schedule_AN(user.username, real_password, return_html=True)
            parsed_classes = parse_schedule_html_AN(html)

            for cls in parsed_classes:
                if cls["day"] != weekday_today:
                    continue

                class_time = datetime.datetime.strptime(cls["start_time"], "%H:%M").time()
                class_dt = datetime.datetime.combine(now.date(), class_time)
                delta_min = (class_dt - now).total_seconds() / 60

                if settings.remind_10 and 8 <= delta_min <= 12:
                    bot.send_message(chat_id=user.telegram_id,
                                     text=f"⏰ Через 10 хв пара: {cls['subject']} ({cls['start_time']})")

                if settings.remind_30 and 28 <= delta_min <= 32:
                    bot.send_message(chat_id=user.telegram_id,
                                     text=f"⏰ Через 30 хв пара: {cls['subject']} ({cls['start_time']})")

        except Exception as e:
            print(f"[ERROR] Reminder failed for user {user.telegram_id}: {e}")
            continue

    db.close()
