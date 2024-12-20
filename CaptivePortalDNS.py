# Goat - Captive Portal DNS server class
# Version 1.00
# © (c) 2024 Goat Technologies
# Description:
# Provides DNS services for the captive portal.

# Imports
import socket
import uasyncio as asyncio

# CaptivePortalDNS class
class CaptivePortalDNS:
    """Provides DNS services for the captive portal."""
    # Class constructor
    def __init__(self, portal_ip="192.168.4.1"):
        """Constructs the class and exposes properties."""
        self.dns_ip = portal_ip
        self.dns_port = 53
        self.udp_server = None

    async def start_dns(self):
        """Starts a simple DNS server to redirect all requests to the captive portal."""
        self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_server.bind(('', self.dns_port))
        print(f"DNS server started on port {self.dns_port}.")

        while True:
            try:
                # Receive DNS query
                data, addr = self.udp_server.recvfrom(512)
                if data:
                    print(f"DNS query received from {addr}")
                    # Construct a response
                    response = self.handle_dns_query(data)
                    self.udp_server.sendto(response, addr)
            except Exception as e:
                print(f"Error in DNS server: {e}")

    def handle_dns_query(self, data):
        """Parses a DNS query and constructs a response to redirect to the portal."""
        # DNS packet structure
        transaction_id = data[:2]  # Keep the transaction ID
        flags = b'\x81\x80'  # Standard DNS response, no error
        question_count = data[4:6]  # Number of questions (keep the same)
        answer_count = b'\x00\x01'  # One answer
        authority_rrs = b'\x00\x00'
        additional_rrs = b'\x00\x00'

        # Question section
        query_section = data[12:]  # Skip the header

        # Answer section
        answer_name = b'\xc0\x0c'  # Pointer to the domain name in the query
        answer_type = b'\x00\x01'  # Type A (host address)
        answer_class = b'\x00\x01'  # Class IN (Internet)
        ttl = b'\x00\x00\x00\x3c'  # Time-to-live: 60 seconds
        data_length = b'\x00\x04'  # IPv4 address is 4 bytes
        answer_ip = socket.inet_aton(self.dns_ip)  # Convert IP to bytes

        # Build the response
        dns_response = (
            transaction_id + flags + question_count + answer_count +
            authority_rrs + additional_rrs + query_section +
            answer_name + answer_type + answer_class + ttl +
            data_length + answer_ip
        )
        return dns_response

    async def stop_dns(self):
        """Stops the DNS server."""
        if self.udp_server:
            self.udp_server.close()
            self.udp_server = None
            print("DNS server stopped.")
