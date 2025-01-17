# Goat - GitHub Updater library
# Version 1.0.0
# © (c) 2025 Goat Technologies
# Description:
# Provides online update functionality for your device firmware.
# Designed for the Raspberry Pi Pico W microcontroller.
# Includes periodic update checking and automatic update download.

# Imports
import machine
import uasyncio as asyncio
import urequests
import uos

# GitHubUpdater class
class GitHubUpdater:
    """Provides online update functionality for device firmware."""
    def __init__(self, current_version, repo_url, update_interval=3600, auto_reboot=False):
        self.current_version = current_version
        self.repo_url = repo_url
        self.update_interval = update_interval
        self.auto_reboot = auto_reboot

        self.latest_version = None
        self.latest_release_url = None

    async def check_for_update(self):
        """Checks for updates from GitHub."""
        url = f"{self.repo_url}/releases/latest"
        try:
            print("Checking for updates...")
            response = urequests.get(url)
            if response.status_code == 200:
                release_data = response.json()
                self.latest_version = release_data['tag_name']
                self.latest_release_url = release_data['tarball_url']
                print(f"Latest version: {self.latest_version}")
            else:
                print(f"Failed to fetch release data: {response.status_code}")
            response.close()
        except Exception as e:
            print(f"Error fetching update: {e}")

    async def download_update(self):
        """Downloads the latest firmware version from GitHub."""
        if self.latest_version:
            print(f"Downloading update {self.latest_version}...")
            try:
                response = urequests.get(self.latest_release_url)
                if response.status_code == 200:
                    with open('/update.tar.gz', 'wb') as file:
                        file.write(response.content)
                    print("Update downloaded successfully.")
                else:
                    print(f"Error downloading update: {response.status_code}")
                response.close()
            except Exception as e:
                print(f"Error downloading update: {e}")

    def decompress_gzip(self, gzip_file, output_file):
        """Decompresses a .gz file into a .tar file."""
        try:
            print("Decompressing gzip file...")
            with open(gzip_file, 'rb') as gz, open(output_file, 'wb') as out:
                # Skip the 10-byte Gzip header
                gz.read(10)
                while True:
                    chunk = gz.read(1024)
                    if not chunk:
                        break
                    out.write(chunk)
            print("Decompression complete.")
            uos.remove(gzip_file)  # Clean up the original gzip file
        except Exception as e:
            print(f"Error during decompression: {e}")

    def extract_tar(self, tar_file, dest="/"):
        """Extracts a .tar file to the specified destination."""
        try:
            print("Extracting tar file...")
            with open(tar_file, 'rb') as f:
                while True:
                    header = f.read(512)
                    if len(header) < 512 or header == b'\0' * 512:
                        break

                    file_name = header[0:100].decode('utf-8').strip('\0')
                    file_size = int(header[124:136].strip(b'\0').decode('utf-8'), 8)

                    if file_name.startswith("src/"):  # Only process files in the "src" directory
                        dest_path = uos.path.join(dest, file_name[4:])
                        if file_name.endswith('/'):  # Directory
                            uos.makedirs(dest_path, exist_ok=True)
                        else:  # File
                            uos.makedirs(uos.path.dirname(dest_path), exist_ok=True)
                            with open(dest_path, 'wb') as out_file:
                                out_file.write(f.read(file_size))
                            # Align to 512-byte blocks
                            padding = (512 - (file_size % 512)) % 512
                            f.read(padding)
            print("Extraction complete.")
            uos.remove(tar_file)  # Clean up the tar file
        except Exception as e:
            print(f"Error extracting update: {e}")

    async def is_update_available(self):
        """Check if a firmware update is available for download."""
        return self.latest_version and self.current_version != self.latest_version

    async def update(self):
        """Update device firmware from GitHub."""
        await self.check_for_update()
        if await self.is_update_available():
            await self.download_update()
            self.decompress_gzip('/update.tar.gz', '/update.tar')
            self.extract_tar('/update.tar')
            self.current_version = self.latest_version
            print(f"Update complete to version {self.current_version}")
            if self.auto_reboot:
                print("Restarting...")
                machine.reset()
        else:
            print("No updates available.")

    async def run_periodically(self):
        """Periodically update device firmware from GitHub."""
        while True:
            await self.update()
            await asyncio.sleep(self.update_interval)
