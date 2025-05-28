Accounts:

Admin:
    username: admin 
    password: 123
User:
    username: user
    password: userpassword123

Configuring Authorized Login WiFi Network:
    views.py 
        def detect_wifi_robust():
             # Default allowed networks if not specified
            if allowed_networks is None:
                allowed_networks = ['Converge_2.4GHz_Yj3u']
    login.html  
         const allowedNetworks = JSON.parse(document.getElementById('allowedNetworksData').textContent || ['Converge_2.4GHz_Yj3u']);
      
    change the allowed networks based on your preference.

Configuring the HTML Location for Selenium:
    tasks.py
	def fetch_html_data(self):
        """Fetch data from HTML file after switching to secondary network"""
        try:
            logger.info("Starting to fetch data from HTML file")
            ConnectionLog.objects.create(
                message="Starting data fetch from HTML file",
                is_success=True
            )
            
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from django.db import connection
            import os
            import pandas as pd
            import time
            
            # Define the correct path to chromedriver.exe
            driver_path = 'C:\\Users\\ADMIN\\Documents\\LaundryTeam\\LaundryApp\\bin\\chromedriver.exe'
            
            # Fallback paths in case the primary location doesn't work
            fallback_paths = [
                driver_path,
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bin', 'chromedriver.exe'),
                '/LaundryApp/bin/chromedriver.exe',
                'C:/bin/chromedriver.exe',
                'chromedriver.exe',  # If in PATH
            ]
            
            # Find the first existing driver path
            for path in fallback_paths:
                if os.path.exists(path):
                    driver_path = path
                    logger.info(f"Using chromedriver at: {path}")
                    break
            
            if not os.path.exists(driver_path):
                error_msg = f"Chrome driver not found at any location. Primary path tried: {driver_path}"
                logger.error(error_msg)
                ConnectionLog.objects.create(
                    message=error_msg,
                    is_success=False
                )
                return False
                
            local_html_path = os.path.abspath(
                'C:/Users/ADMIN/Documents/LaundryTeam/Reporting System.html'
                # 'http://192.168.22.23/?action=doReport&mainObj=report&from=+" + str(yday) + "%2000:00:00&to=" + str(yday) + "%2023:00:00&gml=g&reportType=br&washExtractorIds=(1,%202,%203,%204)&classificationIds=(1,%202,%204,%205,%206,%208,%209)&chemicalIds=(3,%204,%205,%206,%208,%209)&customerIds=(0)&dosingDeviceIds=(1)#reportTab'
                # Uncomment this for the site URL
                
            )


Commands needed when deploying to another computer:

    # delete old venv folder
    # Create a virtual environment
    python -m venv venv

    # Activate the virtual environment
    venv\Scripts\activate

    # Navigate to the LaundryApp directory
    cd LaundryApp

    # Install requirements
    pip install -r requirements.txt

    # Apply any pending migrations
    python manage.py migrate

    # Start the Django server
    python manage.py runserver

    http://127.0.0.1:8000/

Command and steps to run in Raspberry Pi:
    # Transfer the project to the Raspberr Pi
    scp -r your_project_folder pi@<raspberry_pi_ip>:~/your_project_folder

    # delete old venv folder
    # Create a virtual environment
    python -m venv venv

    # Activate the virtual environment
    venv\Scripts\activate

    # Install requirements
    pip install -r requirements.txt

    # Configure Django settings.py
    ALLOWED_HOSTS = ['<raspberry_pi_ip>', 'localhost']
    STATIC_ROOT = BASE_DIR / 'staticfiles'

    # Then run this
    python manage.py collectstatic

    # Apply any pending migrations
    python manage.py migrate

    # Start the Django server
    python manage.py runserver

    http://127.0.0.1:8000/