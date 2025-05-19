from .base import SeleniumTestBase
from django.contrib.auth.models import User
from django.conf import settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AuthTests(SeleniumTestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test user in SQLite database
        User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_login_flow(self):
        self.selenium.get(f"{self.live_server_url}{settings.LOGIN_URL}")
        
        # Updated title check
        self.assertIn("Sign In", self.selenium.title)
        
        # Fill out and submit login form
        username = self.selenium.find_element(By.NAME, "username")
        password = self.selenium.find_element(By.NAME, "password")
        submit = self.selenium.find_element(By.XPATH, "//button[@type='submit']")
        
        username.send_keys("testuser")
        password.send_keys("testpass123")
        submit.click()
        
        # Verify successful login (URL change)
        WebDriverWait(self.selenium, settings.SELENIUM_TIMEOUT).until(
            EC.url_changes(f"{self.live_server_url}{settings.LOGIN_URL}")
        )
        self.assertNotIn(settings.LOGIN_URL, self.selenium.current_url)
