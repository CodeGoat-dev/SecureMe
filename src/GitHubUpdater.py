# Goat - GitHub Updater library
# Version 1.1.0
# © (c) 2025 Goat Technologies

# Imports
import machine
import network
import uasyncio as asyncio
import urequests
import uos
import mip

class GitHubUpdater:
    """Provides online update functionality for device firmware using MIP."""
    def __init__(self, current_version, repo_url, update_interval=3600, auto_reboot=False):
        self.current_version = f"v{current_version}"
        self.repo_url = repo_url
        self.update_interval = update_interval
        self.auto_reboot = auto_reboot

        self.headers = {"User-Agent": "GoatGitHubUpdater/1.1"}
        self.latest_version = None
        self.files_to_download = []

    def isNetworkConnected(self):
        """Check if the network interface is connected."""
        try:
            sta = network.WLAN(network.STA_IF)
            return sta.isconnected()
        except Exception:
            return False

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
            await self.download_update()
            self.current_version = self.latest_version
            print(f"Firmware update complete. Updated to version {self.current_version}")
            if self.auto_reboot:
                print("Restarting system...")
                machine.reset()
        else:
            print("No firmware updates available.")

    async def run_periodically(self):
        """Periodically update device firmware from GitHub."""
        print("Initializing automatic update...")

        await asyncio.sleep(30)  # Delay before starting

        while True:
            if not self.isNetworkConnected():
                print("The network is not currently connected. Retrying in 10 seconds.")
                await asyncio.sleep(10)
            await self.update()
            await asyncio.sleep(self.update_interval)
