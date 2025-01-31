# Goat - GitHub Updater library
# Version 1.1.3
# © (c) 2025 Goat Technologies
# https://github.com/CodeGoat-dev/SecureMe
# Description:
# Provides automatic firmware update functionality for the Goat - SecureMe firmware.

# Imports
import machine
import network
import uasyncio as asyncio
import urequests
import uos
import mip
from ConfigManager import ConfigManager

class GitHubUpdater:
    """Provides online update functionality for device firmware using MIP."""
    def __init__(self, current_version, repo_url, update_interval=3600, auto_reboot=False):
        self.current_version = f"v{current_version}"
        self.repo_url = repo_url
        self.update_interval = update_interval
        self.auto_reboot = auto_reboot

        self.config_directory = "/config"
        self.config_file = "secureme.conf"
        self.network_config_file = "network_config.conf"

        self.pushover_app_token = None
        self.pushover_api_key = None
        self.system_status_notifications = None
        self.update_notifications = None
        self.enable_auto_update = None
       self.update_check_interval = None
        self.default_update_check_interval = 30

        self.headers = {"User-Agent": "GoatGitHubUpdater/1.1"}
        self.latest_version = None
        self.files_to_download = []

    async def initialize(self):
        """Initializes the server by loading configuration data."""
        self.config = ConfigManager(self.config_directory, self.config_file)
        await self.config.read_async()

        self.pushover_app_token = self.config.get_entry("pushover", "app_token")
        self.pushover_api_key = self.config.get_entry("pushover", "api_key")
        self.system_status_notifications = self.config.get_entry("pushover", "system_status_notifications")
        if not isinstance(self.system_status_notifications, bool):
            self.system_status_notifications = True
            self.config.set_entry("pushover", "system_status_notifications", self.system_status_notifications)
            await self.config.write_async()
        self.update_notifications = self.config.get_entry("pushover", "update_notifications")
        if not isinstance(self.update_notifications, bool):
            self.update_notifications = True
            self.config.set_entry("pushover", "update_notifications", self.update_notifications)
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

        self.config_watcher = asyncio.create_task(self.config.start_watching())

    def isNetworkConnected(self):
        """Check if the network interface is connected."""
        try:
            sta = network.WLAN(network.STA_IF)
            return sta.isconnected()
        except Exception:
            return False

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
        data = self.urlencode(data_dict).encode("utf-8")
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

    def urlencode(self, data):
        """Encode a dictionary into a URL-encoded string."""
        return "&".join(f"{key}={value}" for key, value in data.items())

    async def check_for_update(self):
        """Checks for updates from GitHub."""
        url = f"{self.repo_url}/releases/latest"
        try:
            print("Checking for firmware updates...")
            response = urequests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                self.latest_version = release_data['tag_name']
                print(f"Current version: {self.current_version}")
                print(f"Latest version: {self.latest_version}")

                # Get file list from the 'build' directory
                contents_url = f"{self.repo_url}/contents/build?ref={self.latest_version}"
                self.files_to_download = await self.get_files_in_directory(contents_url)
            else:
                print(f"Failed to fetch firmware release information: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"Error checking for firmware updates: {e}")

    async def get_files_in_directory(self, url):
        """Fetch the list of files in a given directory recursively."""
        files = []

        try:
            response = urequests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                contents = response.json()
                for item in contents:
                    if item['type'] == 'file':  # Add files with their download URLs
                        files.append({"url": item['download_url'], "path": item['path']})
                    elif item['type'] == 'dir':  # Recurse into subdirectories
                        sub_files = await self.get_files_in_directory(item['url'])
                        files.extend(sub_files)
            else:
                print(f"Failed to fetch update contents: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"Error fetching update contents: {e}")

        return files

    async def download_update(self):
        """Downloads and installs firmware files using MIP."""
        if not self.files_to_download:
            print("No files to download.")
            return

        print(f"Installing firmware update...")

        try:
            for file_info in self.files_to_download:
                download_url = file_info["url"]
                print(f"Installing dependency: {download_url}...")

                try:
                    mip.install(download_url, target="/")
                    print(f"Successfully installed dependency: {download_url}")
                except Exception as e:
                    print(f"Failed to install dependency: {download_url}: {e}")
        
            print("All dependencies installed successfully.")
        except Exception as e:
            print(f"Error during firmware update installation: {e}")

    async def is_update_available(self):
        """Check if a firmware update is available for download."""
        if self.latest_version:
            # Strip 'v' prefix and split versions into parts
            current_version_parts = [int(x) for x in self.current_version.lstrip('v').split('.')]
            latest_version_parts = [int(x) for x in self.latest_version.lstrip('v').split('.')]

            # Compare versions part by part
            for current, latest in zip(current_version_parts, latest_version_parts):
                if latest > current:
                    return True
                elif latest < current:
                    return False

            # Check if latest has additional parts (e.g., "1.2" < "1.2.1")
            return len(latest_version_parts) > len(current_version_parts)
        else:
            return False

    async def update(self):
        """Update device firmware from GitHub."""
        if not self.isNetworkConnected():
            return

        await self.check_for_update()
        if await self.is_update_available():
            if self.system_status_notifications:
                if self.update_notifications:
                    asyncio.create_task(self.send_system_status_notification(status_message=f"Firmware update available. Updating from {self.current_version} to {self.latest_version}"))
            await self.download_update()
            self.current_version = self.latest_version
            print(f"Firmware update complete. Updated to version {self.current_version}")
            if self.system_status_notifications:
                if self.update_notifications:
                    asyncio.create_task(self.send_system_status_notification(status_message=f"Firmware update complete. Updated to {self.latest_version}."))
            if self.auto_reboot:
                print("Restarting system...")
                await asyncio.sleep(10)  # Delay before rebooting
                machine.reset()
        else:
            print("No firmware updates available.")

    async def run_periodically(self):
        """Periodically update device firmware from GitHub."""
        print("Initializing automatic update...")

        await self.initialize()

        await asyncio.sleep(30)  # Delay before starting

        while True:
            if not self.isNetworkConnected():
                print("The network is not currently connected. Retrying in 10 seconds.")
                await asyncio.sleep(10)
            if self.enable_auto_update:
                await self.update()
            await asyncio.sleep(self.update_check_interval)
