from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service  # ✅ Required for Selenium 4+
from django.conf import settings
import os

class SeleniumTestBase(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        
        if settings.CHROMEDRIVER_OPTIONS.get('headless'):
            chrome_options.add_argument("--headless")
        if settings.CHROMEDRIVER_OPTIONS.get('no_sandbox'):
            chrome_options.add_argument("--no-sandbox")
        if settings.CHROMEDRIVER_OPTIONS.get('disable_dev_shm_usage'):
            chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Windows-specific path handling
        chromedriver_path = os.path.normpath(settings.CHROMEDRIVER_PATH)

        # ✅ Use Service object instead of deprecated executable_path
        service = Service(executable_path=chromedriver_path)
        cls.selenium = webdriver.Chrome(service=service, options=chrome_options)

        cls.selenium.implicitly_wait(settings.SELENIUM_TIMEOUT)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()
