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