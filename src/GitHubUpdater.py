# Goat - GitHub Updater library
# Version 1.0.0
# © (c) 2025 Goat Technologies

# Imports
import machine
import network
import uasyncio as asyncio
import urequests
import uos

class GitHubUpdater:
    """Provides online update functionality for device firmware."""
    def __init__(self, current_version, repo_url, update_interval=3600, auto_reboot=False):
        self.current_version = f"v{current_version}"
        self.repo_url = repo_url
        self.update_interval = update_interval
        self.auto_reboot = auto_reboot

        self.headers = {"User-Agent": "GoatGitHubUpdater/1.1"}
        self.latest_version = None
        self.files_to_download = []
        self.temp_dir = "/temp_update"  # Temporary directory for updates

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
            print("Checking for updates...")
            response = urequests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                self.latest_version = release_data['tag_name']
                print(f"Current version: {self.current_version}")
                print(f"Latest version: {self.latest_version}")

                # Get file list recursively from the 'src' directory
                contents_url = f"{self.repo_url}/contents/src?ref={self.latest_version}"
                self.files_to_download = await self.get_files_in_directory(contents_url)
            else:
                print(f"Failed to fetch release data: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"Error fetching update: {e}")

    async def get_files_in_directory(self, url):
        """Fetch the list of files in a given directory recursively."""
        files = []
        try:
            response = urequests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                contents = response.json()
                for item in contents:
                    if item['type'] == 'file':  # Add files with their relative paths
                        files.append({"url": item['download_url'], "path": item['path']})
                    elif item['type'] == 'dir':  # Recurse into subdirectories
                        sub_files = await self.get_files_in_directory(item['url'])
                        files.extend(sub_files)
            else:
                print(f"Failed to fetch directory contents: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"Error fetching directory contents: {e}")
        return files

    def create_temp_dir(self):
        """Create a temporary directory for downloads."""
        try:
            if not self.temp_dir in uos.listdir("/"):
                uos.mkdir(self.temp_dir)
            print(f"Temporary directory '{self.temp_dir}' created.")
        except Exception as e:
            print(f"Error creating temporary directory: {e}")

    async def download_update(self):
        """Downloads the latest firmware version files to a temporary directory."""
        if self.files_to_download:
            print(f"Downloading {len(self.files_to_download)} files...")
            self.create_temp_dir()
            try:
                for file_info in self.files_to_download:
                    download_url = file_info["url"]
                    relative_path = file_info["path"]
                    temp_file_path = f"{self.temp_dir}/{relative_path}"

                    # Ensure directories exist in temporary storage
                    dir_path = "/".join(temp_file_path.split("/")[:-1])
                    if not uos.path.exists(dir_path):
                        self.create_directories(dir_path)

                    # Stream the file and write in chunks
                    response = urequests.get(download_url, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        with open(temp_file_path, 'wb') as file:
                            # Access raw socket stream to fetch data in chunks
                            sock = response.raw
                            while True:
                                chunk = sock.read(1024)  # Stream 1KB chunks
                                if not chunk:
                                    break
                                file.write(chunk)
                        print(f"Downloaded {relative_path} to temporary directory.")
                    else:
                        print(f"Error downloading {download_url}: {response.status_code}")
                    response.close()

                # Move files to the root if all downloads succeed
                self.move_files_to_root()
            except Exception as e:
                print(f"Error downloading update: {e}")
        else:
            print("No files to download.")

    def move_files_to_root(self):
        """Move files from the temporary directory to the root filesystem."""
        try:
            for root, dirs, files in uos.walk(self.temp_dir):
                for file_name in files:
                    temp_file_path = f"{root}/{file_name}"
                    relative_path = temp_file_path[len(self.temp_dir) + 1:]  # Remove temp_dir prefix
                    final_file_path = f"/{relative_path}"

                    # Ensure directories exist in the root filesystem
                    dir_path = "/".join(final_file_path.split("/")[:-1])
                    if not uos.path.exists(dir_path):
                        self.create_directories(dir_path)

                    uos.rename(temp_file_path, final_file_path)
                    print(f"Moved {relative_path} to root directory.")

            # Cleanup temporary directory
            self.cleanup_temp_dir()
            print("Temporary directory cleaned up.")
        except Exception as e:
            print(f"Error moving files to root: {e}")

    def create_directories(self, path):
        """Create directories recursively."""
        parts = path.split("/")
        for i in range(2, len(parts) + 1):
            dir_path = "/".join(parts[:i])
            if not uos.path.exists(dir_path):
                uos.mkdir(dir_path)

    def cleanup_temp_dir(self):
        """Recursively delete the temporary directory and its contents."""
        try:
            for root, dirs, files in uos.walk(self.temp_dir, topdown=False):
                for file_name in files:
                    uos.remove(f"{root}/{file_name}")
                for dir_name in dirs:
                    uos.rmdir(f"{root}/{dir_name}")
            uos.rmdir(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temporary directory: {e}")

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
            print(f"Update complete to version {self.current_version}")
            if self.auto_reboot:
                print("Restarting...")
                machine.reset()
        else:
            print("No updates available.")

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
