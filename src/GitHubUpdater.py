# Goat - GitHub Updater library
# Version 1.1.6
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
import pushover
import utils

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

    async def check_for_update(self):
        """Checks for updates from GitHub with retry and error handling."""
        url = f"{self.repo_url}/releases/latest"
        attempts = 0

        while attempts < 3:
            try:
                print("Checking for firmware updates...")
                response = urequests.get(url, headers=self.headers, timeout=10)

                if response.status_code == 403:
                    print("GitHub API rate limit reached. Try again later.")
                    response.close()
                    return
                
                if response.status_code == 200:
                    release_data = response.json()
                    self.latest_version = release_data['tag_name']
                    print(f"Current version: {self.current_version}")
                    print(f"Latest version: {self.latest_version}")
                    response.close()

                    # Get file list from the 'build' directory
                    contents_url = f"{self.repo_url}/contents/build?ref={self.latest_version}"
                    try:
                        self.files_to_download = await self.get_files_in_directory(contents_url)
                    except Exception as e:
                        print(f"Unable to fetch update contents: {e}")

                    return  # Success, exit retry loop
                else:
                    print(f"Failed to fetch firmware release info: {response.status_code}")
                    response.close()
            except Exception as e:
                print(f"Attempt {attempts + 1}: Error checking for firmware updates: {e}")
            finally:
                if response:
                    response.close()

            await asyncio.sleep(2)

            attempts += 1

        print("All attempts to fetch firmware update information failed.")

    async def get_files_in_directory(self, url):
        """Fetch the list of files in a given directory recursively."""
        files = []
        attempts = 0

        while attempts < 3:
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

                    response.close()
                    return files  # Exit retry loop on success
                else:
                    print(f"Failed to fetch update contents: {response.status_code}")
                    response.close()
            except Exception as e:
                print(f"Attempt {attempts + 1}: Error fetching update contents: {e}")
            finally:
                if response:
                    response.close()

            await asyncio.sleep(2)  # Small delay before retry
            attempts += 1

        print("Failed to retrieve update contents after multiple attempts.")
        return files

    async def download_update(self):
        """Downloads and installs firmware files using MIP."""
        if not self.files_to_download:
            print("No files to download.")
            return

        print(f"Installing firmware update...")

        for file_info in self.files_to_download:
            download_url = file_info["url"]
            print(f"Installing dependency: {download_url}...")

            attempts = 0
            while attempts < 3:
                try:
                    mip.install(download_url, target="/")
                    print(f"Successfully installed dependency: {download_url}")
                    break  # Exit retry loop on success
                except Exception as e:
                    attempts += 1
                    print(f"Attempt {attempts}: Failed to install {download_url}: {e}")

                    if attempts == 3:
                        print(f"Failed to install {download_url} after {attempts} attempts.")

            await asyncio.sleep(1)  # Short delay before the next install

        print("Firmware update process completed.")

    async def is_update_available(self):
        """Check if a firmware update is available for download."""
        if self.latest_version:
            # Strip 'v' prefix and convert to tuples (e.g., "1.2.3" -> (1,2,3))
            current_version_tuple = tuple(map(int, self.current_version.lstrip('v').split('.')))
            latest_version_tuple = tuple(map(int, self.latest_version.lstrip('v').split('.')))

            return latest_version_tuple > current_version_tuple  # Tuple comparison works natively
        return False

    async def update(self):
        """Update device firmware from GitHub."""
        if not utils.isPicoW():
            return

        if not utils.isNetworkConnected():
            return

        if utils.isRP2040():
            utils.defragment_memory()

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

            self.enable_auto_update = self.config.get_entry("update", "enable_auto_update")
            self.update_check_interval = self.config.get_entry("update", "update_check_interval")

            if self.enable_auto_update:
                await self.update()

            await asyncio.sleep(self.update_check_interval*60)
