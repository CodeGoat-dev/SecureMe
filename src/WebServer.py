# Goat - SecureMe WebServer class
# Version 1.5.2
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
import pushover
import utils

# WebServer class
class WebServer:
    """Provides the web server for the Goat - SecureMe firmware."""
    
    def __init__(self, ip_address="0.0.0.0", http_port=8000):
        """Constructs the class and exposes properties."""
        # Constants
        self.VERSION = "1.5.2"
        self.REPO_URL = "https://github.com/CodeGoat-dev/SecureMe"

        self.default_ip_address = "0.0.0.0"
        self.default_http_port = 8000

        self.ip_address = ip_address
        self.http_port = http_port
        self.server = None

        self.config_directory = "/config"
        self.config_file = "secureme.conf"
        self.network_config_file = "network_config.conf"

        self.hostname = "SecureMe"
        self.default_hostname = "SecureMe"
        self.ip_address = "0.0.0.0"
        self.default_ip_address = "0.0.0.0"
        self.subnet_mask = "0.0.0.0"
        self.default_subnet_mask = "0.0.0.0"
        self.gateway = "0.0.0.0"
        self.default_gateway = "0.0.0.0"
        self.dns = "0.0.0.0"
        self.default_dns = "0.0.0.0"
        self.detect_motion = None
        self.detect_tilt = None
        self.detect_sound = None
        self.sensor_cooldown = 10
        self.default_sensor_cooldown = 10
        self.arming_cooldown = 10
        self.default_arming_cooldown = 10
        self.pir_warmup_time = 60
        self.default_pir_warmup_time = 60
        self.pushover_app_token = None
        self.pushover_api_key = None
        self.system_status_notifications = None
        self.general_notifications = None
        self.security_code_notifications = None
        self.web_interface_notifications = None
        self.update_notifications = None
        self.web_server_address = "0.0.0.0"
        self.default_web_server_address = "0.0.0.0"
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

        self.hostname = self.config.get_entry("network", "hostname")
        if not isinstance(self.hostname, str):
            self.hostname = self.default_hostname
            self.config.set_entry("network", "hostname", self.hostname)
            await self.config.write_async()
        self.ip_address = self.config.get_entry("network", "ip_address")
        if not isinstance(self.ip_address, str):
            self.ip_address = self.default_ip_address
            self.config.set_entry("network", "ip_address", self.ip_address)
            await self.config.write_async()
        self.subnet_mask = self.config.get_entry("network", "subnet_mask")
        if not isinstance(self.subnet_mask, str):
            self.subnet_mask = self.default_subnet_mask
            self.config.set_entry("network", "subnet_mask", self.subnet_mask)
            await self.config.write_async()
        self.gateway = self.config.get_entry("network", "gateway")
        if not isinstance(self.gateway, str):
            self.gateway = self.default_gateway
            self.config.set_entry("network", "gateway", self.gateway)
            await self.config.write_async()
        self.dns = self.config.get_entry("network", "dns")
        if not isinstance(self.dns, str):
            self.dns = self.default_dns
            self.config.set_entry("network", "dns", self.dns)
            await self.config.write_async()
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
        self.pir_warmup_time = self.config.get_entry("security", "pir_warmup_time")
        if not isinstance(self.pir_warmup_time, int):
            self.pir_warmup_time = self.default_pir_warmup_time
            self.config.set_entry("security", "pir_warmup_time", self.pir_warmup_time)
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
        self.web_server_address = self.config.get_entry("server", "address")
        if not isinstance(self.web_server_address, str):
            self.web_server_address = self.default_web_server_address
            self.config.set_entry("server", "address", self.web_server_address)
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

        self.pushover_app_token = self.config.get_entry("pushover", "app_token")

        if not self.pushover_app_token:
            print("A Pushover app token is required to send push notifications.")
            return

        self.pushover_api_key = self.config.get_entry("pushover", "api_key")

        if not self.pushover_api_key:
            print("A Pushover API key is required to send push notifications.")
            return

        try:
            key_is_valid = await pushover.validate_api_key(app_token=self.pushover_app_token, api_key=self.pushover_api_key)
            if not key_is_valid:
                print("The configured Pushover API key is invalid.")
                return

            asyncio.create_task(pushover.send_notification(app_token=self.pushover_app_token, api_key=self.pushover_api_key, title=title, message=message, priority=priority, timeout=timeout))
        except Exception as e:
            print(f"Error sending notification: {e}")

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
            if "GET /network_settings" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_network_settings_form()
            elif "GET /web_interface_settings" in request:
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
            elif "POST /update_network_settings" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                hostname = post_data.get('hostname', self.hostname)
                dhcp = post_data.get('dhcp', True)
                ip_address = f"{post_data.get('ip1', '0')}.{post_data.get('ip2', '0')}.{post_data.get('ip3', '0')}.{post_data.get('ip4', '0')}"
                subnet_mask = f"{post_data.get('subnet1', '0')}.{post_data.get('subnet2', '0')}.{post_data.get('subnet3', '0')}.{post_data.get('subnet4', '0')}"
                gateway = f"{post_data.get('gateway1', '0')}.{post_data.get('gateway2', '0')}.{post_data.get('gateway3', '0')}.{post_data.get('gateway4', '0')}"
                dns = f"{post_data.get('dns1', '0')}.{post_data.get('dns2', '0')}.{post_data.get('dns3', '0')}.{post_data.get('dns4', '0')}"
                if dhcp:
                    ip_address = "0.0.0.0"
                    subnet_mask = "0.0.0.0"
                    gateway = "0.0.0.0"
                    dns = "0.0.0.0"
                self.hostname = hostname
                self.ip_address = ip_address
                self.subnet_mask = subnet_mask
                self.gateway = gateway
                self.dns = dns
                self.config.set_entry("network", "hostname", self.hostname)
                self.config.set_entry("network", "ip_address", self.ip_address)
                self.config.set_entry("network", "subnet_mask", self.subnet_mask)
                self.config.set_entry("network", "gateway", self.gateway)
                self.config.set_entry("network", "dns", self.dns)
                await self.config.write_async()
                self.alert_text = "Network settings updated."
                response = "HTTP/1.1 303 See Other\r\nLocation: /network_settings\r\n\r\n"
            elif "POST /update_web_interface_settings" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                address = 'address' in post_data
                http_port = 'http_port' in post_data
                self.web_server_address = address
                self.web_server_http_port = http_port
                self.config.set_entry("server", "address", self.web_server_address)
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
                pir_warmup_time = 'pir_warmup_time' in post_data
                self.detect_motion = detect_motion
                self.detect_tilt = detect_tilt
                self.detect_sound = detect_sound
                self.sensor_cooldown = sensor_cooldown
                self.arming_cooldown = arming_cooldown
                self.pir_warmup_time = pir_warmup_time
                self.config.set_entry("security", "detect_motion", self.detect_motion)
                self.config.set_entry("security", "detect_tilt", self.detect_tilt)
                self.config.set_entry("security", "detect_sound", self.detect_sound)
                self.config.set_entry("security", "sensor_cooldown", self.sensor_cooldown)
                self.config.set_entry("security", "arming_cooldown", self.arming_cooldown)
                self.config.set_entry("security", "pir_warmup_time", self.pir_warmup_time)
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
                        await asyncio.sleep(10)
                machine.reset()
            elif "POST /reset_firmware" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                reset_confirmation = post_data.get('reset_confirmation', None)
                if reset_confirmation != "secureme":
                    self.alert_text = "Reset confirmation mismatch."
                    if self.config_file in uos.listdir(self.config_directory):
                        uos.remove(f"{self.config_directory}/{self.config_file}")
                    if self.network_config_file in uos.listdir(self.config_directory):
                        uos.remove(f"{self.config_directory}/{self.network_config_file}")
                    uos.rmdir(self.config_directory)
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
                if self.system_status_notifications:
                    if self.web_interface_notifications:
                        asyncio.create_task(self.send_system_status_notification(status_message="Configuration reset to factory defaults."))
                        await asyncio.sleep(10)
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
        <h2>Return To Home</h2>
        <p>Click <a href="/">Here</a> to return to the home page.</p>
        """
        return self.html_template("Unauthorized", body)

    def serve_error(self):
        """Serves the web server error page."""
        body = """<p>The page you requested does not exist.<br>
        <a href="/">Home</a></p>
        """
        return self.html_template("Unauthorized", body)

    def serve_index(self):
        """Serves the web interface index page."""
        body = """<p>Welcome to the Goat - SecureMe - Portable Security System.<br>
        Use the SecureMe web interface to manage system settings securely.</p>
        <h2>System Settings</h2>
        <p>Select a setting from the list below.<br>
        <ul>
        <li><a href="/network_settings">Network Settings</a></li>
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

    def serve_network_settings_form(self):
        """Serves the network settings configuration form."""
        dhcp_enabled = "checked" if self.ip_address == "0.0.0.0" else ""

        form = f"""
        <h2>Network Settings</h2>
        <p>The settings below control the SecureMe network connection.<br>
        Make sure you provide valid values to avoid connectivity issues.</p>
        <p><b>The SecureMe system must be restarted after changing network settings.</b></p>
        <p><b>Incorrect configuration of the SecureMe network settings may require a configuration reset.</b></p>
        <form method="POST" action="/update_network_settings">
            <h3>System Hostname</h3>
            <p>The hostname is the name used to identify the SecureMe device on your network.<br>
            You can specify a custom hostname or use the default.</p>
            <label for="hostname">Hostname:</label>
            <input type="text" id="hostname" name="hostname" value="{self.escape_html(self.hostname)}" required><br>
            <h3>IP Address</h3>
            <p>By default, SecureMe obtains an IP address via DHCP.<br>
            You can optionally customise the IP address settings below.</p>
            <label for="dhcp">Use DHCP:</label>
            <input type="checkbox" id="dhcp" name="dhcp" {dhcp_enabled} onchange="toggleIPFields()"><br>
            <label>IP Address:</label>
            <input type="number" name="ip1" min="0" max="255" value="{self.ip_address.split('.')[0]}" required>.
            <input type="number" name="ip2" min="0" max="255" value="{self.ip_address.split('.')[1]}" required>.
            <input type="number" name="ip3" min="0" max="255" value="{self.ip_address.split('.')[2]}" required>.
            <input type="number" name="ip4" min="0" max="255" value="{self.ip_address.split('.')[3]}" required><br>
            <label>Subnet Mask:</label>
            <input type="number" name="subnet1" min="0" max="255" value="{self.subnet_mask.split('.')[0]}" required>.
            <input type="number" name="subnet2" min="0" max="255" value="{self.subnet_mask.split('.')[1]}" required>.
            <input type="number" name="subnet3" min="0" max="255" value="{self.subnet_mask.split('.')[2]}" required>.
            <input type="number" name="subnet4" min="0" max="255" value="{self.subnet_mask.split('.')[3]}" required><br>
            <label>Gateway:</label>
            <input type="number" name="gateway1" min="0" max="255" value="{self.gateway.split('.')[0]}" required>.
            <input type="number" name="gateway2" min="0" max="255" value="{self.gateway.split('.')[1]}" required>.
            <input type="number" name="gateway3" min="0" max="255" value="{self.gateway.split('.')[2]}" required>.
            <input type="number" name="gateway4" min="0" max="255" value="{self.gateway.split('.')[3]}" required><br>
            <label>DNS Server:</label>
            <input type="number" name="dns1" min="0" max="255" value="{self.dns.split('.')[0]}" required>.
            <input type="number" name="dns2" min="0" max="255" value="{self.dns.split('.')[1]}" required>.
            <input type="number" name="dns3" min="0" max="255" value="{self.dns.split('.')[2]}" required>.
            <input type="number" name="dns4" min="0" max="255" value="{self.dns.split('.')[3]}" required><br>
            <input type="submit" value="Save Settings">
        </form><br>
        <script>
            function toggleIPFields() {{
                var dhcpChecked = document.getElementById('dhcp').checked;
                var ipFields = document.querySelectorAll('input[type="number"]');
                ipFields.forEach(field => {{
                    field.disabled = dhcpChecked;
                }});
            }}
            // Run on page load to set correct state
            window.onload = toggleIPFields;
        </script>
        """

        return self.html_template("Network Settings", form)

    def serve_web_interface_settings_form(self):
        """Serves the web interface settings form with the current settings pre-populated."""
        form = f"""<h2>Web Interface Settings</h2>
        <p>The settings below control the SecureMe web interface.<br>
        You should take care when modifying these settings.</p>
        <p><b>The SecureMe system must be restarted after changing web interface settings.</b></p>
        <p><b>Improper modification of the settings below may render the SecureMe web interface inaccessible.</b></p>
        <form method="POST" action="/update_web_interface_settings">
            <h3>Listen Address</h3>
            <p>The listen address is the address SecureMe uses to serve the web interface.<br>
            If the address is set to "0.0.0.0", connections are allowed from all interfaces.</p>
            <label for="address">Listen Address:</label>
            <input type="text" id="address" name="address" value="{self.web_server_address}" required><br>
            <h3>HTTP Port</h3>
            <p>The HTTP port is the port used by the web server to serve the web interface.<br>
            By default the web interface listens on port "8000".</p>
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
        <p>The settings below control how the SecureMe system detects movement.<br>
        You can control which sensors are enabled as well as adjust cooldown times.</p>
        <form method="POST" action="/update_detection_settings">
            <h3>Detection</h3>
            <p>Select the types of motion you want to detect.</p>
            <label for="detect_motion">Enable Motion Detection</label>
            <input type="checkbox" id="detect_motion" name="detect_motion" {detect_motion_checked}><br>
            <label for="detect_tilt">Enable Tilt Detection</label>
            <input type="checkbox" id="detect_tilt" name="detect_tilt" {detect_tilt_checked}><br>
            <label for="detect_sound">Enable Sound Detection</label>
            <input type="checkbox" id="detect_sound" name="detect_sound" {detect_sound_checked}><br>
            <h3>Cooldown Settings</h3>
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
            <h3>PIR Warmup Time</h3>
            <p>You can customise the PIR sensor warmup time to match the requirements of your sensor.<br>
            Specify how long in seconds the PIR sensor should warm up for.</p>
            <label for="pir_warmup_time">PIR Warmup Time (Sec):</label>
            <input type="number" id="pir_warmup_time" name="pir_warmup_time" minlength=1 maxlength=3 value="{self.pir_warmup_time}" required><br>
            <input type="submit" value="Save Settings">
        </form><br>
        """

        return self.html_template("Detection Settings", form)

    def serve_change_password_form(self):
        """Serves the change password form.""" 
        form = f"""<h2>Change Administrator Password</h2>
        <p>It is recommended to change the SecureMe web interface password to prevent unauthorized access.<br>
        To change the web interface administrator password, enter a new password below.</p>
        <form method="POST" action="/update_password">
            <h3>Administration Password</h3>
            <label for="password">New Admin Password:</label>
            <input type="password" id="password" name="password" required><br>
            <input type="submit" value="Update Password">
        </form><br>
        """

        return self.html_template("Change Admin Password", form)

    def serve_pushover_settings_form(self):
        """Serves the Pushover Settings form with the current credentials and settings pre-populated."""
        status_notifications_checked = 'checked' if self.system_status_notifications else ''
        general_notifications_checked = 'checked' if self.general_notifications else ''
        security_code_notifications_checked = 'checked' if self.security_code_notifications else ''
        web_interface_notifications_checked = 'checked' if self.web_interface_notifications else ''
        update_notifications_checked = 'checked' if self.update_notifications else ''

        form = f"""<h2>Pushover Settings</h2>
        <p>To register an application and obtain an API key for Pushover, visit the <a href="https://pushover.net">Pushover</a> web site.<br>
        Sign up for an account and register an application to obtain a token, and a device to obtain a key.</p>
        <form method="POST" action="/update_pushover_settings">
            <h3>Pushover API Credentials</h3>
        <p>In order to receive system status notifications and use silent alarms, you must specify Pushover API credentials.<br>
        The Pushover app token identifies your application with Pushover.<br>
        The Pushover API key enables the SecureMe firmware to send push notifications.</p>
        <p>Specify your Pushover API credentials below.</p>
            <label for="pushover_token">Pushover App Token:</label>
            <input type="text" id="pushover_token" name="pushover_token" value="{self.pushover_app_token}" required><br>
            <label for="pushover_key">Pushover API Key:</label>
            <input type="text" id="pushover_key" name="pushover_key" value="{self.pushover_api_key}" required><br>
            <h3>System Status Notifications</h3>
            <p>SecureMe can send system status notifications to keep you informed about how the system is operating.</p>
            <label for="status_notifications">Enable System Status Notifications</label>
            <input type="checkbox" id="status_notifications" name="status_notifications" {status_notifications_checked}><br>
           <h3>Notification Types</h3>
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
        """Serves the change security code form.""" 
        form = f"""<h2>Change Security Code</h2>
        <p>The system security code is required to arm or disarm the system.<br>
        The security code will also be required when changing the alarm mode or resetting the configuration to factory settings.</p>
        <p>You should change the security code from the default value of "0000" if you have not already done so.</p>
        <form method="POST" action="/update_security_code">
            <h3>System Security Code</h3>
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
        <p>The settings below control how the SecureMe system checks for firmware updates.<br>
        You can control whether automatic update is enabled as well as adjust the update interval.</p>
        <form method="POST" action="/update_auto_update_settings">
            <h3>Enable Automatic Update</h3>
            <p>Choose whether to enable the automatic update feature.</p>
            <p><b>Note that automatic update may cause memory issues on RP2040 based microcontrollers.</b></p>
            <label for="enable_auto_update">Enable Automatic Update</label>
            <input type="checkbox" id="enable_auto_update" name="enable_auto_update" {enable_auto_update_checked}><br>
            <h3>Update Check Interval</h3>
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
        <p>The settings below control how the SecureMe system synchronises the time and date.<br>
        You can control whether time synchronisation is enabled, the sync interval and the server to synchronise from.</p>
        <form method="POST" action="/update_time_sync_settings">
            <h3>Enable Time Synchronisation</h3>
            <p>Choose whether to enable the time synchronisation feature.</p>
            <label for="enable_time_sync">Enable Time Synchronisation</label>
            <input type="checkbox" id="enable_time_sync" name="enable_time_sync" {enable_time_sync_checked}><br>
            <h3>Synchronisation Server</h3>
            <p>By default, SecureMe will use the <b>Goatbot.org</b> server for time synchronisation.<br>
            You can optionally specify an alternate server to use.<br>
            You should only choose an alternative server if you are self-hosting the Time Synchronisation API from the Pico Network Manager library.<br>
            Specify the time synchronisation server you want to use below.</p>
            <label for="time_sync_server">Time Synchronisation Server:</label>
            <input type="string" id="time_sync_server" name="time_sync_server" value="{self.time_sync_server}" required><br>
            <h3>Synchronisation Interval</h3>
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
        <p>To reboot the SecureMe system, click the "Reboot" button below.</p>
        <form method="POST" action="/reboot_device">
            <input type="submit" value="Reboot Device">
        </form><br>
        """

        return self.html_template("Reboot Device", form)

    def serve_reset_firmware_form(self):
        """Serves the reset firmware form.""" 
        form = f"""<h2>Reset SecureMe Firmware</h2>
        <p>If you are having trouble with your SecureMe security system you can try resetting the firmware.<br>
        Resetting the firmware will clear all current configuration data.</p>
        <form method="POST" action="/reset_firmware">
            <h3>Reset Configuration</h3>
        <p>To reset the device, type "secureme" in the confirmation box below.</p>
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
