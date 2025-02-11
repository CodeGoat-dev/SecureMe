# Goat - SecureMe WebServer class
# Version 1.4.7
# © (c) 2024-2025 Goat Technologies
# https://github.com/CodeGoat-dev/SecureMe
# Description:
# Provides the web server for the Goat - SecureMe firmware.

# Imports
import machine
import network
import time
import uasyncio as asyncio
import uos
import urequests
import utime
import ubinascii
from ConfigManager import ConfigManager
import utils

# WebServer class
class WebServer:
    """Provides the web server for the Goat - SecureMe firmware."""
    
    def __init__(self, ip_address="0.0.0.0", http_port=8000):
        """Constructs the class and exposes properties."""
        # Constants
        self.VERSION = "1.4.7"
        self.REPO_URL = "https://github.com/CodeGoat-dev/SecureMe"

        self.default_ip_address = "0.0.0.0"
        self.default_http_port = 8000

        self.ip_address = ip_address
        self.http_port = http_port
        self.server = None

        self.config_directory = "/config"
        self.config_file = "secureme.conf"
        self.network_config_file = "network_config.conf"

        self.detect_motion = None
        self.detect_tilt = None
        self.detect_sound = None
        self.sensor_cooldown = 10
        self.default_sensor_cooldown = 10
        self.arming_cooldown = 10
        self.default_arming_cooldown = 10
        self.pushover_app_token = None
        self.pushover_api_key = None
        self.system_status_notifications = None
        self.general_notifications = None
        self.security_code_notifications = None
        self.web_interface_notifications = None
        self.update_notifications = None
        self.web_server_http_port = 8000
        self.default_web_server_http_port = 8000
        self.admin_password = "secureme"
        self.default_admin_password = "secureme"
        self.security_code = "0000"
        self.default_security_code = "0000"
        self.security_code_min_length = 4
        self.security_code_max_length = 8
        self.enable_auto_update = None
        self.update_check_interval = None
        self.default_update_check_interval = 30
        self.enable_time_sync = None
        self.time_sync_server = "https://goatbot.org"
        self.default_time_sync_server = "https://goatbot.org"
        self.time_sync_interval = 360
        self.default_time_sync_interval = 360

        self.alert_text = None

    async def initialize(self):
        """Initializes the server by loading configuration data."""
        self.config = ConfigManager(self.config_directory, self.config_file)
        await self.config.read_async()

        self.detect_motion = self.config.get_entry("security", "detect_motion")
        if not isinstance(self.detect_motion, bool):
            self.detect_motion = True
            self.config.set_entry("security", "detect_motion", self.detect_motion)
            await self.config.write_async()
        self.detect_tilt = self.config.get_entry("security", "detect_tilt")
        if not isinstance(self.detect_tilt, bool):
            self.detect_tilt = True
            self.config.set_entry("security", "detect_tilt", self.detect_tilt)
            await self.config.write_async()
        self.detect_sound = self.config.get_entry("security", "detect_sound")
        if not isinstance(self.detect_sound, bool):
            self.detect_sound = True
            self.config.set_entry("security", "detect_sound", self.detect_sound)
            await self.config.write_async()
        self.sensor_cooldown = self.config.get_entry("security", "sensor_cooldown")
        if not isinstance(self.sensor_cooldown, int):
            self.sensor_cooldown = self.default_sensor_cooldown
            self.config.set_entry("security", "sensor_cooldown", self.sensor_cooldown)
            await self.config.write_async()
        self.arming_cooldown = self.config.get_entry("security", "arming_cooldown")
        if not isinstance(self.arming_cooldown, int):
            self.arming_cooldown = self.default_arming_cooldown
            self.config.set_entry("security", "arming_cooldown", self.arming_cooldown)
            await self.config.write_async()
        self.pushover_app_token = self.config.get_entry("pushover", "app_token")
        self.pushover_api_key = self.config.get_entry("pushover", "api_key")
        self.system_status_notifications = self.config.get_entry("pushover", "system_status_notifications")
        if not isinstance(self.system_status_notifications, bool):
            self.system_status_notifications = True
            self.config.set_entry("pushover", "system_status_notifications", self.system_status_notifications)
            await self.config.write_async()
        self.general_notifications = self.config.get_entry("pushover", "general_notifications")
        if not isinstance(self.general_notifications, bool):
            self.general_notifications = True
            self.config.set_entry("pushover", "general_notifications", self.general_notifications)
            await self.config.write_async()
        self.security_code_notifications = self.config.get_entry("pushover", "security_code_notifications")
        if not isinstance(self.security_code_notifications, bool):
            self.security_code_notifications = True
            self.config.set_entry("pushover", "security_code_notifications", self.security_code_notifications)
            await self.config.write_async()
        self.web_interface_notifications = self.config.get_entry("pushover", "web_interface_notifications")
        if not isinstance(self.web_interface_notifications, bool):
            self.web_interface_notifications = True
            self.config.set_entry("pushover", "web_interface_notifications", self.web_interface_notifications)
            await self.config.write_async()
        self.update_notifications = self.config.get_entry("pushover", "update_notifications")
        if not isinstance(self.update_notifications, bool):
            self.update_notifications = True
            self.config.set_entry("pushover", "update_notifications", self.update_notifications)
            await self.config.write_async()
        self.security_code = self.config.get_entry("security", "security_code")
        if not isinstance(self.security_code, str):
            self.security_code = self.default_security_code
            self.config.set_entry("security", "security_code", self.security_code)
            await self.config.write_async()
        self.web_server_http_port = self.config.get_entry("server", "http_port")
        if not isinstance(self.web_server_http_port, int):
            self.web_server_http_port = self.default_web_server_http_port
            self.config.set_entry("server", "http_port", self.web_server_http_port)
            await self.config.write_async()
        self.admin_password = self.config.get_entry("server", "admin_password")
        if not isinstance(self.admin_password, str):
            self.admin_password = self.default_admin_password
            self.config.set_entry("server", "admin_password", self.admin_password)
            await self.config.write_async()
        self.enable_auto_update = self.config.get_entry("update", "enable_auto_update")
        if not isinstance(self.enable_auto_update, bool):
            self.enable_auto_update = True
            self.config.set_entry("update", "enable_auto_update", self.enable_auto_update)
            await self.config.write_async()
        self.update_check_interval = self.config.get_entry("update", "update_check_interval")
        if not isinstance(self.update_check_interval, int):
            self.update_check_interval = self.default_update_check_interval
            self.config.set_entry("update", "update_check_interval", self.update_check_interval)
            await self.config.write_async()
        self.enable_time_sync = self.config.get_entry("time", "enable_time_sync")
        if not isinstance(self.enable_time_sync, bool):
            self.enable_time_sync = True
            self.config.set_entry("time", "enable_time_sync", self.enable_time_sync)
            await self.config.write_async()
        self.time_sync_server = self.config.get_entry("time", "time_sync_server")
        if not isinstance(self.time_sync_server, str):
            self.time_sync_server = self.default_time_sync_server
            self.config.set_entry("time", "time_sync_server", self.time_sync_server)
            await self.config.write_async()
        self.time_sync_interval = self.config.get_entry("time", "time_sync_interval")
        if not isinstance(self.time_sync_interval, int):
            self.time_sync_interval = self.default_time_sync_interval
            self.config.set_entry("time", "time_sync_interval", self.time_sync_interval)
            await self.config.write_async()

        self.config_watcher = asyncio.create_task(self.config.start_watching())

    async def send_pushover_notification(self, title="Goat - SecureMe", message="Testing", priority=0, timeout=5):
        """Send push notifications using Pushover.

            Args:
            - title: The title for the notification.
            - message: The message to send.
            - priority: The notification priority (0-2).
            - timeout: The request timeout in seconds.
            """
        await asyncio.sleep(0)

        url = "https://api.pushover.net/1/messages.json"

        self.pushover_app_token = self.config.get_entry("pushover", "app_token")

        if not self.pushover_app_token:
            print("A Pushover app token is required to send push notifications.")
            return

        self.pushover_api_key = self.config.get_entry("pushover", "api_key")

        if not self.pushover_api_key:
            print("A Pushover API key is required to send push notifications.")
            return

        data_dict = {
            "token": self.pushover_app_token,
            "user": self.pushover_api_key,
            "message": message,
            "priority": priority,
            "title": title
        }
        data = utils.urlencode(data_dict).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        for attempt in range(3):  # Retry up to 3 times
            try:
                print(f"Attempt {attempt + 1}: Sending notification...")
                response = urequests.post(url, data=data, headers=headers, timeout=timeout)

                if response.status_code == 200:
                    print("Notification sent successfully!")
                    print("Response:", response.text)
                    return
                else:
                    print(f"Failed to send notification. Status code: {response.status_code}")
            except Exception as e:
                print(f"Error sending notification (Attempt {attempt + 1}): {e}")
            finally:
                if 'response' in locals():
                    response.close()
                await asyncio.sleep(0.5)  # Slight delay before retrying

        print("All attempts to send notification failed.")

    async def send_system_status_notification(self, status_message):
        """Sends a system status notification via Pushover.

        Args:
        - status_message: The message to send.
        """
        await asyncio.sleep(0)

        if not status_message:
            print("A status message is required.")
            return

        try:
            self.pushover_app_token = self.config.get_entry("pushover", "app_token")

            if not self.pushover_app_token:
                return

            self.pushover_api_key = self.config.get_entry("pushover", "api_key")

            if not self.pushover_api_key:
                return

            self.system_status_notifications = self.config.get_entry("pushover", "system_status_notifications")

            if self.system_status_notifications:
                asyncio.create_task(self.send_pushover_notification(message=status_message))
        except Exception as e:
            print(f"Unable to send system status notification: {e}")

    def html_template(self, title, body):
        """Generates an HTML page template."""
        now = time.localtime()

        current_date = f"{now[1]:02d}/{now[2]:02d}/{now[0]}"
        current_time = f"{now[3]:02d}:{now[4]:02d}"

        template = f"""<html>
        <head><title>{title}</title></head>
        <body>
        <h1>{title}</h1>
        <p>Welcome to Goat - SecureMe.</p>
        <p><a href="/">Home</a></p>
        """

        if self.alert_text:
            template += f"""
            <h2>Alert</h2>
            <p><b>{self.escape_html(self.alert_text)}</b></p>
            """
            self.alert_text = None

        template += body

        template += f"""<h1>Information</h1>
        <p>Date: {current_date}<br>
        time: {current_time}</p>
        <p>Check out other Goat Technologies offerings at <a href="https://goatbot.org/">Goatbot.org</a></p>
        <p>Contribute to <b>SecureMe</b> on <a href="{self.REPO_URL}">GitHub</a></p>
        <p><b>Version {self.VERSION}</b><br>
        <b>© (c) 2024-2025 Goat Technologies</b></p>
        </body>
        </html>"""

        return template

    def authenticate(self, request):
        """Performs basic HTTP authentication."""
        try:
            if "Authorization: Basic" not in request:
                return False
            # Extract and decode credentials
            auth_header = request.split("Authorization: Basic ")[1].split("\r\n")[0]
            credentials = ubinascii.a2b_base64(auth_header).decode()
            username, password = credentials.split(":")

            # Perform plain-text password comparison
            if username == "admin" and password == self.admin_password:
                return True

            print("Incorrect credentials.")

            if self.system_status_notifications:
                if self.web_interface_notifications:
                    asyncio.create_task(self.send_system_status_notification(status_message="Web interface authorisation error."))

            return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    async def handle_request(self, reader, writer):
        """Handles incoming HTTP requests for the web server."""
        try:
            request = await reader.read(1024)
            request = request.decode()
            print("Request:", request)

            # Handle authentication
            if not self.authenticate(request):
                response = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm=\"SecureMe\"\r\n\r\n" + self.serve_unauthorized()
                writer.write(response.encode())
                await writer.drain()
                return

            # Serve the appropriate pages based on the request
            if "GET /web_interface_settings" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_web_interface_settings_form()
            elif "GET /detection_settings" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_detection_settings_form()
            elif "GET /change_password" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_change_password_form()
            elif "GET /pushover_settings" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_pushover_settings_form()
            elif "GET /change_security_code" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_change_security_code_form()
            elif "GET /auto_update_settings" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_auto_update_settings_form()
            elif "GET /time_sync_settings" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_time_sync_settings_form()
            elif "GET /reset_firmware" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_reset_firmware_form()
            elif "GET /reboot_device" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_reboot_device_form()
            elif "GET /" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_index()
            elif "POST /update_web_interface_settings" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                http_port = 'http_port' in post_data
                self.web_server_http_port = http_port
                self.config.set_entry("server", "http_port", self.web_server_http_port)
                await self.config.write_async()
                self.alert_text = "Web interface settings updated."
                if self.system_status_notifications:
                    if self.web_interface_notifications:
                        asyncio.create_task(self.send_system_status_notification(status_message="Web interface settings updated."))
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /update_detection_settings" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                detect_motion = 'detect_motion' in post_data
                detect_tilt = 'detect_tilt' in post_data
                detect_sound = 'detect_sound' in post_data
                sensor_cooldown = 'sensor_cooldown' in post_data
                arming_cooldown = 'arming_cooldown' in post_data
                self.detect_motion = detect_motion
                self.detect_tilt = detect_tilt
                self.detect_sound = detect_sound
                self.sensor_cooldown = sensor_cooldown
                self.arming_cooldown = arming_cooldown
                self.config.set_entry("security", "detect_motion", self.detect_motion)
                self.config.set_entry("security", "detect_tilt", self.detect_tilt)
                self.config.set_entry("security", "detect_sound", self.detect_sound)
                self.config.set_entry("security", "sensor_cooldown", self.sensor_cooldown)
                self.config.set_entry("security", "arming_cooldown", self.arming_cooldown)
                await self.config.write_async()
                self.alert_text = "Detection settings updated."
                if self.system_status_notifications:
                    if self.web_interface_notifications:
                        asyncio.create_task(self.send_system_status_notification(status_message="Detection settings updated."))
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /update_pushover_settings" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                self.pushover_app_token = post_data.get('pushover_token', None)
                self.pushover_api_key = post_data.get('pushover_key', None)
                self.system_status_notifications = post_data.get('status_notifications', True)
                self.general_notifications = post_data.get('general_notifications', True)
                self.security_code_notifications = post_data.get('security_code_notifications', True)
                self.web_interface_notifications = post_data.get('web_interface_notifications', True)
                self.update_notifications = post_data.get('update_notifications', True)
                self.config.set_entry("pushover", "app_token", self.pushover_app_token)
                self.config.set_entry("pushover", "api_key", self.pushover_api_key)
                self.config.set_entry("pushover", "system_status_notifications", self.system_status_notifications)
                self.config.set_entry("pushover", "general_notifications", self.general_notifications)
                self.config.set_entry("pushover", "security_code_notifications", self.security_code_notifications)
                self.config.set_entry("pushover", "web_interface_notifications", self.web_interface_notifications)
                self.config.set_entry("pushover", "update_notifications", self.update_notifications)
                await self.config.write_async()
                self.alert_text = "Pushover settings updated."
                if self.system_status_notifications:
                    if self.web_interface_notifications:
                        asyncio.create_task(self.send_system_status_notification(status_message="Pushover settings updated."))
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /update_security_code" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                self.security_code = post_data.get('security_code', None)
                self.config.set_entry("security", "security_code", self.security_code)
                await self.config.write_async()
                self.alert_text = "System security code updated."
                if self.system_status_notifications:
                    if self.web_interface_notifications:
                        asyncio.create_task(self.send_system_status_notification(status_message="System security code updated."))
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /update_password" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                self.admin_password = post_data.get('password', None)
                self.config.set_entry("server", "admin_password", self.admin_password)
                await self.config.write_async()
                self.alert_text = "Web administration password updated."
                if self.system_status_notifications:
                    if self.web_interface_notifications:
                        asyncio.create_task(self.send_system_status_notification(status_message="Web administration password updated."))
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /update_auto_update_settings" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                self.enable_auto_update = post_data.get('enable_auto_update', True)
                self.update_check_interval = post_data.get('update_check_interval', self.default_update_check_interval)
                self.config.set_entry("update", "enable_auto_update", self.enable_auto_update)
                self.config.set_entry("update", "update_check_interval", self.update_check_interval)
                await self.config.write_async()
                self.alert_text = "Automatic update settings updated."
                if self.system_status_notifications:
                    if self.web_interface_notifications:
                        asyncio.create_task(self.send_system_status_notification(status_message="Automatic update settings updated."))
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /update_time_sync_settings" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                self.enable_time_sync = post_data.get('enable_time_sync', True)
                self.time_sync_server = post_data.get('time_sync_server', self.default_time_sync_server)
                self.time_sync_interval = post_data.get('time_sync_server', self.default_time_sync_interval)
                self.config.set_entry("time", "enable_time_sync", self.enable_time_sync)
                self.config.set_entry("time", "time_sync_server", self.time_sync_server)
                self.config.set_entry("time", "time_sync_interval", self.time_sync_interval)
                await self.config.write_async()
                self.alert_text = "Time synchronisation settings updated."
                if self.system_status_notifications:
                    if self.web_interface_notifications:
                        asyncio.create_task(self.send_system_status_notification(status_message="Time synchronisation settings updated."))
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /reboot_device" in request:
                content = request.split("\r\n\r\n")[1]
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
                if self.system_status_notifications:
                    if self.web_interface_notifications:
                        asyncio.create_task(self.send_system_status_notification(status_message="System rebooting."))
                machine.reset()
            elif "POST /reset_firmware" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                reset_confirmation = post_data.get('reset_confirmation', None)
                if reset_confirmation != "secureme":
                    response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nReset confirmation mismatch."
                else:
                    response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
                    if self.config_file in uos.listdir(self.config_directory):
                        uos.remove(f"{self.config_directory}/{self.config_file}")
                    if self.network_config_file in uos.listdir(self.config_directory):
                        uos.remove(f"{self.config_directory}/{self.network_config_file}")
                    uos.rmdir(self.config_directory)
                if self.system_status_notifications:
                    if self.web_interface_notifications:
                        asyncio.create_task(self.send_system_status_notification(status_message="Configuration reset to factory defaults."))
                    machine.reset()
            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\n" + self.serve_error()

            # Send the response
            writer.write(response.encode())
            await writer.drain()
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    def escape_html(self, text):
        """Manually escape HTML characters."""
        return (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;")
        )

    def parse_form_data(self, content):
        """Parses URL-encoded form data into a dictionary and decodes percent-encoded characters."""
        post_data = {}
        pairs = content.split("&")  # Split the form data by '&'

        for pair in pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)  # Split each pair by '='
                post_data[utils.urldecode(key)] = utils.urldecode(value)  # Decode the key and value

        return post_data

    def serve_unauthorized(self):
        """Serves the web server unauthorized page."""
        body = """<p>Unable to access the SecureMe web interface using the credentials you provided.<br>
        Please check your access credentials and try again.</p>
        <h2>System Recovery</h2>
        <p>If you are unable to access the web interface due to lost credentials, perform a configuration reset using the SecureMe console.</p>
        """
        return self.html_template("Unauthorized", body)

    def serve_error(self):
        """Serves the web server error page."""
        body = """<p>The page you requested does not exist.<br>
        <a href="/">Home</a></p>
        """
        return self.html_template("Unauthorized", body)

    def serve_index(self):
        """Serves the web server index page."""
        body = """<p>Welcome to the Goat - SecureMe - Portable Security System.<br>
        Use the web interface to manage system settings securely.</p>
        <h2>System Settings</h2>
        <p>Select a setting from the list below.<br>
        <ul>
        <li><a href="/web_interface_settings">Web Interface Settings</a></li>
        <li><a href="/detection_settings">Detection Settings</a></li>
        <li><a href="/change_password">Change Admin Password</a><br></li>
        <li><a href="/pushover_settings">Pushover Settings</a></li>
        <li><a href="/change_security_code">Change System Security Code</a></li>
        <li><a href="/auto_update_settings">Automatic Update Settings</a></li>
        <li><a href="/time_sync_settings">Time Synchronisation Settings</a></li>
        <li><a href="/reboot_device">Reboot Device</a></li>
        <li><a href="/reset_firmware">Reset Firmware</a></li>
        </ul></p>
        <h2>About SecureMe</h2>
        <p>SecureMe is a portable, configurable security system designed for simplicity and effectiveness.</p>
        """

        return self.html_template("Welcome", body)

    def serve_web_interface_settings_form(self):
        """Serves the web interface settings form with the current settings pre-populated."""
        form = f"""<h2>Web Interface Settings</h2>
        <p>The settings below control the SecureMe web interface.<br>
        You should take care when modifying these settings.</p>
        <p><b>Improper modification of the settings below may render the SecureMe web interface inaccessible.</b></p>
        <form method="POST" action="/update_web_interface_settings">
            <label for="http_port">HTTP Port:</label>
            <input type="number" id="http_port" name="http_port" minlength=1 maxlength=5 value="{self.web_server_http_port}" required><br>
            <input type="submit" value="Save Settings">
        </form><br>
        """

        return self.html_template("Web Interface Settings", form)

    def serve_detection_settings_form(self):
        """Serves the detection settings form with the current settings pre-populated."""
        detect_motion_checked = 'checked' if self.detect_motion else ''
        detect_tilt_checked = 'checked' if self.detect_tilt else ''
        detect_sound_checked = 'checked' if self.detect_sound else ''
    
        form = f"""<h2>Detection Settings</h2>
        <p>The settings below control how the SecureMe system detects movement.</p>
        <form method="POST" action="/update_detection_settings">
            <p>Select the types of motion you want to detect.</p>
            <label for="detect_motion">Enable Motion Detection</label>
            <input type="checkbox" id="detect_motion" name="detect_motion" {detect_motion_checked}><br>
            <label for="detect_tilt">Enable Tilt Detection</label>
            <input type="checkbox" id="detect_tilt" name="detect_tilt" {detect_tilt_checked}><br>
            <label for="detect_sound">Enable Sound Detection</label>
            <input type="checkbox" id="detect_sound" name="detect_sound" {detect_sound_checked}><br>
            <p>After detecting motion, the system will cool down for a specified time before detecting again.<br>
            The cooldown is applied separately per sensor.<br>
            Specify how long in seconds the cooldown should last.</p>
            <label for="sensor_cooldown">Sensor Cooldown Time (Sec):</label>
            <input type="number" id="sensor_cooldown" name="sensor_cooldown" minlength=1 maxlength=2 value="{self.sensor_cooldown}" required><br>
            <p>When arming and disarming the system, a cooldown is applied to give you time to prepare.<br>
            For example, you might want time to secure the room after arming.<br>
            Specify how long in seconds the cooldown should last.</p>
            <label for="arming_cooldown">Arming Cooldown Time (Sec):</label>
            <input type="number" id="arming_cooldown" name="arming_cooldown" minlength=1 maxlength=2 value="{self.arming_cooldown}" required><br>
            <input type="submit" value="Save Settings">
        </form><br>
        """

        return self.html_template("Detection Settings", form)

    def serve_change_password_form(self):
        """Serves the change password form.""" 
        form = f"""<h2>Change Administrator Password</h2>
        <p>To change the administrator password, enter a new password below.</p>
        <form method="POST" action="/update_password">
            <label for="password">New Admin Password:</label>
            <input type="password" id="password" name="password" required><br>
            <input type="submit" value="Update Password">
        </form><br>
        """

        return self.html_template("Change Admin Password", form)

    def serve_pushover_settings_form(self):
        """Serves the Pushover Settings form with the current credentials pre-populated."""
        status_notifications_checked = 'checked' if self.system_status_notifications else ''
        general_notifications_checked = 'checked' if self.general_notifications else ''
        security_code_notifications_checked = 'checked' if self.security_code_notifications else ''
        web_interface_notifications_checked = 'checked' if self.web_interface_notifications else ''
        update_notifications_checked = 'checked' if self.update_notifications else ''

        form = f"""<h2>Pushover Settings</h2>
        <p>To register an application and obtain an API key for Pushover, visit the <a href="https://pushover.net">Pushover</a> web site.<br>
        Sign up for an account and register an application to obtain a token, and a device to obtain a key.</p>
        <form method="POST" action="/update_pushover_settings">
        <p>In order to receive system status notifications and use silent alarms, you must specify Pushover API credentials.<br>
        The Pushover app token identifies your application with Pushover.<br>
        The Pushover API key enables the SecureMe firmware to send push notifications.</p>
        <p>Specify your Pushover API credentials below.</p>
            <label for="pushover_token">Pushover App Token:</label>
            <input type="text" id="pushover_token" name="pushover_token" value="{self.pushover_app_token}" required><br>
            <label for="pushover_key">Pushover API Key:</label>
            <input type="text" id="pushover_key" name="pushover_key" value="{self.pushover_api_key}" required><br>
            <p>SecureMe can send system status notifications to keep you informed about how the system is operating.</p>
            <label for="status_notifications">Enable System Status Notifications</label>
            <input type="checkbox" id="status_notifications" name="status_notifications" {status_notifications_checked}><br>
            <p>Specify which status notifications you want to receive.</p>
            <label for="general_notifications">General Notifications</label>
            <input type="checkbox" id="general_notifications" name="general_notifications" {general_notifications_checked}><br>
            <label for="security_code_notifications">Security Code Entry Notifications</label>
            <input type="checkbox" id="security_code_notifications" name="security_code_notifications" {security_code_notifications_checked}><br>
            <label for="web_interface_notifications">Web Interface Notifications</label>
            <input type="checkbox" id="web_interface_notifications" name="web_interface_notifications" {web_interface_notifications_checked}><br>
            <label for="update_notifications">Firmware Update Notifications</label>
            <input type="checkbox" id="update_notifications" name="update_notifications" {update_notifications_checked}><br>
            <input type="submit" value="Save Settings">
        </form><br>
        """

        return self.html_template("Pushover Settings", form)

    def serve_change_security_code_form(self):
        """Serves the change security code form with the current key pre-populated.""" 
        form = f"""<h2>Change Security Code</h2>
        <p>The system security code is required to arm or disarm the system.<br>
        You should change this from the default value of "0000".</p>
        <form method="POST" action="/update_security_code">
            <label for="security_code">New Security Code:</label>
            <input type="number" id="security_code" name="security_code" minlength={self.security_code_min_length} maxlength={self.security_code_max_length} value="{self.security_code}" required><br>
            <input type="submit" value="Update Security Code">
        </form><br>
        """

        return self.html_template("Change System Security Code", form)

    def serve_auto_update_settings_form(self):
        """Serves the automatic update settings form with the current settings pre-populated."""
        enable_auto_update_checked = 'checked' if self.enable_auto_update else ''
    
        form = f"""<h2>Automatic Update Settings</h2>
        <p>The settings below control how the SecureMe system checks for firmware updates.</p>
        <form method="POST" action="/update_auto_update_settings">
            <p>Choose whether to enable the automatic update feature.</p>
            <label for="enable_auto_update">Enable Automatic Update</label>
            <input type="checkbox" id="enable_auto_update" name="enable_auto_update" {enable_auto_update_checked}><br>
            <p>After checking for updates when the system starts, SecureMe will wait for a specified duration before checking again.<br>
            Specify how long in minutes to wait between update checks.</p>
            <label for="update_check_interval">Update Check Interval (Min):</label>
            <input type="number" id="update_check_interval" name="update_check_interval" minlength=1 maxlength=3 value="{self.update_check_interval}" required><br>
            <input type="submit" value="Save Settings">
        </form><br>
        """

        return self.html_template("Automatic Update Settings", form)

    def serve_time_sync_settings_form(self):
        """Serves the time synchronisation settings form with the current settings pre-populated."""
        enable_time_sync_checked = 'checked' if self.enable_time_sync else ''
    
        form = f"""<h2>Time Synchronisation Settings</h2>
        <p>The settings below control how the SecureMe system synchronises the time and date.</p>
        <form method="POST" action="/update_time_sync_settings">
            <p>Choose whether to enable the time synchronisation feature.</p>
            <label for="enable_time_sync">Enable Time Synchronisation</label>
            <input type="checkbox" id="enable_time_sync" name="enable_time_sync" {enable_time_sync_checked}><br>
            <p>By default, SecureMe will use the <b>Goatbot.org</b> server for time synchronisation.<br>
            You can optionally specify an alternate server to use.<br>
            You should only choose an alternative server if you are self-hosting the Time Synchronisation API from the Pico Network Manager library.<br>
            Specify the time synchronisation server you want to use below.</p>
            <label for="time_sync_server">Time Synchronisation Server:</label>
            <input type="string" id="time_sync_server" name="time_sync_server" value="{self.time_sync_server}" required><br>
            <p>The system date and time are synchronised automatically after a specified interval.<br>
            You can optionally customize the time synchronisation interval below.</p>
            <label for="time_sync_interval">Time Synchronisation Interval (Min):</label>
            <input type="number" id="time_sync_interval" name="time_sync_interval" minlength=1 maxlength=4 value="{self.time_sync_interval}" required><br>
            <input type="submit" value="Save Settings">
        </form><br>
        """

        return self.html_template("Time Synchronisation Settings", form)

    def serve_reboot_device_form(self):
        """Serves the reboot device form.""" 
        form = f"""<h2>Reboot Device</h2>
        <p>If you recently made configuration changes and want to restart the SecureMe system, you can do so here.<br>
        Restarting the system will not affect any configuration settings.</p>
        <p>To reboot the SecureMe system, click "Reboot" below.</p>
        <form method="POST" action="/reboot_device">
            <input type="submit" value="Reboot Device">
        </form><br>
        """

        return self.html_template("Reboot Device", form)

    def serve_reset_firmware_form(self):
        """Serves the reset firmware form with the current key pre-populated.""" 
        form = f"""<h2>Reset SecureMe Firmware</h2>
        <p>If you are having trouble with your SecureMe security system you can try resetting the firmware.<br>
        Resetting the firmware will clear all current configuration data.</p>
        <form method="POST" action="/reset_firmware">
        <p>To reset the device, type "secureme" in the box below.</p>
            <label for="reset_confirmation">Reset Confirmation:</label>
            <input type="text" id="reset_confirmation" name="reset_confirmation" required><br>
            <input type="submit" value="Reset Device">
        </form><br>
        """

        return self.html_template("Reset SecureMe Firmware", form)

    async def start_server(self):
        """Starts the SecureMe HTTP server asynchronously."""
        if not self.ip_address:
            self.ip_address = self.default_ip_address

        if not self.http_port:
            self.http_port = self.default_http_port

        try:
            print("Starting SecureMe Web Interface...")

            self.server = await asyncio.start_server(self.handle_request, self.ip_address, self.http_port)

            print(f"Serving on {self.ip_address}:{self.http_port}")

            while True:
                machine.idle()

                await asyncio.sleep(1)  # Keep the server running
        except Exception as e:
            await self.stop_server()
            print(f"Error starting server: {e}")

    async def stop_server(self):
        """Stops the SecureMe HTTP server."""
        try:
            print("Stopping SecureMe Web Interface...")

            if self.server:
                self.server.close()
                await self.server.wait_closed()
                print("Server stopped.")
            else:
                print("Server already stopped.")
        except Exception as e:
            print(f"Error stopping server: {e}")
        finally:
            self.config_watcher.cancel()

    async def run(self):
        """Runs the SecureMe web server initialization process."""
        await self.initialize()
        await self.start_server()
