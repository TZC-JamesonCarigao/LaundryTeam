from django.apps import AppConfig
import threading
import time
import sys

class LaundryApplicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'LaundryApplication'
    
    def ready(self):
        """Called when the application is ready"""
        # Only initialize tasks when running the server (not during migrations)
        if 'runserver' in sys.argv and not any(arg in sys.argv for arg in ['makemigrations', 'migrate']):
            # Delay initialization to avoid loading models during app init
            def delayed_init():
                time.sleep(5)  # Wait 5 seconds to ensure app is fully loaded
                try:
                    from .tasks import initialize_schedule_manager
                    initialize_schedule_manager()
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Error initializing schedule manager: {str(e)}")
            
            # Start as a separate thread
            t = threading.Thread(target=delayed_init)
            t.daemon = True
            t.start()
