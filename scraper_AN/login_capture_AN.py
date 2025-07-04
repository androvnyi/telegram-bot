import os
import time
import uuid
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

load_dotenv()


def login_and_capture_schedule_AN(username_AN: str, password_AN: str) -> str:
    driver_path = os.getenv("CHROME_DRIVER_PATH")
    options = Options()
    options.add_argument('--headless=new')  # новий стабільний headless
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(
            "https://login.vistula.edu.pl/cas/login"
            "?service=https://usosweb.vistula.edu.pl/kontroler.php?_action=home/plan&plan_format=gif"
        )
        driver.find_element(By.ID, "username").send_keys(username_AN)
        driver.find_element(By.ID, "password").send_keys(password_AN)
        driver.find_element(By.NAME, "submit").click()
        time.sleep(3)

        # Перевірка чи успішно залогінилось
        if "login" in driver.current_url or "haslo" in driver.page_source.lower():
            raise Exception("Login failed. Please check credentials.")

        driver.get(
            "https://usosweb.vistula.edu.pl/kontroler.php"
            "?_action=home/plan&plan_format=gif"
        )
        time.sleep(3)

        img_element = driver.find_element(By.CSS_SELECTOR, "img[usemap='#plan_image_map']")
        img_url = img_element.get_attribute("src")

        cookies = {c['name']: c['value'] for c in driver.get_cookies()}
        headers = {'User-Agent': driver.execute_script("return navigator.userAgent;")}

        response = requests.get(img_url, cookies=cookies, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to download image, status code: {response.status_code}")

        output_filename = f"schedule_{uuid.uuid4().hex}.png"
        output_path = os.path.join("schedules", output_filename)
        os.makedirs("schedules", exist_ok=True)

        with open(output_path, "wb") as file:
            file.write(response.content)
        return output_path

    finally:
        driver.quit()
