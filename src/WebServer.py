# Goat - SecureMe WebServer class
# Version 1.1.1
# © (c) 2024-2025 Goat Technologies
# https://github.com/CodeGoat-dev/SecureMe
# Description:
# Provides the web server for the Goat - SecureMe firmware.

# Imports
import machine
import network
import uasyncio as asyncio
import uos
import utime
import ubinascii
from ConfigManager import ConfigManager

# WebServer class
class WebServer:
    """Provides the web server for the Goat - SecureMe firmware."""
    
    def __init__(self, ip_address="0.0.0.0", http_port=8000):
        """Constructs the class and exposes properties."""
        # Constants
        self.VERSION = "1.1.1"

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
        self.admin_password = "secureme"
        self.default_admin_password = "secureme"
        self.security_code = "0000"
        self.default_security_code = "0000"
        self.security_code_min_length = 4
        self.security_code_max_length = 8

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
        self.security_code = self.config.get_entry("security", "security_code")
        if not isinstance(self.security_code, str):
            self.security_code = self.default_security_code
            self.config.set_entry("security", "security_code", self.security_code)
            await self.config.write_async()
        self.admin_password = self.config.get_entry("server", "admin_password")
        if not isinstance(self.admin_password, str):
            self.admin_password = self.default_admin_password
            self.config.set_entry("server", "admin_password", self.admin_password)
            await self.config.write_async()

        self.config_watcher = asyncio.create_task(self.config.start_watching())

    def html_template(self, title, body):
        """Generates an HTML page template."""
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

        template += f"""{body}
        <h1>Information</h1>
        <p>Check out other Goat Technologies offerings at <a href="https://goatbot.org/">Goatbot.org</a></p>
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
                response = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm=\"SecureMe\"\r\n\r\nUnauthorized"
                writer.write(response.encode())
                await writer.drain()
                return

            # Serve the appropriate pages based on the request
            if "GET /detection_settings" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_detection_settings_form()
            elif "GET /change_password" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_change_password_form()
            elif "GET /change_pushover" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_change_pushover_form()
            elif "GET /change_security_code" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_change_security_code_form()
            elif "GET /reset_firmware" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_reset_firmware_form()
            elif "GET /reboot_device" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_reboot_device_form()
            elif "GET /" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_index()
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
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /update_pushover" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                self.pushover_app_token = post_data.get('pushover_token', None)
                self.pushover_api_key = post_data.get('pushover_key', None)
                self.config.set_entry("pushover", "app_token", self.pushover_app_token)
                self.config.set_entry("pushover", "api_key", self.pushover_api_key)
                await self.config.write_async()
                self.alert_text = "Pushover API credentials updated."
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /update_security_code" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                self.security_code = post_data.get('security_code', None)
                self.config.set_entry("security", "security_code", self.security_code)
                await self.config.write_async()
                self.alert_text = "System security code updated."
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /update_password" in request:
                content = request.split("\r\n\r\n")[1]
                post_data = self.parse_form_data(content)  # Parse the form data manually
                self.admin_password = post_data.get('password', None)
                self.config.set_entry("server", "admin_password", self.admin_password)
                await self.config.write_async()
                self.alert_text = "Web administration password updated."
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
            elif "POST /reboot_device" in request:
                content = request.split("\r\n\r\n")[1]
                response = "HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n"
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
                    machine.reset()
            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\nNot Found"

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
        """Parses URL-encoded form data into a dictionary."""
        post_data = {}
        pairs = content.split("&")  # Split the form data by '&'
        for pair in pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)  # Split each pair by '='
                post_data[key] = value  # Store the key-value pair in the dictionary
        return post_data

    def serve_index(self):
        """Serves the web server index page."""
        body = """<p>Welcome to the Goat - SecureMe - Portable Security System.<br>
        Use the web interface to manage system settings securely.</p>
        <h2>System Settings</h2>
        <p>Select a setting from the list below.<br>
        <ul>
        <li><a href="detection_settings">Detection Settings</a></li>
        <li><a href="/change_password">Change Admin Password</a><br></li>
        <li><a href="/change_pushover">Change Pushover API Credentials</a></li>
        <li><a href="/change_security_code">Change System Security Code</a></li>
        <li><a href="/reboot_device">Reboot Device</a></li>
        <li><a href="/reset_firmware">Reset Firmware</a></li>
        </ul></p>
        <h2>About SecureMe</h2>
        <p>SecureMe is a portable, configurable security system designed for simplicity and effectiveness.</p>
        """
        return self.html_template("Welcome", body)

    def serve_detection_settings_form(self):
        """Serves the detection settings form with the current settings pre-populated."""
        detect_motion_checked = 'checked' if self.detect_motion else ''
        detect_tilt_checked = 'checked' if self.detect_tilt else ''
        detect_sound_checked = 'checked' if self.detect_sound else ''
    
        form = f"""<h2>Detection Settings</h2>
        <p>The settings below control how the SecureMe system detects movement.</p>
        <p><form method="POST" action="/update_detection_settings">
            <p>Select the types of motion you want to detect."</p>
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
        </form></p>
        """

        return self.html_template("Detection Settings", form)

    def serve_change_password_form(self):
        """Serves the change password form.""" 
        form = f"""<h2>Change Administrator Password</h2>
        <p>To change the administrator password, enter a new password below.</p>
        <p><form method="POST" action="/update_password">
            <label for="password">New Admin Password:</label>
            <input type="password" id="password" name="password" required><br>
            <input type="submit" value="Update Password">
        </form></p>
        """
        return self.html_template("Change Admin Password", form)

    def serve_change_pushover_form(self):
        """Serves the change Pushover API credentials form with the current credentials pre-populated."""
        form = f"""<h2>Change Pushover API Credentials</h2>
        <p>In order to use the silent alarm feature, you must specify Pushover API credentials.<br>
        The Pushover app token identifies your application with Pushover.<br>
        The Pushover API key enables the SecureMe firmware to send push notifications when the alarm is triggered.</p>
        <p>To register an application and obtain an API key for Pushover, visit the <a href="https://pushover.net">Pushover</a> web site.<br>
        Sign up for an account and register an application to obtain a token, and a device to obtain a key.</p>
        <p><form method="POST" action="/update_pushover">
            <label for="pushover_token">Pushover App Token:</label>
            <input type="text" id="pushover_token" name="pushover_token" value="{self.pushover_app_token}" required><br>
            <label for="pushover_key">Pushover API Key:</label>
            <input type="text" id="pushover_key" name="pushover_key" value="{self.pushover_api_key}" required><br>
            <input type="submit" value="Save">
        </form></p>
        """
        return self.html_template("Change Pushover API Key", form)

    def serve_change_security_code_form(self):
        """Serves the change security code form with the current key pre-populated.""" 
        form = f"""<h2>Change Security Code</h2>
        <p>The system security code is required to arm or disarm the system.<br>
        You should change this from the default value of "0000".</p>
        <p><form method="POST" action="/update_security_code">
            <label for="security_code">New Security Code:</label>
            <input type="number" id="security_code" name="security_code" minlength={self.security_code_min_length} maxlength={self.security_code_max_length} value="{self.security_code}" required><br>
            <input type="submit" value="Update Security Code">
        </form></p>
        """
        return self.html_template("Change System Security Code", form)

    def serve_reboot_device_form(self):
        """Serves the reboot device form.""" 
        form = f"""<h2>Reboot Device</h2>
        <p>If you recently made configuration changes and want to restart the SecureMe system, you can do so here.<br>
        Restarting the system will not affect any configuration settings.</p>
        <p>To reboot the SecureMe system, click "Reboot" below.</p>
        <p><form method="POST" action="/reboot_device">
            <input type="submit" value="Reboot Device">
        </form></p>
        """
        return self.html_template("Reboot Device", form)

    def serve_reset_firmware_form(self):
        """Serves the reset firmware form with the current key pre-populated.""" 
        form = f"""<h2>Reset SecureMe Firmware</h2>
        <p>If you are having trouble with your SecureMe security system you can try resetting the firmware.<br>
        Resetting the firmware will clear all current configuration data.</p>
        <p>To reset the device, type "secureme" in the box below.</p>
        <p><form method="POST" action="/reset_firmware">
            <label for="reset_confirmation">Reset Confirmation:</label>
            <input type="text" id="reset_confirmation" name="reset_confirmation" required><br>
            <input type="submit" value="Reset Device">
        </form></p>
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
