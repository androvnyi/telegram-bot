import os
import datetime
import re
from dotenv import load_dotenv
from PIL import Image
import pytesseract
from db_AN.database_AN import SessionLocal
from models_AN.user_model_AN import User_AN
from models_AN.reminder_model_AN import ReminderSetting_AN
from scraper_AN.login_capture_AN import login_and_capture_schedule_AN
from telegram import Bot

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
TESSERACT_PATH = os.getenv("TESSERACT_PATH")  # Example: 'C:/Program Files/Tesseract-OCR/tesseract.exe'

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

bot = Bot(token=BOT_TOKEN)

def extract_times_from_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)

        # Парсимо часи, наприклад: "08:00", "10.10", "12:30"
        time_matches = re.findall(r'\b\d{1,2}[:.]\d{2}\b', text)

        parsed_times = []
        for match in time_matches:
            match = match.replace('.', ':')
            try:
                t = datetime.datetime.strptime(match, "%H:%M").time()
                parsed_times.append(t)
            except ValueError:
                continue

        return parsed_times
    except Exception as e:
        print(f"[OCR ERROR] Failed to extract times: {e}")
        return []

def parse_schedule_image_and_get_times(image_path):
    return extract_times_from_image(image_path)

def check_upcoming_classes():
    now = datetime.datetime.now()
    now_plus_10 = (now + datetime.timedelta(minutes=10)).time()
    now_plus_30 = (now + datetime.timedelta(minutes=30)).time()

    db = SessionLocal()
    users = db.query(User_AN).all()

    for user in users:
        settings = db.query(ReminderSetting_AN).filter(ReminderSetting_AN.user_id == user.id).first()
        if not settings:
            continue

        try:
            image_path = login_and_capture_schedule_AN(user.username, user.password)
            class_times = parse_schedule_image_and_get_times(image_path)
            os.remove(image_path)
        except Exception as e:
            print(f"[ERROR] Could not get schedule for {user.telegram_id}: {e}")
            continue

        for class_time in class_times:
            if settings.remind_10 and class_time == now_plus_10:
                bot.send_message(chat_id=user.telegram_id,
                                 text=f"⏰ Your class starts in 10 minutes at {class_time.strftime('%H:%M')}!")
            if settings.remind_30 and class_time == now_plus_30:
                bot.send_message(chat_id=user.telegram_id,
                                 text=f"⏰ Your class starts in 30 minutes at {class_time.strftime('%H:%M')}!")

    db.close()
