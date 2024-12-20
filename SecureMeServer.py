# Goat - SecureMe Server class
# Version 1.00
# © (c) 2024 Goat Technologies
# Description:
# Provides the web server for the Goat - SecureMe firmware.

# Imports
import network
import uasyncio as asyncio
import utime

# SecureMeServer class
class SecureMeServer:
    """Provides the web server for the Goat - SecureMe firmware."""
    # Class constructor
    def __init__(self, ip_address="0.0.0.0", http_port=8000):
        """Constructs the class and exposes properties."""
        self.ip_address = ip_address
        self.server = None
        self.http_port = http_port

    def html_template(self, title, body):
        """Generates an HTML page template."""
        return f"""<html>
        <head><title>{title}</title></head>
        <body>
        <h1>{title}</h1>
        {body}
        <p>© (c) 2024 Goat Technologies</p>
        </body>
        </html>"""

    async def handle_request(self, reader, writer):
        """Handles incoming HTTP requests for the web server."""
        try:
            request = await reader.read(1024)
            request = request.decode()
            print("Request:", request)

            # Handle web server endpoints
            if "GET /" in request:
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + self.serve_index()

            # Write the response
            writer.write(response.encode())
            await writer.drain()
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    def serve_index(self):
        """Serves the web server index page."""
        body = """<p>Welcome  to the Goat - SecureMe - Portable Security System.<br>
        More functionality will be added here soon.</p>"""
        return self.html_template("Welcome", body)

    async def start_server(self):
        """Starts the SecureMe HTTP server asynchronously."""
        if not self.ip_address:
            print("IP address not assigned. Cannot start server.")
            return

        try:
            self.server = await asyncio.start_server(self.handle_request, self.ip_address, self.http_port)
            print(f"Serving on {self.ip_address}:{self.http_port}")

            while True:
                await asyncio.sleep(1)  # Keep the server running
        except Exception as e:
            print(f"Error starting server: {e}")

    async def stop_server(self):
        """Stops the SecureMe HTTP server."""
        try:
            if self.server:
                await self.server.await_closed()
                print("Server stopped.")
            else:
                print("Server already stopped.")
        except Exception as e:
            print(f"Error stopping server: {e}")

    async def run(self):
        """Runs the SecureMe web server initialization process and maintains connectivity."""
        try:
            await self.start_server()

            # Keep the web server active
            while True:
                await asyncio.sleep(0.05)
        except Exception as e:
            print(f"Error starting the SecureMe web server: {e}")
        finally:
            await self.stop_server()
