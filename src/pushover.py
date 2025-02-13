# Goat - Pushover - Notifications Library
# Version 1.1.6
# © (c) 2025 Goat Technologies
# https://github.com/CodeGoat-dev/SecureMe
# Description:
# Used by Goat firmware to send notifications via the Pushover push notifications platform.

# Imports
import uasyncio as asyncio
import urequests
import utils

# Validate Pushover API key
async def validate_api_key(app_token=None, api_key=None, timeout=5):
    """Validate a Pushover API key.

        Args:
        - app_token: The Pushover application token to use.
        - api_key: The Pushover API key to validate.
        - timeout: The request timeout in seconds.
        """
    if not utils.isPicoW():
        print("Unsupported device.")
        return False

    if not utils.isNetworkConnected():
        print("No internet connection available.")
        return False

    key_is_valid = False

    url = "https://api.pushover.net/1/users/validate.json"

    if not app_token:
        return key_is_valid

    if not api_key:
        return key_is_valid

    data_dict = {
        "token": app_token,
        "user": api_key,
    }
    data = utils.urlencode(data_dict).encode("utf-8")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    for attempt in range(3):  # Retry up to 3 times
        try:
            print(f"Attempt {attempt + 1}: Validating API key...")
            response = urequests.post(url, data=data, headers=headers, timeout =timeout)

            if response.status_code == 200:
                key_is_valid = True
                print("API key is valid.")
                return key_is_valid
            else:
                print(f"Invalid API key. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error validating API key (Attempt {attempt + 1}): {e}")
        finally:
            if 'response' in locals():
                response.close()
            await asyncio.sleep(0.5)  # Slight delay before retrying

    return key_is_valid

# Send push notifications using Pushover
async def send_notification(app_token=None, api_key=None, title="Goat - SecureMe", message=None, priority=0, timeout=5):
    """Send push notifications using Pushover.

        Args:
        - app_token: The Pushover application token to use.
        - api_key: The Pushover API key to use.
        - title: The title for the notification.
        - message: The message to send.
        - priority: The notification priority (0-2).
        - timeout: The request timeout in seconds.
        """

    await asyncio.sleep(0)

    if not utils.isPicoW():
        print("Unsupported device.")
        return

    if not utils.isNetworkConnected():
        print("No internet connection available.")
        return

    url = "https://api.pushover.net/1/messages.json"

    if not app_token:
        print("A Pushover app token is required to send push notifications.")
        return

    if not api_key:
        print("A Pushover API key is required to send push notifications.")
        return

    if not message:
        print("A message must be provided to send push notifications.")
        return

    data_dict = {
        "token": app_token,
        "user": api_key,
        "message": message,
        "priority": priority,
        "title": title
    }
    data = utils.urlencode(data_dict).encode("utf-8")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    for attempt in range(3):  # Retry up to 3 times
        try:
            print(f"Attempt {attempt + 1}: Sending notification...")
            response = urequests.post(url, data=data, headers=headers, timeout =timeout)

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
