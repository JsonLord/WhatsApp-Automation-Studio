import os
import time
import random
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (TimeoutException, NoSuchElementException,
                                      ElementClickInterceptedException, StaleElementReferenceException)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class WhatsAppAutomation:
    def __init__(self, config=None):
        self.config = config or {
            "delay_min": 1.0,
            "delay_max": 3.0,
            "typing_simulation": True,
            "typing_speed": 0.01,
            "randomize_order": False,
            "session_path": "whatsapp_session",
            "xpaths": {
                "message_box": '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div[1]/div[2]/div/p',
                "message_area_click": '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div[1]/div[2]',
                "send_button": '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div[2]/button',
                "chat_title": '//div[@data-testid="conversation-header-content"]//span',
                "qr_container": '//div[@data-testid="qrcode"]'
            }
        }
        self.driver = None

    def initialize_driver(self, headless=True, session_path=None):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            # Required for running in Docker
            chrome_options.add_argument("--remote-debugging-port=9222")

        session_path = session_path or self.config.get("session_path")
        if session_path:
            # Ensure session path is absolute for Docker/Headless reliability
            abs_session_path = os.path.abspath(session_path)
            chrome_options.add_argument(f"user-data-dir={abs_session_path}")

        try:
            # First try system-installed chromedriver (recommended for Docker)
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                return True
            except Exception as e:
                print(f"System chromedriver failed: {e}. Trying webdriver-manager...")
                # Fallback to webdriver-manager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                return True
        except Exception as e:
            print(f"Browser initialization failed: {str(e)}")
            return False

    def navigate_to_whatsapp(self):
        if not self.driver:
            return False
        try:
            self.driver.get("https://web.whatsapp.com/")
            return True
        except Exception as e:
            print(f"Error navigating to WhatsApp: {str(e)}")
            return False

    def get_qr_code_screenshot(self):
        if not self.driver:
            return None
        try:
            # Wait for QR code to appear
            qr_xpath = self.config["xpaths"]["qr_container"]
            qr_element = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, qr_xpath))
            )
            # Take screenshot of the QR element
            qr_screenshot = qr_element.screenshot_as_base64
            return qr_screenshot
        except Exception as e:
            print(f"Error capturing QR code: {str(e)}")
            return None

    def check_login_status(self, timeout=30):
        if not self.driver:
            return False
        try:
            # Look for the search box/chat list which indicates login success
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true" and @data-tab="3"]'))
            )
            return True
        except TimeoutException:
            return False
        except Exception as e:
            print(f"Error checking login status: {str(e)}")
            return False

    def send_message(self, message):
        if not message or not self.driver:
            return False

        try:
            # Find and click the message area
            message_area = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, self.config["xpaths"]["message_area_click"]))
            )
            message_area.click()

            # Find the text input element
            message_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, self.config["xpaths"]["message_box"]))
            )

            # Type the message
            lines = message.split("\n")
            if self.config.get("typing_simulation", True):
                for i, line in enumerate(lines):
                    for char in line:
                        message_box.send_keys(char)
                        delay = self.config.get("typing_speed", 0.01) * random.uniform(0.8, 1.2)
                        time.sleep(delay)
                    if i < len(lines) - 1:
                        message_box.send_keys(Keys.SHIFT + Keys.ENTER)
            else:
                for i, line in enumerate(lines):
                    message_box.send_keys(line)
                    if i < len(lines) - 1:
                        message_box.send_keys(Keys.SHIFT + Keys.ENTER)

            # Click send button
            send_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, self.config["xpaths"]["send_button"]))
            )
            send_button.click()

            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return False

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
