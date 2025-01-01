# Goat - Network Manager DNS server class
# Version 1.0.0
# © (c) 2024-2025 Goat Technologies
# Description:
# Provides DNS services for the captive portal provided by the Goat - Network Manager.

# Imports
import socket
import uasyncio as asyncio

# NetworkManagerDNS class
class NetworkManagerDNS:
    """Provides DNS services for the captive portal provided by the Goat - Network Manager."""
    # Class constructor
    def __init__(self, portal_ip="192.168.4.1", dns_port=53):
        """Constructs the class and exposes properties."""
        self.dns_ip = portal_ip
        self.dns_port = dns_port

        self.udp_server = None
        self.buffer_size = 512  # Default DNS packet size

    async def start_dns(self):
        """Starts a simple DNS server to redirect all requests to the captive portal."""
        try:
            self.udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_server.setblocking(False)  # Non-blocking mode
            self.udp_server.bind((self.dns_ip, self.dns_port))
            print(f"DNS server started listening on IP address {self.dns_ip} port {self.dns_port}.")

            while True:
                try:
                    data, addr = await self._receive_from()
                    if data:
                        print(f"DNS query received from {addr}")
                        response = self.handle_dns_query(data)
                        await self._send_to(response, addr)
                except Exception as e:
                    print(f"Error handling DNS query: {e}")
        except Exception as e:
            print(f"Error starting DNS server: {e}")
        finally:
            if self.udp_server:
                self.udp_server.close()
                print("DNS server socket closed.")

    async def _receive_from(self):
        """Non-blocking wrapper for receiving data."""
        while True:
            try:
                data, addr = self.udp_server.recvfrom(self.buffer_size)
                return data, addr
            except OSError as e:
                if e.errno != 11:  # EAGAIN or EWOULDBLOCK
                    raise
                await asyncio.sleep(0)  # Yield to the event loop

    async def _send_to(self, data, addr):
        """Non-blocking wrapper for sending data."""
        while True:
            try:
                self.udp_server.sendto(data, addr)
                return
            except OSError as e:
                if e.errno != 11:  # EAGAIN or EWOULDBLOCK
                    raise
                await asyncio.sleep(0)  # Yield to the event loop

    def handle_dns_query(self, data):
        """Parses a DNS query and constructs a response to redirect to the portal."""
        try:
            transaction_id = data[:2]  # Transaction ID
            flags = b'\x81\x80'  # Standard DNS response, no error
            question_count = data[4:6]
            answer_count = b'\x00\x01'
            authority_rrs = b'\x00\x00'
            additional_rrs = b'\x00\x00'

            # Extract query section and domain name
            query_section = data[12:]
            domain_name = self._decode_domain_name(query_section)
            print(f"Handling DNS query for domain: {domain_name}")

            # Answer section
            answer_name = b'\xc0\x0c'  # Pointer to domain name in query
            answer_type = b'\x00\x01'  # Type A
            answer_class = b'\x00\x01'  # Class IN
            ttl = b'\x00\x00\x00\x3c'  # Time-to-live: 60 seconds
            data_length = b'\x00\x04'  # IPv4 address size
            answer_ip = socket.inet_aton(self.dns_ip)

            # Build the response
            dns_response = (
                transaction_id + flags + question_count + answer_count +
                authority_rrs + additional_rrs + query_section +
                answer_name + answer_type + answer_class + ttl +
                data_length + answer_ip
            )
            return dns_response
        except Exception as e:
            print(f"Error handling DNS query: {e}")
            return b''

    def _decode_domain_name(self, query_section):
        """Decodes the domain name from the query section."""
        domain_parts = []
        i = 0
        while query_section[i] != 0:
            length = query_section[i]
            i += 1
            domain_parts.append(query_section[i:i+length].decode())
            i += length
        return '.'.join(domain_parts)

    async def stop_dns(self):
        """Stops the DNS server."""
        if self.udp_server:
            self.udp_server.close()
            self.udp_server = None
            print("DNS server stopped.")
