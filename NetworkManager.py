# Goat - Network Manager class
# Version 1.0.0
# © (c) 2024-2025 Goat Technologies
# Description:
# Provides network management for Goat device firmware.
# Responsible for maintaining network state and managing connection lifetime.
# Includes access point mode with a captive portal as well as station mode.

# Imports
import network
import uasyncio as asyncio
import uos
import utime
from ConfigManager import ConfigManager
from NetworkManagerDNS import NetworkManagerDNS

# NetworkManager class
class NetworkManager:
    """Provides network management for Goat device firmware.
    Responsible for maintaining network state and managing connection lifetime.
"""
    # Class constructor
    def __init__(self, ap_ssid="Goat - Captive Portal", ap_password="securepassword", sta_web_server = None):
        """Constructs the class and exposes properties."""
        # Network configuration
        self.config_directory = "/config"
        self.config_file = "network_config.conf"

        # Interface configuration
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.ip_address = None
        self.server = None

        # Access point settings
        self.ap_ssid = ap_ssid
        self.ap_password = ap_password
        self.captive_portal_http_port = 80
        self.network_connection_timeout = 10

        # Access point IP settings
        self.ap_ip_address = "192.168.4.1"
        self.ap_subnet = "255.255.255.0"
        self.ap_gateway = "192.168.4.1"
        self.ap_dns = "192.168.4.1"

        # Captive portal DNS server
        self.dns_server = NetworkManagerDNS(portal_ip=self.ap_ip_address)

        # STA web server configuration
        self.sta_web_server = sta_web_server

    async def load_config(self):
        """Loads saved network configuration and connects to a saved network."""
        try:
            if self.config_file in uos.listdir(self.config_directory):
                config = ConfigManager(self.config_directory, self.config_file)
                await config.read_async()

                ssid = config.get_entry("network", "ssid")
                password = config.get_entry("network", "password")

                if not ssid:
                    print("No SSID provided in configuration. Cannot connect to a network.")
                    return

                attempts = 0

                while attempts < 3:
                    self.sta_if.active(True)
                    self.sta_if.connect(ssid, password)
                    print(f"Attempting to connect to {ssid}...")

                    timeout = utime.time() + self.network_connection_timeout
                    while not self.sta_if.isconnected() and utime.time() < timeout:
                        utime.sleep(0.5)

                    if self.sta_if.isconnected():
                        self.ip_address = self.sta_if.ifconfig()[0]
                        print(f"Connected to {ssid}. IP: {self.ip_address}")
                        if self.sta_web_server:
                            try:
                                self.server = await self.sta_web_server.run()
                            except Exception as e:
                                print(f"Error starting web server: {e}")
                        break
                    else:
                        print(f"Attempt {attempts + 1}: Failed to connect to Wi-Fi.")
                        attempts += 1

                if not self.sta_if.isconnected():
                    print("All connection attempts failed.")
            else:
                print("No saved network configuration found.")
        except Exception as e:
            print(f"Error loading network configuration: {e}")

    async def save_config(self, ssid, password):
        """Saves network connection configuration to a file."""
        try:
            config = ConfigManager(self.config_directory, self.config_file)
            await config.read_async()

            config.set_entry("network", "ssid", ssid)
            config.set_entry("network", "password", password)

            await config.write_async()

            print("Network configuration saved.")
        except Exception as e:
            print(f"Error saving configuration: {e}")

    async def start_ap(self):
        """Starts the access point with WPA2 security and optional custom IP configuration."""
        ip_address = self.ap_ip_address
        subnet = self.ap_subnet
        gateway = self.ap_gateway
        dns = self.ap_dns

        if len(self.ap_password) < 8:
            print("Password must be at least 8 characters long.")
            return

        try:
            self.ap_if.config(essid=self.ap_ssid, password=self.ap_password)
            self.ap_if.active(True)

            # Configure access point IP settings
            self.ap_if.ifconfig((ip_address, subnet, gateway, dns))

            self.ip_address = self.ap_if.ifconfig()[0]

            print(f"Access point started. SSID: {self.ap_ssid}, IP: {self.ip_address}")
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

            self.ip_address = None

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
            elif "GET /success.conf" in request:  # Windows detection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
                response += "Microsoft Connect Test"
            elif "GET /ncsi.conf" in request:  # Windows NCSI detection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
                response += "Microsoft NCSI"
            elif "GET /scan" in request:  # Wireless network scan
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + await self.scan_networks()
            elif "POST /connect" in request:  # Wireless network connection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + await self.connect_to_wifi(request)
            elif "POST /reconnect" in request:  # Saved wireless network reconnection
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + await self.reconnect_to_wifi()
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

    def html_template(self, title, body):
        """Generates an HTML page template."""
        return f"""
        <html>
        <head><title>{title}</title></head>
        <body>
            <h1>{title}</h1>
            <p><a href="/">Home</a></p>
            {body}
            <h1>Information</h1>
            <p>Check out other Goat Technologies offerings at <a href="https://goatbot.org/">Goatbot.org</a></p>
            <p>© (c) 2024-2025 Goat Technologies</p>
        </body>
        </html>
        """

    async def scan_networks(self):
        """Scans for available wireless networks and returns HTML."""
        self.sta_if.active(True)
        html = "<h2>Network Scan</h2><p>Network scan complete.</p><h3>Available Wi-Fi Networks</h3><p>The following wi-fi networks were detected:"
        try:
            networks = self.sta_if.scan()
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
            html += f"<h2>Scan Error</h2><p>An error occurred while scanning Wi-Fi networks.<br>Error: {e}</p>"
        finally:
            self.sta_if.active(False)
        html += """<h3>Information</h3>
        <p>If the network you want is not listed, click <a href="/scan">Rescan</a> to scan again.</p>
        <p><a href='/'>Go Back</a></p>
        """
        return self.html_template("Goat - Captive Portal", html)

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
                self.sta_if.active(True)
                self.sta_if.connect(ssid, password)

                timeout = utime.time() + self.network_connection_timeout
                while not self.sta_if.isconnected() and utime.time() < timeout:
                    await asyncio.sleep(0.5)

                if self.sta_if.isconnected():
                    self.ip_address = self.sta_if.ifconfig()[0]
                    body = f"""<h2>Connected</h2>
                    <p>You successfully connected to {ssid}.</p>
                    <h2>Information</h2>
                    <p>The access point has been shut down and you can now close this page.</p>"""
                    return self.html_template("Goat - Captive Portal", body)
                else:
                    body = f"""<h2>Connection Failed</h2>
                    <p>Failed to connect to {ssid}.</p>"""
                    return self.html_template("Goat - Captive Portal", body)
            else:
                body = """<h2>Connection Error</h2>
                <p>The SSID or password for the wi-fi network was not provided.</p>"""
                return self.html_template("Goat - Captive Portal", body)
        except Exception as e:
            body = f"""<h2>Error</h2>
            <p>An error occurred: {e}</p>"""
            return self.html_template("Goat - Captive Portal", body)
        finally:
            if self.sta_if.isconnected():
                try:
                    await self.save_config(ssid, password)
                except Exception as e:
                    print(f"Error saving network configuration: {e}")

                try:
                    await self.stop_captive_portal_server()
                    await self.dns_server.stop_dns()
                    await self.stop_ap()
                except Exception as e:
                    print(f"Error stopping access point services: {e}")

                # Start STA web server
                if self.sta_web_server:
                    try:
                        self.server = await self.sta_web_server.run()
                    except Exception as e:
                        print(f"Error starting station web server: {e}")

    async def reconnect_to_wifi(self, request):
        """Reconnects to a saved Wi-Fi network."""
        try:
            if self.config_file in uos.listdir(self.config_directory):
                await self.load_config()

                if self.sta_if.isconnected():
                    body = """<h2>Reconnected</h2>
                    <p>You successfully reconnected to your saved network.</p>
                    <h2>Information</h2>
                    <p>The access point has been shut down and you can now close this page.</p>"""
                    return self.html_template("Goat - Captive Portal", body)
                else:
                    body = """<h2>Reconnection Failed</h2>
                    <p>Failed to reconnect to your saved network.</p>"""
                    return self.html_template("Goat - Captive Portal", body)
            else:
                body = """<h2>Configuration Error</h2>
                <p>There was an error locating your network configuration.<br>
                Please try manually reconnecting to the network.</p>"""
                return self.html_template("Goat - Captive Portal", body)
        except Exception as e:
            body = f"""<h2>Error</h2>
            <p>An error occurred: {e}</p>"""
            return self.html_template("Goat - Captive Portal", body)
        finally:
            if self.sta_if.isconnected():
                try:
                    await self.stop_captive_portal_server()
                    await self.dns_server.stop_dns()
                    await self.stop_ap()
                except Exception as e:
                    print(f"Error stopping access point services: {e}")

    async def disconnect_from_wifi(self):
        """Disconnects from the currently connected wireless network."""
        if not self.sta_if.isconnected():
            print("The network is not connected.")
            return;

        try:
            self.sta_if.active(False)
            self.sta_if.deinit()
            self.ip_address = None
        except Exception as e:
            print(f"Error disconnecting from wi-fi: {e}")

    def serve_index(self):
        """Serves the captive portal index page."""
        body = """<p>Welcome to the Goat - Captive Portal.<br>
        Use the portal to connect your Goat device to your wireless network.</p>"""

        if self.config_file in uos.listdir(self.config_directory):
            body += """<h2>Reconnect To Saved Network</h2>
            <p>An existing saved wireless network connection is configured for this system.<br>
            Click the 'Reconnect' button below to attempt to reconnect to your saved network.</p>
            <p><form action="/reconnect" method="post">
            <button type="submit">Reconnect</button>
            </form></p>"""

        body += """<h2>Connect To A Network</h2>
        <p>Click the link below to scan for networks:</p>
        <p><a href='/scan'>Start Scan</a></p>"""
        return self.html_template("Goat - Captive Portal", body)

    async def start_captive_portal_server(self):
        """Starts the captive portal HTTP server asynchronously."""
        if not self.ip_address:
            print("AP IP address not assigned. Cannot start server.")
            return

        try:
            self.server = await asyncio.start_server(self.handle_request, self.ip_address, self.captive_portal_http_port)
            print(f"Serving on {self.ip_address}:{self.captive_portal_http_port}")

            while True:
                await asyncio.sleep(1)  # Keep the server running
        except Exception as e:
            print(f"Error starting the captive portal server: {e}")

    async def stop_captive_portal_server(self):
        """Stops the captive portal HTTP server."""
        try:
            if self.server:
                self.server.close()
                await self.server.wait_closed()
                print("Server stopped.")
            else:
                print("Server already stopped.")
        except Exception as e:
            print(f"Error stopping server: {e}")

    async def run(self):
        """Runs the network manager initialization process and maintains connectivity."""
        try:
            await self.load_config()  # Load and attempt to connect to saved configuration

            while True:
                if not self.sta_if.isconnected():
                    print("Station disconnected, attempting reconnection...")
                    await self.load_config()  # Reload saved configuration and reconnect
                    if not self.sta_if.isconnected():
                        # Start AP if STA fails to reconnect
                        print("Switching to AP mode...")
                        await self.start_ap()
                        await self.start_captive_portal_server()
                        await self.dns_server.start_dns()

                # Check if both STA and AP are disconnected
                if not self.sta_if.isconnected() and not self.ap_if.isconnected():
                    print("No active connections. Rescanning...")
                    await asyncio.sleep(2)  # Pause before rescanning
                    continue

                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in network manager: {e}")
        finally:
            print("Cleaning up resources...")
            try:
                if self.sta_web_server:
                    print("Stopping STA web server...")
                    await self.sta_web_server.stop_server()
                if self.sta_if.isconnected():
                    print("Disconnecting from WiFi...")
                    await self.disconnect_from_wifi()
                if self.ap_if.isconnected():
                    print("Stopping access point services...")
                    await self.dns_server.stop_dns()
                    await self.stop_captive_portal_server()
                    await self.stop_ap()
            except Exception as cleanup_error:
                print(f"Error during cleanup: {cleanup_error}")
            await asyncio.sleep(0)  # Yield control after cleanup
