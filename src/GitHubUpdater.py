# Goat - GitHub Updater library
# Version 1.0.0
# © (c) 2025 Goat Technologies
# Description:
# Provides online update functionality for your device firmware.
# Designed for the Raspberry Pi Pico W microcontroller.
# Includes periodic update checking and automatic update download.

# Imports
import machine
import network
import uasyncio as asyncio
import urequests
import uos

class GitHubUpdater:
    """Provides online update functionality for device firmware."""
    def __init__(self, current_version, repo_url, update_interval=3600, auto_reboot=False):
        self.current_version = current_version
        self.repo_url = repo_url
        self.update_interval = update_interval
        self.auto_reboot = auto_reboot

        self.latest_version = None
        self.latest_release_url = None
        self.files_to_download = []

    def isNetworkConnected(self):
        """Check if the network interface is connected."""
        try:
            sta = network.WLAN(network.STA_IF)
            if sta.isconnected():
                return True  # Network is connected
            else:
                return False  # Network is not connected
        except Exception as e:
            return False

    async def check_for_update(self):
        """Checks for updates from GitHub."""
        url = f"{self.repo_url}/releases/latest"
        try:
            print("Checking for updates...")
            response = urequests.get(url, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                self.latest_version = release_data['tag_name']
                print(f"Latest version: {self.latest_version}")

                # List files in the 'src' directory for the release
                contents_url = f"{self.repo_url}/contents/src?ref={self.latest_version}"
                self.files_to_download = await self.get_files_in_directory(contents_url)
            else:
                print(f"Failed to fetch release data: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"Error fetching update: {e}")

    async def get_files_in_directory(self, url):
        """Fetch the list of files in a given directory."""
        files = []
        try:
            response = urequests.get(url, timeout=10)
            if response.status_code == 200:
                contents = response.json()
                for item in contents:
                    if item['type'] == 'file':  # Only consider files
                        files.append(item['download_url'])
            else:
                print(f"Failed to fetch directory contents: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"Error fetching directory contents: {e}")
        return files

    async def download_update(self):
        """Downloads the latest firmware version files from GitHub."""
        if self.files_to_download:
            print(f"Downloading {len(self.files_to_download)} files...")
            try:
                for file_url in self.files_to_download:
                    response = urequests.get(file_url, timeout=10)
                    if response.status_code == 200:
                        # Determine the file path and save it
                        file_name = file_url.split('/')[-1]
                        with open(f"/{file_name}", 'wb') as file:
                            file.write(response.content)
                        print(f"Downloaded {file_name} successfully.")
                    else:
                        print(f"Error downloading {file_url}: {response.status_code}")
                    response.close()
            except Exception as e:
                print(f"Error downloading update: {e}")
        else:
            print("No files to download.")

    async def is_update_available(self):
        """Check if a firmware update is available for download."""
        return self.latest_version and self.current_version != self.latest_version

    async def update(self):
        """Update device firmware from GitHub."""
        if not self.isNetworkConnected():
            return

        await self.check_for_update()
        if await self.is_update_available():
            await self.download_update()
            self.current_version = self.latest_version
            print(f"Update complete to version {self.current_version}")
            if self.auto_reboot:
                print("Restarting...")
                machine.reset()
        else:
            print("No updates available.")

    async def run_periodically(self):
        """Periodically update device firmware from GitHub."""
        print("Initializing automatic update...")
        while True:
            if not self.isNetworkConnected():
                print("The network is not currently connected. Retrying in 10 seconds.")
                await asyncio.sleep(10)
            await self.update()
            await asyncio.sleep(self.update_interval)
