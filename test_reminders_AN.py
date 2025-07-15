import datetime
from scheduler_AN.html_schedule_parser_AN import parse_schedule_html_AN

# Завантажити тестовий HTML
with open("test_data/sample_schedule_with_classes.html", "r", encoding="utf-8") as f:
    html = f.read()

parsed = parse_schedule_html_AN(html)

print("🧾 Parsed schedule:")
for cls in parsed:
    print(cls)

# Імітація: зараз понеділок, 07:50
fake_now = datetime.datetime.strptime("2025-05-12 07:50", "%Y-%m-%d %H:%M")
fake_weekday = fake_now.strftime("%A")

print("\n🔔 Simulated reminders:")

for cls in parsed:
    if cls["day"] != fake_weekday:
        continue

    class_time = datetime.datetime.strptime(cls["start_time"], "%H:%M").time()
    class_dt = datetime.datetime.combine(fake_now.date(), class_time)
    delta = (class_dt - fake_now).total_seconds() / 60

    if 8 <= delta <= 12:
        print(f"⏰ Reminder: 10 mins before — {cls['subject']} at {cls['start_time']}")

    if 28 <= delta <= 32:
        print(f"⏰ Reminder: 30 mins before — {cls['subject']} at {cls['start_time']}")
