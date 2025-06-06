import subprocess
import re
import time
import socket
from datetime import datetime, timedelta
from django.utils import timezone
from .models import WiFiNetwork, Schedule, ConnectionLog

import requests
import logging
import threading
from .models import MeterData

# Add these imports at the top of the file if not already present
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time

logger = logging.getLogger(__name__)

class MeterDataFetcher:
    """Class to manage fetching meter data from the API"""
    
    def __init__(self):
        self.client_id = 102
        self.api_key = "Rz4ThT0DurbK1"
        self.base_url = "https://tzcapi.azurewebsites.net/publicapi/GetConsumptions"
        self.meter_id = 2305  # Default meter ID
        self.running = False
        self.thread = None
        self.interval = 60  # Set to exactly 60 seconds as requested
        self.latest_timestamps = {}  # Track latest timestamp per meter ID
    
    def start(self):
        """Start the periodic data fetching"""
        if self.running:
            logger.info("Meter data fetcher already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        logger.info("Started meter data fetching thread")
    
    def stop(self):
        """Stop the periodic data fetching"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            logger.info("Stopped meter data fetching thread")
    
    def _run(self):
        """Run the data fetching in a loop"""
        # Load existing latest timestamps from database when starting
        self._load_latest_timestamps()
        
        while self.running:
            try:
                self.fetch_and_save_data()
            except Exception as e:
                logger.error(f"Error fetching meter data: {str(e)}", exc_info=True)
            
            # Wait for the next interval
            time.sleep(self.interval)
    
    def _load_latest_timestamps(self):
        """Load the latest timestamps for each meter ID from the database"""
        try:
            # Get the latest timestamp for each meter ID
            from django.db.models import Max
            latest_records = MeterData.objects.values('meterId').annotate(
                latest_timestamp=Max('timestamp')
            )
            
            # Store in our dictionary
            self.latest_timestamps = {
                record['meterId']: record['latest_timestamp']
                for record in latest_records
            }
            
            logger.info(f"Loaded latest timestamps for {len(self.latest_timestamps)} meters")
        except Exception as e:
            logger.error(f"Error loading latest timestamps: {str(e)}", exc_info=True)
            self.latest_timestamps = {}  # Reset to empty if there's an error
    
    def fetch_and_save_data(self):
        """Fetch data from API and save to database"""
        try:
            # Get today's date and yesterday's date for the API request
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Build the API URL
            endpoint = f"{self.base_url}/{self.client_id}/{self.meter_id}/{yesterday}/{today}"
            
            # Headers for authentication
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Log the request attempt
            logger.info(f"Fetching data from: {endpoint}")
            
            # Make the API request
            response = requests.get(endpoint, headers=headers)
            
            # Log the response status
            logger.info(f"API response status: {response.status_code}")
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code}, Response: {response.text}")
                return False
            
            response.raise_for_status()
            
            # Parse the response
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                logger.info(f"Received {len(data)} records from API")
                records_processed = 0
                records_saved = 0
                
                for item in data:
                    records_processed += 1
                    if self._save_meter_data(item):
                        records_saved += 1
                
                logger.info(f"Processed {records_processed} records, saved {records_saved} new records")
            else:
                # If response is a single reading
                if self._save_meter_data(data):
                    logger.info("Saved 1 new record from API")
                else:
                    logger.info("Record already exists or is older than stored data, skipped saving")
                
            return True
            
        except requests.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error processing meter data: {str(e)}", exc_info=True)
            return False
    
    def _save_meter_data(self, data):
        """Save a single meter data record to the database. Returns True if saved, False if skipped."""
        try:
            # Extract required fields
            meter_id = data.get('meterId')
            consumption_record_id = data.get('consumptionRecordId')
            timestamp_str = data.get('timestamp')
            value = data.get('value')
            correction_factor = data.get('correctionFactor', 1)
            
            # Log the data we're trying to process
            logger.debug(f"Processing data: meterId={meter_id}, consumptionRecordId={consumption_record_id}, timestamp={timestamp_str}")
            
            # Validate required fields
            if not meter_id or not timestamp_str or value is None:
                logger.warning(f"Skipping record with missing required fields: {data}")
                return False
            
            # Parse timestamp string to datetime
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                logger.error(f"Invalid timestamp format: {timestamp_str}")
                return False
            
            # DUPLICATE CHECK 1: Check if record already exists with this consumptionRecordId
            if consumption_record_id and MeterData.objects.filter(consumptionRecordId=consumption_record_id).exists():
                logger.debug(f"Skipping duplicate record with consumptionRecordId: {consumption_record_id}")
                return False
            
            # DUPLICATE CHECK 2: Check if a record with the same meter_id and timestamp already exists
            if MeterData.objects.filter(meterId=meter_id, timestamp=timestamp).exists():
                logger.debug(f"Skipping duplicate record with meter_id {meter_id} and timestamp {timestamp}")
                return False
            
            # It's a new record, save it
            MeterData.objects.create(
                meterId=meter_id,
                consumptionRecordId=consumption_record_id,
                timestamp=timestamp,
                value=value,
                correctionFactor=correction_factor
            )
            
            # Update our latest timestamp tracking
            self.latest_timestamps[meter_id] = timestamp
            
            logger.info(f"Saved new meter reading: {meter_id} at {timestamp} with value {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving meter data: {str(e)}", exc_info=True)
            return False

# Create a global instance
meter_data_fetcher = MeterDataFetcher()

class WiFiConnectionManager:
    def __init__(self):
        self.current_ssid = None
        self.last_verified = None

    def get_current_ssid(self):
        """Get currently connected SSID with verification"""
        try:
            # Use universal_newlines=True and specify encoding to properly handle output
            result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'],
                                  capture_output=True, 
                                  text=True, 
                                  encoding='utf-8',
                                  errors='replace',
                                  check=True)
            
            # First, check if there's any WiFi interface
            if "There is no wireless interface on the system." in result.stdout:
                logger.warning("No wireless interface detected")
                return None  # Changed from "No_Wireless_Interface"
                
            # More robust regex that handles different formats and line endings
            ssid_patterns = [
                r'SSID\s*:\s*(.*?)[\r\n]',
                r'SSID\s+:\s+(.*?)[\r\n]',
                r'Profile\s*:\s*(.*?)[\r\n]'
            ]
            
            for pattern in ssid_patterns:
                match = re.search(pattern, result.stdout)
                if match and match.group(1).strip():
                    self.current_ssid = match.group(1).strip()
                    self.last_verified = timezone.now()
                    logger.info(f"Detected SSID: '{self.current_ssid}'")
                    return self.current_ssid
                    
            # If no match is found, try using an alternative approach
            try:
                # Try alternative command
                alt_result = subprocess.run(['netsh', 'wlan', 'show', 'state'],
                                          capture_output=True, text=True, check=True)
                match = re.search(r'SSID\s*:?\s*(.*?)[\r\n]', alt_result.stdout)
                if match and match.group(1).strip():
                    self.current_ssid = match.group(1).strip()
                    self.last_verified = timezone.now()
                    logger.info(f"Detected SSID (alt method): '{self.current_ssid}'")
                    return self.current_ssid
            except Exception as alt_error:
                logger.error(f"Alternative SSID detection failed: {str(alt_error)}")
            
            # If everything else fails, try a manual approach
            if "SSID" in result.stdout:
                # Try to extract the line containing "SSID"
                ssid_line = [line for line in result.stdout.splitlines() if "SSID" in line and "BSSID" not in line]
                if ssid_line:
                    # Extract everything after the colon
                    parts = ssid_line[0].split(':')
                    if len(parts) > 1:
                        self.current_ssid = parts[1].strip()
                        self.last_verified = timezone.now()
                        logger.info(f"Detected SSID (fallback): '{self.current_ssid}'")
                        return self.current_ssid
            
            # If we got here, couldn't extract the SSID
            logger.warning(f"Could not extract SSID from output: '{result.stdout[:200]}...'")
            return None  # Changed from "Unknown_Network"
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running netsh command: {str(e)}")
            return None  # Changed from "Command_Error"
        except Exception as e:
            logger.error(f"Unexpected error getting SSID: {str(e)}")
            return None  # Changed from "Detection_Error"

    def is_internet_available(self, timeout=3):
        """Check if internet access is available"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=timeout)
            return True
        except (socket.timeout, ConnectionError):
            return False

    def connect_to_wifi(self, ssid, password=None):
        """Connect to specified WiFi network with robust verification"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Disconnect first if needed
                current_ssid = self.get_current_ssid()
                if current_ssid:
                    subprocess.run(['netsh', 'wlan', 'disconnect'], check=True)
                    time.sleep(2)

                # Connect command
                cmd = ['netsh', 'wlan', 'connect', f'name={ssid}']
                if password:
                    cmd.extend(['keyMaterial', password])

                subprocess.run(cmd, check=True, timeout=30)

                # Enhanced verification
                if self._verify_connection(ssid):
                    self.current_ssid = ssid
                    return True

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                time.sleep(5)  # Wait before retry
                
        return False

    def _verify_connection(self, expected_ssid, max_attempts=3, delay=5):
        """Thorough connection verification"""
        for _ in range(max_attempts):
            current_ssid = self.get_current_ssid()
            if current_ssid == expected_ssid and self.is_internet_available():
                return True
            time.sleep(delay)
        return False

    def log_message(self, message, is_success=False):
        """Log a message to the database"""
        ConnectionLog.objects.create(message=message, is_success=is_success)

def check_and_switch_wifi():
    """Check schedules and switch WiFi if needed"""
    wifi_manager = WiFiConnectionManager()
    now = timezone.now()
    current_time = now.time()
    today = now.date()

    active_schedules = Schedule.objects.filter(is_active=True)
    
    for schedule in active_schedules:
        # Check if it's time to switch to secondary
        if (current_time.hour == schedule.switch_time.hour and
                current_time.minute == schedule.switch_time.minute):

            if (not schedule.last_switch or 
                    schedule.last_switch.date() != today or
                    wifi_manager.get_current_ssid() != schedule.secondary_network.ssid):
                
                success = wifi_manager.connect_to_wifi(
                    schedule.secondary_network.ssid,
                    schedule.secondary_network.password
                )
                
                if success:
                    wifi_manager.log_message(
                        f"Switched to secondary WiFi: {schedule.secondary_network.ssid}",
                        is_success=True
                    )
                    schedule.last_switch = now
                    schedule.save()
                else:
                    wifi_manager.log_message(
                        f"Failed to switch to secondary WiFi: {schedule.secondary_network.ssid}",
                        is_success=False
                    )
                
                time.sleep(61)  # Prevent duplicate switches

        # Check if it's time to revert to primary
        elif (current_time.hour == schedule.revert_time.hour and
              current_time.minute == schedule.revert_time.minute):

            if (not schedule.last_switch or 
                    schedule.last_switch.date() != today or
                    wifi_manager.get_current_ssid() != schedule.primary_network.ssid):
                
                success = wifi_manager.connect_to_wifi(
                    schedule.primary_network.ssid,
                    schedule.primary_network.password
                )
                
                if success:
                    wifi_manager.log_message(
                        f"Reverted to primary WiFi: {schedule.primary_network.ssid}",
                        is_success=True
                    )
                    schedule.last_switch = now
                    schedule.save()
                else:
                    wifi_manager.log_message(
                        f"Failed to revert to primary WiFi: {schedule.primary_network.ssid}",
                        is_success=False
                    )
                
                time.sleep(61)  # Prevent duplicate switches

from datetime import datetime, timedelta
import time
import threading
import logging
from django.conf import settings
import schedule
import pytz
from .models import Schedule, ConnectionLog

# Configure logger
logger = logging.getLogger(__name__)

class WiFiConnectionManager:
    """Class to manage WiFi connections and detect current networks"""
    
    def __init__(self):
        # Initialize any required system resources
        pass
        
    def get_current_ssid(self):
        """Get the SSID of the currently connected WiFi network"""
        # Implementation depends on the operating system
        # Simple implementation for demo/placeholder
        import subprocess
        import platform
        import re
        
        os_name = platform.system()
        
        if os_name == "Windows":
            try:
                output = subprocess.check_output(
                    ['netsh', 'wlan', 'show', 'interfaces'],
                    universal_newlines=True
                )
                ssid_match = re.search(r'SSID\s+:\s+(.*)\r', output)
                if ssid_match:
                    return ssid_match.group(1).strip()
                return None
            except Exception as e:
                logger.error(f"Error getting current SSID: {str(e)}")
                return None
        # Add support for other operating systems as needed
        return "Unknown"
    
    def connect_to_network(self, ssid, password=None):
        """Connect to the specified WiFi network"""
        # Implementation depends on the operating system
        import subprocess
        import platform
        
        os_name = platform.system()
        success = False
        error_msg = ""
        
        try:
            if os_name == "Windows":
                # For Windows, we use netsh command
                cmd = ['netsh', 'wlan', 'connect', f'name={ssid}']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    success = True
                else:
                    error_msg = result.stderr or "Failed to connect to network"
            # Add handling for other operating systems here
            
            # Log the attempt
            if success:
                logger.info(f"Successfully connected to WiFi: {ssid}")
                return True, "Connected successfully"
            else:
                logger.error(f"Failed to connect to WiFi: {ssid}. Error: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"Exception connecting to WiFi: {str(e)}")
            return False, str(e)


class ScheduleManager:
    """Manager for WiFi network switching schedules"""
    
    def __init__(self):
        self.connection_manager = WiFiConnectionManager()
        self.scheduler = schedule.Scheduler()
        self.running = False
        self.thread = None
        self.active_schedules = {}
        self.timezone = pytz.timezone(settings.TIME_ZONE)
        
    def add_schedule(self, db_schedule):
        """Add a schedule from database model to the scheduler"""
        schedule_id = db_schedule.id
        
        # Clear any existing jobs for this schedule
        if schedule_id in self.active_schedules:
            self.remove_schedule(schedule_id)
        
        # Parse times from the database schedule
        switch_time = db_schedule.switch_time
        revert_time = db_schedule.revert_time
        
        # Add the switch job
        switch_job = self.scheduler.every().day.at(switch_time).do(
            self.switch_network,
            schedule_id=schedule_id,
            ssid=db_schedule.secondary_network.ssid,
            is_secondary=True
        )
        
        # Add the revert job
        revert_job = self.scheduler.every().day.at(revert_time).do(
            self.switch_network,
            schedule_id=schedule_id,
            ssid=db_schedule.primary_network.ssid,
            is_secondary=False
        )
        
        # Store the jobs
        self.active_schedules[schedule_id] = {
            'db_schedule': db_schedule,
            'switch_job': switch_job,
            'revert_job': revert_job,
        }
        
        logger.info(f"Added schedule {schedule_id}: {db_schedule.primary_network.ssid} ↔ {db_schedule.secondary_network.ssid}")
        logger.info(f"  - Switch to secondary at {switch_time}")
        logger.info(f"  - Revert to primary at {revert_time}")
        
        # Make sure the scheduler is running
        self.ensure_running()
        
        return True
    
    def remove_schedule(self, schedule_id):
        """Remove a schedule from the scheduler"""
        if schedule_id in self.active_schedules:
            # Get the jobs
            schedule_data = self.active_schedules[schedule_id]
            switch_job = schedule_data.get('switch_job')
            revert_job = schedule_data.get('revert_job')
            
            # Cancel the jobs
            if switch_job:
                self.scheduler.cancel_job(switch_job)
            if revert_job:
                self.scheduler.cancel_job(revert_job)
                
            # Remove from active schedules
            del self.active_schedules[schedule_id]
            
            logger.info(f"Removed schedule {schedule_id}")
            return True
        
        return False
    
    def switch_network(self, schedule_id, ssid, is_secondary=False):
        """Switch to the specified network as part of a schedule"""
        logger.info(f"Schedule {schedule_id}: Preparing to switch to {'secondary' if is_secondary else 'primary'} network: {ssid}")
        
        # Find the db_schedule object
        schedule_data = self.active_schedules.get(schedule_id)
        if not schedule_data:
            logger.error(f"Schedule {schedule_id} not found in active schedules")
            return False
        
        db_schedule = schedule_data.get('db_schedule')
        if not db_schedule:
            logger.error(f"Database schedule object not found for schedule {schedule_id}")
            return False
        
        # Log that we're starting the switch process
        network_type = "secondary" if is_secondary else "primary"
        pre_log_message = f"Preparing to switch to {network_type} network: {ssid} (waiting 10 seconds)"
        ConnectionLog.objects.create(
            message=pre_log_message,
            is_success=True
        )
        logger.info(pre_log_message)
        
        # Delay for 10 seconds before switching
        logger.info(f"Waiting 10 seconds before switching to {ssid}...")
        time.sleep(10)
        
        # Switch network
        success, message = self.connection_manager.connect_to_network(ssid)
        
        # Log the switch attempt
        if success:
            log_message = f"Switched to {network_type} network: {ssid}"
            ConnectionLog.objects.create(
                message=log_message,
                is_success=True
            )
            logger.info(log_message)
            
            # If switching to secondary network, fetch HTML data
            if is_secondary and success:
                self.fetch_html_data()
        else:
            log_message = f"Failed to switch to {network_type} network {ssid}: {message}"
            ConnectionLog.objects.create(
                message=log_message,
                is_success=False
            )
            logger.error(log_message)
        
        return success
    
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
            
            if not os.path.exists(local_html_path):
                error_msg = f"HTML file not found at {local_html_path}"
                logger.error(error_msg)
                ConnectionLog.objects.create(
                    message=error_msg,
                    is_success=False
                )
                return False
            
            html_url = f"file:///{local_html_path.replace(os.sep, '/')}"
            
            # Start Selenium browser with headless option
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless")  # Run browser in background
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                service = Service(executable_path=driver_path)
                browser = webdriver.Chrome(service=service, options=chrome_options)
                
                logger.info(f"Browser initialized with driver at: {driver_path}")
                browser.get(html_url)
                time.sleep(5)  # Let the page fully load
                
                # Extract table using pandas
                tables = pd.read_html(browser.page_source)
                browser.quit()
            except Exception as browser_error:
                error_msg = f"Error opening HTML with browser: {str(browser_error)}"
                logger.error(error_msg, exc_info=True)
                ConnectionLog.objects.create(
                    message=error_msg,
                    is_success=False
                )
                return False
            
            if not tables:
                error_msg = "No table found in HTML report"
                logger.error(error_msg)
                ConnectionLog.objects.create(
                    message=error_msg,
                    is_success=False
                )
                return False
                
            df = tables[0]  # Use first table only
            logger.info(f"Successfully read HTML file. Found {len(df)} rows in table")
            
            # Check for expected column names from the new HTML format
            expected_columns = [
                'Batch id', 'Time', 'Duration', 'Alarms', 'Machine', 'Classification', 
                'Triggers', 'Device', 'ABP Cost', 'Dosage Cost', 'Weight', 'Dosings', 'pH', 
                'Temp.', 'Dis. Temp. Range', 'Customer'
            ]
            
            # Check if important columns exist
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                error_msg = f"Missing columns in HTML: {', '.join(missing_columns)}"
                logger.error(error_msg)
                ConnectionLog.objects.create(
                    message=error_msg,
                    is_success=False
                )
                return False
            
            # Import LaundryData model
            from .models import LaundryData
            
            # Track counts for logging
            records_added = 0
            records_skipped = 0
            
            # Get existing batch IDs to avoid duplicates
            existing_batch_ids = set(LaundryData.objects.values_list('batch_id', flat=True))
            
            # Process each row
            for _, row in df.iterrows():
                batch_id = row.get('Batch id')
                
                # Skip if already exists
                if batch_id in existing_batch_ids:
                    records_skipped += 1
                    continue
                
                try:
                    # Parse Time field if it's a datetime string
                    time_value = row.get('Time')
                    
                    # Create new record in database mapping columns to model fields
                    LaundryData.objects.create(
                        batch_id=batch_id,
                        time=time_value,
                        duration=row.get('Duration'),
                        alarms=row.get('Alarms'),
                        machine=row.get('Machine'),
                        classification=row.get('Classification'),
                        triggers=row.get('Triggers'),
                        device=row.get('Device'),
                        abp_cost=row.get('ABP Cost'),
                        dosage_cost=row.get('Dosage Cost'),
                        weight=row.get('Weight'),
                        dosings=row.get('Dosings'),
                        ph=row.get('pH'),
                        temperature=row.get('Temp.'),
                        temperature_range=row.get('Dis. Temp. Range'),
                        customer=row.get('Customer')
                    )
                    records_added += 1
                    existing_batch_ids.add(batch_id)
                except Exception as row_error:
                    logger.error(f"Error adding row with batch ID {batch_id}: {str(row_error)}")
            
            success_message = f"Imported {records_added} laundry records from HTML ({records_skipped} skipped as duplicates)"
            logger.info(success_message)
            ConnectionLog.objects.create(
                message=success_message,
                is_success=True
            )
            return True
                
        except Exception as e:
            error_msg = f"Error fetching HTML data: {str(e)}"
            logger.error(error_msg, exc_info=True)
            ConnectionLog.objects.create(
                message=error_msg,
                is_success=False
            )
            return False

    def ensure_running(self):
        """Make sure the scheduler is running in its own thread"""
        if not self.running or not self.thread or not self.thread.is_alive():
            self.start()
    
    def start(self):
        """Start the scheduler in its own thread"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler)
        self.thread.daemon = True  # Thread will exit when main thread exits
        self.thread.start()
        logger.info("Schedule manager started")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            # Let the thread exit naturally
            self.thread.join(timeout=5.0)
            self.thread = None
        logger.info("Schedule manager stopped")
    
    def _run_scheduler(self):
        """Run the scheduler (called in thread)"""
        while self.running:
            self.scheduler.run_pending()
            time.sleep(1)
    
    def load_active_schedules(self):
        """Load all active schedules from the database"""
        active_schedules = Schedule.objects.filter(is_active=True)
        
        if active_schedules.exists():
            logger.info(f"Loading {active_schedules.count()} active schedules from database")
            for db_schedule in active_schedules:
                self.add_schedule(db_schedule)
        else:
            logger.info("No active schedules found in database")
    
    def get_status(self):
        """Get the current status of all schedules"""
        return {
            'active': bool(self.active_schedules),
            'count': len(self.active_schedules),
            'schedules': list(self.active_schedules.keys())
        }


# Create a global instance of the schedule manager
wifi_schedule_manager = ScheduleManager()

# Function to initialize the schedule manager
def initialize_schedule_manager():
    """Initialize the schedule manager and load active schedules"""
    logger.info("Initializing WiFi schedule manager")
    wifi_schedule_manager.load_active_schedules()
    logger.info("WiFi schedule manager initialized")

# Meter Data Fetcher as a background thread class
class MeterDataFetcher:
    def __init__(self):
        self.running = False
        self.thread = None
        self.interval = 60  # Default 60 seconds
        
    def _fetch_data(self):
        """The actual fetching function that runs in the background"""
        logger.info("Starting meter data fetching loop")
        while self.running:
            try:
                # This is where you'd put the actual meter data fetching logic
                logger.debug("Fetching meter data...")
                # Your data fetching code here
                
                # Sleep for the configured interval
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in meter data fetcher: {str(e)}")
                time.sleep(10)  # Sleep for a shorter interval on error
        
        logger.info("Meter data fetching loop ended")
                
    def start(self):
        """Start the meter data fetcher in a background thread"""
        if self.running:
            logger.info("Meter data fetcher already running")
            return
            
        logger.info("Starting meter data fetcher")
        self.running = True
        self.thread = threading.Thread(target=self._fetch_data)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        """Stop the meter data fetcher"""
        if not self.running:
            return
            
        logger.info("Stopping meter data fetcher")
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.thread = None

# Create a global instance
meter_data_fetcher = MeterDataFetcher()
