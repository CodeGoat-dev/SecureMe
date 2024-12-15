# Goat - Captive Portal class
# Version 1.00
# © (c) 2024 Goat Technologies
# Description:
# Provides captive portal and wireless connectivity for Goat firmware.

# Imports
import network
import uasyncio as asyncio
import uos
import utime

# CaptivePortal class
class CaptivePortal:
    def __init__(self, ssid="Goat - Captive Portal", password="securepassword"):
        self.ssid = ssid
        self.password = password
        self.http_port = 80
        self.sta = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.ip_address = None
        self.config_file = "network_config.txt"

        self.server = None

    def load_config(self):
        """Loads saved network configuration and connects."""
        try:
            if self.config_file in uos.listdir("/"):
                with open(self.config_file, "r") as file:
                    try:
                        ssid, password = file.read().strip().split("\n")
                    except ValueError:
                        print("Error: Invalid format in config file.")
                        return

                attempts = 0

                while attempts < 3:
                    self.sta.active(True)
                    self.sta.connect(ssid, password)
                    print(f"Attempting to connect to {ssid}...")

                    timeout = utime.time() + 10
                    while not self.sta.isconnected() and utime.time() < timeout:
                        utime.sleep(0.5)

                    if self.sta.isconnected():
                        self.ip_address = self.sta.ifconfig()[0]
                        print(f"Connected to {ssid}. IP: {self.ip_address}")
                        break
                    else:
                        print(f"Attempt {attempts + 1}: Failed to connect to Wi-Fi.")
                        attempts += 1

                if not self.sta.isconnected():
                    print("All connection attempts failed.")
            else:
                print("No saved network configuration found.")
        except Exception as e:
            print(f"Error loading network configuration: {e}")

    def save_config(self, ssid, password):
        """Saves network configuration to a file."""
        try:
            with open(self.config_file, "w") as file:
                file.write(f"{ssid}\n{password}")
            print("Network configuration saved.")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    async def start_ap(self):
        """Starts the access point with WPA2 security."""
        try:
            if len(self.password) < 8:
                raise ValueError("Password must be at least 8 characters long.")
            self.ap_if.config(essid=self.ssid, password=self.password)
            self.ap_if.active(True)
            self.ip_address = self.ap_if.ifconfig()[0]
            print(f"Access point started. SSID: {self.ssid}, IP: {self.ip_address}")
        except Exception as e:
            print(f"Error starting Access point: {e}")

    async def handle_request(self, reader, writer):
        """Handles incoming HTTP requests."""
        try:
            request = await reader.read(1024)
            request = request.decode()
            print("Request:", request)

            response = ""
            if "GET /scan" in request:
                response = await self.scan_networks()
            elif "POST /connect" in request:
                response = await self.connect_to_wifi(request)
            else:
                response = self.serve_index()

            writer.write("HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n".encode() + response.encode())
            await writer.drain()
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def scan_networks(self):
        """Scans for available networks and returns HTML."""
        self.sta.active(True)
        html = "<html><head><title>Network Scan</title></head><body>"
        html += "<h1>Available Wi-Fi Networks</h1><p>The following wi-fi networks were detected:"
        try:
            networks = self.sta.scan()
            for net in networks:
                ssid = net[0].decode()
                html += f"""
                    <form action='/connect' method='POST'>
                        <label>{ssid} - Signal Strength: {net[3]}</label><br>
                        <input type='hidden' name='ssid' value='{ssid}'>
                        <input type='password' name='password' placeholder='Password'><br>
                        <button type='submit'>Connect</button>
                    </form><br>
                """
        except Exception as e:
            html += f"<h2>Error scanning networks: {e}</h2>"
        finally:
            self.sta.active(False)
        html += "<a href='/'>Back</a></body></html>"
        return html

    async def connect_to_wifi(self, request):
        """Parses request for Wi-Fi credentials and connects."""
        try:
            body_start = request.find("\r\n\r\n") + 4
            body = request[body_start:]
            params = {}
            for kv in body.split("&"):
                if "=" in kv:
                    key, value = kv.split("=", 1)
                    params[key] = value.replace("+", " ").replace("%20", " ")

            ssid = params.get("ssid", "")
            password = params.get("password", "")

            if ssid and password:
                self.sta.active(True)
                self.sta.connect(ssid, password)

                timeout = utime.time() + 10
                while not self.sta.isconnected() and utime.time() < timeout:
                    await asyncio.sleep(0.5)

                if self.sta.isconnected():
                    self.save_config(ssid, password)
                    self.ap_if.active(False)
                    self.ap_if.deinit()
                    self.stop_server()
                    return f"<html><head><title>Connected</title></head><body><h1>Connected</h1><p>You successfully connected to {ssid}.</p><p><h2>Information</h2><p>The access point has been shut down and you can now close this page.</p><p>© (c) 2024 Goat Technologies</p></body></html>"
                else:
                    return f"<html><head><title>Connection Failed</title></head><body><h1>Connection Failed</h1><p>Failed to connect to {ssid}.</p></body></html>"
            else:
                return "<html><head><title>Connection Error</title></head><body><h1>Connection Error</h1><p>The SSID or password for the wi-fi network was not provided.</p></body></html>"
        except Exception as e:
            return f"<html><head><title>Error</title></head><body><h1>Error: {e}</h1></body></html>"

    def serve_index(self):
        """Serves the main page."""
        return """<html>
        <head><title>Wi-Fi Setup</title></head>
        <body>
            <h1>Welcome</h1>
            <p>Welcome  to the Goat - Captive Portal.<br>
            You can use the captive portal to connect your Goat device to your wireless network.</p>
            <h2>Connect To A Network</h2>
            <p>Connecting to your network unlocks the full power of Goat devices with features such as web interfaces, mobile app control and more.<br>
            Click the link below to scan for networks.</p>
            <p><a href='/scan'>Start Scan</a></p>
            <p>© (c) 2024 Goat Technologies</p>
        </body>
        </html>"""

    async def start_server(self):
        """Starts the HTTP server asynchronously."""
        if not self.ip_address:
            raise RuntimeError("AP IP address not assigned. Cannot start server.")
        self.server = await asyncio.start_server(self.handle_request, self.ip_address, self.http_port)
        print(f"Serving on {self.ip_address}:{self.http_port}")

        while True:
            await asyncio.sleep(1)  # Keep the server running

    def stop_server(self):
        """Stops the HTTP server."""
        if self.server:
            self.server.close()
            print("Server stopped.")

    async def run(self):
        """Runs the captive portal setup."""
        try:
            self.load_config()  # Load and attempt to connect to saved configuration
            if not self.sta.isconnected():
                await self.start_ap()  # Start AP mode if STA is not connected
                await self.start_server()
        except Exception as e:
            print(f"Error starting the captive portal: {e}")
