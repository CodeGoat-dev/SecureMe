# Goat - Captive Portal class
# Version 1.00
# © (c) 2024 Goat Technologies
# Description:
# Provides captive portal and wireless connectivity for Goat device firmware.
# Responsible for maintaining network state and managing connection lifetime.

# Imports
import network
import uasyncio as asyncio
import uos
import utime

# CaptivePortal class
class CaptivePortal:
    """Provides captive portal and wireless connectivity for Goat device firmware."""
    # Class constructor
    def __init__(self, ssid="Goat - Captive Portal", password="securepassword"):
        """Constructs the class and exposes properties."""
        # Network configuration
        self.config_file = "network_config.txt"

        # Interface configuration
        self.sta = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.ip_address = None
        self.server = None

        # Access point settings
        self.ssid = ssid
        self.password = password
        self.http_port = 80

        # Access point IP settings
        self.ap_ip_address = "192.168.4.1"
        self.ap_subnet = "255.255.255.0"
        self.ap_gateway = "192.168.4.1"
        self.ap_dns = "192.168.4.1"

        # STA web server configuration
        self.sta_web_server = None

    async def load_config(self):
        """Loads saved network configuration and connects to a saved network."""
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
                        if self.sta_web_server:
                            try:
                                web_server = self.sta_web_server()
                                self.server = await web_server.run()
                            except Exception as e:
                                print(f"Error starting web server: {e}")
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

    async def save_config(self, ssid, password):
        """Saves network connection configuration to a file."""
        try:
            with open(self.config_file, "w") as file:
                file.write(f"{ssid}\n{password}")
            print("Network configuration saved.")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    async def start_ap(self):
        """Starts the access point with WPA2 security and optional custom IP configuration."""
        ip_address = self.ap_ip_address
        subnet = self.ap_subnet
        gateway = self.ap_gateway
        dns = self.ap_dns

        if len(self.password) < 8:
            print("Password must be at least 8 characters long.")
            return

        try:
            self.ap_if.config(essid=self.ssid, password=self.password)
            self.ap_if.active(True)

            # Configure access point IP settings
            self.ap_if.ifconfig((ip_address, subnet, gateway, dns))

            self.ip_address = self.ap_if.ifconfig()[0]

            print(f"Access point started. SSID: {self.ssid}, IP: {self.ip_address}")
        except Exception as e:
            print(f"Error starting Access point: {e}")

    async def stop_ap(self):
        """Stops the access point."""
        if not self.ap_if.isconnected():
            print("The access point is not currently enabled.")
            return

        try:
            self.ap_if.config(essid="", password="")
            self.ap_if.active(False)
            self.ap_if.deinit()

            print("Access point stopped.")
        except Exception as e:
            print(f"Error stopping Access point: {e}")

    async def handle_request(self, reader, writer):
        """Handles incoming HTTP requests for the captive portal."""
        try:
            request = await reader.read(1024)
            request = request.decode()
            print("Request:", request)

            # Handle captive portal detection endpoints
            if "GET /generate_204" in request:  # Android detection
                response = "HTTP/1.1 204 No Content\r\n\r\n"
            elif "GET /connectivity-check" in request:  # Chrome OS/Chromium-based browsers
                response = "HTTP/1.1 204 No Content\r\n\r\n"
            elif "GET /hotspot-detect.html" in request:  # macOS/iOS detection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                response += "<HTML><BODY><H1>Success</H1></BODY></HTML>"
            elif "GET /success.txt" in request:  # Windows detection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
                response += "Microsoft Connect Test"
            elif "GET /ncsi.txt" in request:  # Windows NCSI detection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
                response += "Microsoft NCSI"
            elif "GET /scan" in request:  # Wireless network scan
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + await self.scan_networks()
            elif "POST /connect" in request:  # Wireless network connection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + await self.connect_to_wifi(request)
            else:
                # Default response or index page
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_index()

            # Write the response
            writer.write(response.encode())
            await writer.drain()
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def scan_networks(self):
        """Scans for available wireless networks and returns HTML."""
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
        html += "<a href='/'>Go Back</a><br><p>© (c) 2024 Goat Technologies</p></body></html>"
        return html

    async def connect_to_wifi(self, request):
        """Parses request for Wi-Fi credentials and connects to the network."""
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
                    await self.save_config(ssid, password)
                    await self.stop_ap()
                    await self.stop_server()
                    if self.sta_web_server:
                        try:
                            web_server = self.sta_web_server()
                            self.server = await web_server.run()
                        except Exception as e:
                            print(f"Error starting web server: {e}")
                    return f"""<html>
                    <head><title>Connected</title></head>
                    <body>
                    <h1>Connected</h1>
                    <p>You successfully connected to {ssid}.</p>
                    <h2>Information</h2>
                    <p>The access point has been shut down and you can now close this page.</p>
                    <p>© (c) 2024 Goat Technologies</p>
                    </body>
                    </html>"""
                else:
                    return f"""<html>
                    <head><title>Connection Failed</title></head>
                    <body>
                    <h1>Connection Failed</h1>
                    <p>Failed to connect to {ssid}.</p>
                    <p>© (c) 2024 Goat Technologies</p>
                    </body>
                    </html>"""
            else:
                return """<html>
                <head><title>Connection Error</title></head>
                <body>
                <h1>Connection Error</h1>
                <p>The SSID or password for the wi-fi network was not provided.</p>
                <p>© (c) 2024 Goat Technologies</p>
                </body>
                </html>"""
        except Exception as e:
            return f"""<html>
            <head><title>Error</title></head>
            <body>
            <h1>Error</h1>
            <p>An error occurred: {e}</p>
            <p>© (c) 2024 Goat Technologies</p>
            </body>
            </html>"""

    async def disconnect_from_wifi(self):
        """Disconnects from the currently connected wireless network."""
        if not self.sta.isconnected():
            print("The network is not connected.")
            return;

        try:
            self.sta.active(False)
            self.sta.deinit()
        except Exception as e:
            print(f"Error disconnecting from wi-fi: {e}")

    def serve_index(self):
        """Serves the captive portal index page."""
        return """<html>
        <head><title>Goat - Captive Portal</title></head>
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
        """Starts the captive portal HTTP server asynchronously."""
        if not self.ip_address:
            print("AP IP address not assigned. Cannot start server.")
            return

        try:
            self.server = await asyncio.start_server(self.handle_request, self.ip_address, self.http_port)
            print(f"Serving on {self.ip_address}:{self.http_port}")

            while True:
                await asyncio.sleep(1)  # Keep the server running
        except Exception as e:
            print(f"Error starting server: {e}")

    async def stop_server(self):
        """Stops the captive portal HTTP server."""
        try:
            if self.server:
                await self.server.await_closed()
                print("Server stopped.")
            else:
                print("Server already stopped.")
        except Exception as e:
            print(f"Error stopping server: {e}")

    async def run(self):
        """Runs the captive portal initialization process and maintains connectivity."""
        try:
            await self.load_config()  # Load and attempt to connect to saved configuration
            if not self.sta.isconnected():
                await self.start_ap()  # Start AP mode if STA is not connected
                await self.start_server()

            # Keep the network stack active
            while True:
                if not self.ap_if.isconnected() and not self.sta.isconnected():
                    break

                await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Error starting the captive portal: {e}")
        finally:
            await self.disconnect_from_wifi()
            await self.stop_server()
            await self.stop_ap()
