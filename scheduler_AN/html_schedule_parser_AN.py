from bs4 import BeautifulSoup
from typing import List, Dict
import re

def parse_schedule_html_AN(html_content: str) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html_content, "html.parser")
    results = []

    days_map = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday"
    }

    timetable_days = soup.find_all("timetable-day")
    for day_index, day in enumerate(timetable_days):
        entries = day.find_all("timetable-entry")
        for entry in entries:
            subject = entry.get_text(strip=True)
            time_tag = entry.find("span", {"slot": "time"})
            if not time_tag:
                continue

            time_text = time_tag.text.strip()
            match = re.match(r"(\d{1,2}:\d{2})", time_text)
            if not match:
                continue

            start_time = match.group(1)
            results.append({
                "day": days_map[day_index],
                "start_time": start_time,
                "subject": subject
            })

    return results
