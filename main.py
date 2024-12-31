# Goat SecureMe
# Portable Security System
# Version 1.0.0
# © (c) 2024 Goat Technologies
# Description:
# A portable, movable mini security system for personal property protection.
# Includes PIR sensing and tilt sensing
# Provides button configurable settings to control arming and alarm sound
# Includes security code support facilitated by matrix keypad
# Designed for Raspberry Pi Pico based microcontrollers.

# Imports
from machine import Pin, PWM, reset
import os
import time
import utime
import uasyncio as asyncio
import uos
from ConfigManager import ConfigManager
import utils

# Conditional imports
if utils.isPicoW():
    import urequests
    from NetworkManager import NetworkManager
    from SecureMeServer import SecureMeServer

# Pin constants
if utils.isPicoW():
    LED_PIN = "LED"
else:
    LED_PIN = 25
BUZZER_PIN = 1
PIR_PIN = 2
TILT_SWITCH_PIN = 3
ARM_BUTTON_PIN = 4
ALARM_TEST_BUTTON_PIN = 5
ALARM_SOUND_BUTTON_PIN = 6
VOLUME_DOWN_BUTTON_PIN = 15
VOLUME_UP_BUTTON_PIN = 16

# Define the GPIO pins for keypad rows and columns
keypad_row_pins = [7, 8, 9, 10]
keypad_col_pins = [11, 12, 13, 14]

# Configure required pins
led = Pin(LED_PIN, Pin.OUT)
buzzer = PWM(Pin(BUZZER_PIN))
arm_button = Pin(ARM_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
alarm_test_button = Pin(ALARM_TEST_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
alarm_sound_button = Pin(ALARM_SOUND_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
volume_down_button = Pin(VOLUME_DOWN_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
volume_up_button = Pin(VOLUME_UP_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
pir = Pin(PIR_PIN, Pin.IN, Pin.PULL_DOWN)
tilt = Pin(TILT_SWITCH_PIN, Pin.IN, Pin.PULL_UP)

# Initialize keypad row pins as outputs
keypad_rows = [Pin(pin, Pin.OUT) for pin in keypad_row_pins]
# Initialize keypad column pins as inputs
keypad_cols = [Pin(pin, Pin.IN, Pin.PULL_DOWN) for pin in keypad_col_pins]

# Global variables
config_directory = "/config"
config_file = "secureme.conf"
network_config_file = "network_config.conf"

tasks = []

pir_warmup_time = 60

pir_timeout = None
tilt_timeout = None

enable_detect_motion = True
enable_detect_tilt = True
sensor_cooldown = 10
default_sensor_cooldown = 10

is_armed = True
alarm_active = False
alarm_sound = 0
silent_alarm = False

default_buzzer_volume = 3072
buzzer_volume = 3072

security_code = "0000"
entering_security_code = False
security_code_max_entry_attempts = 3
security_code_min_length = 4
security_code_max_length = 8

pushover_app_token = "ahptofxmi4fg8mhadwpebbb559vovo"
pushover_api_key = None

keypad_locked = True

keypad_characters = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

# Dynamic bell player
async def play_dynamic_bell(frequency, initial_volume, loop_delay=0.1, times=5):
    """
    Plays a dynamic bell sound using a buzzer with decreasing volume.
    
    Args:
    - frequency: Frequency of the tone in Hz
    - initial_volume: Initial volume (range 0-65535 for duty cycle)
    - loop_delay: Delay between loops in seconds (default 0.1s)
    - times: Number of times to play (default 5)
    """
    # Number of steps to decrease volume and the duration per step
    steps = 100
    duration_per_step = 1 / steps  # Time per step

    try:    
        # Configure the buzzer
        buzzer.duty_u16(initial_volume)
        buzzer.freq(frequency)

        for _ in range(times):
            led.value(1)

            for step in range(steps):
                # Calculate the volume for the current step
                volume = int(initial_volume * (1 - step / steps))
                buzzer.duty_u16(volume)
                await asyncio.sleep(duration_per_step)

            led.value(0)

            buzzer.duty_u16(0)  # Turn off the buzzer

            if times > 1:
                await asyncio.sleep(loop_delay)
    except Exception as e:
        print(f"Error in play_dynamic_bell: {e}")
    finally:
        buzzer.duty_u16(0)  # Turn off the buzzer

async def play_alarm(alarm_type="sweep", start_freq=500, end_freq=3000, cycles=10, step=50, duration=0.01):
    """
    Plays an alarm sound based on the specified type.
    
    Args:
    - alarm_type: Type of alarm ("sweep" or "high_low").
    - start_freq: Starting frequency of the sweep in Hz (default 500, for sweep alarm).
    - end_freq: Ending frequency of the sweep in Hz (default 3000, for sweep alarm).
    - cycles: Number of times to sweep between start and end frequencies (default 10, for sweep alarm).
    - step: Frequency increment/decrement step (default 50 Hz, for sweep alarm).
    - duration: Duration to hold each frequency step in seconds (default 0.01s, for sweep alarm).
    """
    global alarm_active

    try:
        if buzzer_volume is None or buzzer_volume == 0:
            raise ValueError("Invalid buzzer volume.")

        buzzer.duty_u16(buzzer_volume)

        if alarm_type == "sweep":
            for _ in range(cycles):
                # Sweep up
                for freq in range(start_freq, end_freq, step):
                    buzzer.freq(freq)
                    await asyncio.sleep(duration)
                # Sweep down
                for freq in range(end_freq, start_freq, -step):
                    buzzer.freq(freq)
                    await asyncio.sleep(duration)

        elif alarm_type == "sweep_up":
            for _ in range(cycles):
                # Sweep up
                for freq in range(start_freq, end_freq, step):
                    buzzer.freq(freq)
                    await asyncio.sleep(duration)

        elif alarm_type == "sweep_down":
                # Sweep down
                for freq in range(end_freq, start_freq, -step):
                    buzzer.freq(freq)
                    await asyncio.sleep(duration)

        elif alarm_type == "high_low":
            for _ in range(3):
                buzzer.freq(5000)  # Higher pitch
                led.value(1)
                await asyncio.sleep(0.5)
                buzzer.freq(500)  # Lower pitch
                led.value(0)
                await asyncio.sleep(0.5)

        else:
            raise ValueError(f"Unsupported alarm type: {alarm_type}")

        # Turn off the buzzer after the alarm
        buzzer.duty_u16(0)
    except Exception as e:
        print(f"Error in play_alarm: {e}")
    finally:
        # Ensure the buzzer is off
        buzzer.duty_u16(0)

# Alarm method
async def alarm(message):
    """Run the alarm when a sensor detects motion."""
    global alarm_active, alarm_sound, entering_security_code

    if not message:
        return

    if alarm_active:
        return

    if entering_security_code:
        return

    alarm_active = True

    try:
        alarm_sound = config.get_entry("alarm", "alarm_sound")

        if not alarm_sound == 0 and not alarm_sound == 1 and not alarm_sound == 2 and not alarm_sound == 3:
            alarm_sound = 0
            config.set_entry("alarm", "alarm_sound", alarm_sound)
            await config.write_async()

        if buzzer_volume is None or buzzer_volume == 0:
            raise ValueError("Invalid buzzer volume.")

        if utils.isPicoW():
            if silent_alarm:
                await send_pushover_notification(message=message)
                alarm_active = False
                return

        buzzer.duty_u16(buzzer_volume)

        for _ in range(3):
            if not alarm_active:  # Check if alarm should stop
                buzzer.duty_u16(0)  # Turn off buzzer
                alarm_active = False
                break

            if entering_security_code:  # Check if alarm should stop
                buzzer.duty_u16(0)  # Turn off buzzer
                alarm_active = False
                break

            led.value(1)
            if alarm_sound == 0:
                await play_alarm("sweep", 500, 3000, 1)
                await asyncio.sleep(0.05)
                led.value(0)
                await play_alarm("sweep", 500, 3000, 1)
                await asyncio.sleep(0.05)
            elif alarm_sound == 1:
                await play_alarm("sweep_up", 500, 4000, 1)
                await asyncio.sleep(0.05)
                led.value(0)
                await play_alarm("sweep_up", 500, 4000, 1)
                await asyncio.sleep(0.05)
            elif alarm_sound == 2:
                await play_alarm("sweep_down", 500, 4000, 1)
                await asyncio.sleep(0.05)
                led.value(0)
                await play_alarm("sweep_down", 500, 4000, 1)
                await asyncio.sleep(0.05)
            elif alarm_sound == 3:
                await play_alarm("high_low")
                await asyncio.sleep(0.05)
                led.value(0)
                await play_alarm("high_low")
                await asyncio.sleep(0.05)
            else:
                await play_alarm("sweep", 500, 3000, 1)
                await asyncio.sleep(0.05)
                led.value(0)
                await play_alarm("sweep", 500, 3000, 1)
                await asyncio.sleep(0.05)

        alarm_active = False
    except Exception as e:
        print(f"Error in alarm: {e}") 
    finally:
        alarm_active = False
        led.value(0)

# Arming handler
async def handle_arming():
    """Handle the arming and disarming of the system."""
    global is_armed, alarm_active, security_code, entering_security_code

    try:
        security_code = config.get_entry("security", "security_code")

        if not security_code:
            security_code = "0000"
            config.set_entry("security", "security_code", security_code)
            await config.write_async()

        while True:
            if arm_button.value() == 1:  # Button pressed
                if is_armed:
                    if alarm_active:
                        print("Stopping alarm...")
                        alarm_active = False
                        buzzer.duty_u16(0)  # Stop the buzzer immediately
                    security_code = config.get_entry("security", "security_code")
                    if not security_code:
                        security_code = "0000"
                        config.set_entry("security", "security_code", security_code)
                        await config.write_async()
                    if security_code:
                        entering_security_code = True
                        await play_dynamic_bell(150, buzzer_volume, 0.05, 1)
                        print("Waiting for security code")
                        result = await enter_security_code(security_code, security_code_max_entry_attempts, security_code_min_length, security_code_max_length)
                        entering_security_code = False
                        if result is None:  # User cancelled
                            continue
                        elif not result:  # Max attempts reached or incorrect
                            continue
                    await play_dynamic_bell(300, buzzer_volume, 0.05, 1)
                    print("Disarming")
                    is_armed = False
                    await play_dynamic_bell(250, buzzer_volume)
                    await system_ready_indicator()
                else:
                    security_code = config.get_entry("security", "security_code")
                    if not security_code:
                        security_code = "0000"
                        config.set_entry("security", "security_code", security_code)
                        await config.write_async()
                    if security_code:
                        entering_security_code = True
                        await play_dynamic_bell(150, buzzer_volume, 0.05, 1)
                        print("Waiting for security code")
                        result = await enter_security_code(security_code, security_code_max_entry_attempts, security_code_min_length, security_code_max_length)
                        entering_security_code = False
                        if result is None:  # User cancelled
                            continue
                        elif not result:  # Max attempts reached or incorrect
                            continue
                    await play_dynamic_bell(300, buzzer_volume, 0.05, 1)
                    print("Arming")
                    await play_dynamic_bell(250, buzzer_volume)
                    await system_ready_indicator()
                    is_armed = True
            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in handle_arming: {e}")

# Alarm test handler
async def handle_alarm_testing():
    """Test the alarm buzzer."""
    global alarm_active

    try:
        while True:
            if alarm_test_button.value() == 1:  # Button pressed
                if alarm_active:
                    continue
                print("Testing alarm...")
                await alarm("Testing Alarm.")
            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in handle_alarm_testing: {e}")

# Alarm sound switching handler
async def handle_alarm_sound_switching():
    """Handle switching the alarm sound for the system."""
    global alarm_sound, alarm_config_file

    try:
        # Load the saved alarm sound value or default
        alarm_sound = config.get_entry("alarm", "alarm_sound")

        while True:
            if alarm_sound_button.value() == 1:  # Button pressed
                print("Switching alarm sound")
                if alarm_sound == 0:
                    alarm_sound = 1
                    await play_alarm("sweep_up", 300, 4000, 1)
                elif alarm_sound == 1:
                    alarm_sound = 2
                    await play_alarm("sweep_down", 300, 4000, 1)
                elif alarm_sound == 2:
                    alarm_sound = 3
                    await play_alarm("high_low", 300, 4000, 1)
                elif alarm_sound == 3:
                    alarm_sound = 0
                    await play_alarm("sweep", 500, 3000, 1)

                # Save the updated alarm sound
                config.set_entry("alarm", "alarm_sound", alarm_sound)
                await config.write_async()

            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in handle_alarm_sound_switching: {e}")

# Buzzer volume handler
async def handle_buzzer_volume():
    """Handle buzzer volume changes."""
    global buzzer_volume

    try:
        while True:
            if volume_down_button.value() == 1:  # Button pressed
                if alarm_active:
                    continue
                print("Turning down volume.")
                await decrease_buzzer_volume()

            if volume_up_button.value() == 1:  # Button pressed
                if alarm_active:
                    continue
                print("Turning up volume.")
                await increase_buzzer_volume()

            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in handle_buzzer_volume: {e}")

# Motion detection
async def detect_motion():
    """Detect motion using the PIR sensor."""
    global enable_detect_motion, is_armed, entering_security_code, pir_timeout

    try:
        print("Detecting movement...")

        while True:
            enable_detect_motion = config.get_entry("security", "detect_motion")
            sensor_cooldown = config.get_entry("security", "sensor_cooldown")

            if not enable_detect_motion:
                await asyncio.sleep(0.5)
                continue

            if pir_timeout:
                if utime.time() < pir_timeout:
                    await asyncio.sleep(0.5)
                    continue

            if is_armed and pir.value() == 1:
                if entering_security_code:
                    await asyncio.sleep(0.05)
                    continue
                print("Movement Detected.")
                await alarm("Movement Detected.")
                pir_timeout = utime.time() + sensor_cooldown
                print("Detecting movement...")
            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in detect_motion: {e}")

# Tilt detection
async def detect_tilt():
    """Detect tilting using the tilt switch sensor."""
    global enable_detect_tilt, is_armed, entering_security_code, tilt_timeout

    try:
        print("Detecting tilt...")

        while True:
            enable_detect_tilt = config.get_entry("security", "detect_tilt")
            sensor_cooldown = config.get_entry("security", "sensor_cooldown")

            if not enable_detect_tilt:
                await asyncio.sleep(0.5)
                continue

            if tilt_timeout:
                if utime.time() < tilt_timeout:
                    await asyncio.sleep(0.5)
                    continue

            if is_armed and tilt.value() == 1:
                if entering_security_code:
                    await asyncio.sleep(0.05)
                    continue
                print("Tilt Detected.")
                await alarm("Tilt Detected")
                tilt_timeout = utime.time() + sensor_cooldown
                print("Detecting tilt...")
            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in detect_tilt: {e}")

# Arming indicator handler
async def handle_arming_indicator():
    """Handle blinking the LED to show when the system is armed."""
    global is_armed, alarm_active, entering_security_code

    try:
        while True:
            if is_armed and not alarm_active:
                if entering_security_code:
                    led.value(0)
                    await asyncio.sleep(1)
                    continue
                led.value(1)
                await asyncio.sleep(0.1)
                led.value(0)
            await asyncio.sleep(1)  # Polling interval
    except Exception as e:
        print(f"Error in handle_arming_indicator: {e}")
    finally:
        led.value(0)

# Keypad key detection
async def detect_keypad_keys():
    """Detect matrix keypad key commands."""
    global is_armed, silent_alarm, keypad_locked, entering_security_code

    try:
        print("Detecting keypad keys...")

        while True:
            if entering_security_code:
                await asyncio.sleep(0.05)
                continue

            key = read_keypad_key()
            if key and not entering_security_code:
                if keypad_locked and key != "A":
                    await asyncio.sleep(0.05)
                    continue
                if key == "A":
                    print("Initiating keypad_lock.")
                    await keypad_lock()
                elif key == "B":
                    print("Initiating alarm_mode_switch.")
                    await alarm_mode_switch()
                elif key == "C":
                    print("Initiating change_security_code.")
                    await change_security_code()
                elif key == "D":
                    print("Initiating reset_firmware_config.")
                    await reset_firmware_config()
                else:
                    print(f"Unhandled key press detected: {key}")

            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in detect_keypad_keys: {e}")

# Method to increase buzzer volume by 10%
async def increase_buzzer_volume():
    """Increase the buzzer volume by 10%, up to a maximum of 6144."""
    global buzzer_volume
    step = int(6144 * 0.1)  # Calculate 10% step
    buzzer_volume = min(buzzer_volume + step, 6144)
    config.set_entry("buzzer", "buzzer_volume", buzzer_volume)
    await config.write_async()
    print(f"Buzzer volume increased to: {buzzer_volume}")
    await buzzer_volume_indicator()

# Method to decrease buzzer volume by 10%
async def decrease_buzzer_volume():
    """Decrease the buzzer volume by 10%, down to a minimum of 0."""
    global buzzer_volume
    step = int(6144 * 0.1)  # Calculate 10% step
    buzzer_volume = max(buzzer_volume - step, 0)
    config.set_entry("buzzer", "buzzer_volume", buzzer_volume)
    await config.write_async()
    print(f"Buzzer volume decreased to: {buzzer_volume}")
    await buzzer_volume_indicator()

# Read a single key from the keypad
def read_keypad_key():
    """Read a key press from the matrix keypad."""
    global entering_security_code

    try:
        for i, row in enumerate(keypad_rows):
            row.high()
            for j, col in enumerate(keypad_cols):
                if col.value() == 1:
                    row.low()
                    if entering_security_code:
                        keypad_entry_indicator()
                    time.sleep_ms(100)
                    return keypad_characters[i][j]
            row.low()
        return None
    except Exception as e:
        print(f"Error in read_keypad_key: {e}")
    finally:
        for i, row in enumerate(keypad_rows):
            row.low()

# Validate Pushover API key
async def validate_pushover_api_key(timeout=5):
    """Validate the configured Pushover API key."""
    global pushover_api_key

    if not utils.isPicoW():
        print("Unsupported device.")
        return False

    if not utils.isNetworkConnected():
        print("No internet connection available.")
        return False

    key_is_valid = False

    url = "https://api.pushover.net/1/users/validate.json"

    pushover_api_key = config.get_entry("pushover", "api_key")

    if not pushover_api_key:
        return key_is_valid

    data_dict = {
        "token": pushover_app_token,
        "user": pushover_api_key,
    }
    data = utils.urlencode(data_dict).encode("utf-8")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    for attempt in range(3):  # Retry up to 3 times
        try:
            print(f"Attempt {attempt + 1}: Validating API key...")
            response = urequests.post(url, data=data, headers=headers, timeout=timeout)

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
async def send_pushover_notification(title="Goat - SecureMe", message="Testing", priority=0, timeout=5):
    """Send push notifications using Pushover."""
    global pushover_api_key

    if not utils.isPicoW():
        print("Unsupported device.")
        return

    if not utils.isNetworkConnected():
        print("No internet connection available.")
        return

    url = "https://api.pushover.net/1/messages.json"

    pushover_api_key = config.get_entry("pushover", "api_key")

    if not pushover_api_key:
        print("A Pushover API key is required to send push notifications.")
        return

    data_dict = {
        "token": pushover_app_token,
        "user": pushover_api_key,
        "message": message,
        "priority": priority,
        "title": title
    }
    data = utils.urlencode(data_dict).encode("utf-8")
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

# System startup indicator
async def system_startup_indicator():
    """Play the system startup indicator."""
    try:
        led.value(1)
        buzzer.duty_u16(buzzer_volume)
        buzzer.freq(500)
        await asyncio.sleep(0.1)
        buzzer.freq(1000)
        await asyncio.sleep(0.1)
        buzzer.freq(1500)
        await asyncio.sleep(0.1)
        buzzer.freq(2000)
        await asyncio.sleep(0.1)
        led.value(0)
        buzzer.duty_u16(0)
    except Exception as e:
        print(f"Error in system_startup_indicator: {e}")
    finally:
        buzzer.duty_u16(0)  # Turn off the buzzer
        led.value(0)

# System ready indicator
async def system_ready_indicator():
    """Play the system ready indicator."""
    try:
        buzzer.duty_u16(buzzer_volume)
        buzzer.freq(1000)
        led.value(1)
        await asyncio.sleep(0.1)
        buzzer.freq(1500)
        await asyncio.sleep(0.1)
        buzzer.duty_u16(0)
        led.value(0)
    except Exception as e:
        print(f"Error in system_ready_indicator: {e}")
    finally:
        buzzer.duty_u16(0)  # Turn off the buzzer
        led.value(0)

# Buzzer volume indicator
async def buzzer_volume_indicator():
    """Play the buzzer volume indicator."""
    try:
        led.value(1)
        buzzer.duty_u16(buzzer_volume)
        buzzer.freq(1500)
        await asyncio.sleep(0.1)
        buzzer.duty_u16(0)
        led.value(0)
    except Exception as e:
        print(f"Error in buzzer_volume_indicator: {e}")
    finally:
        buzzer.duty_u16(0)  # Turn off the buzzer
        led.value(0)

# Keypad entry indicator
def keypad_entry_indicator():
    """Play the keypad entry indicator."""
    try:
        led.value(1)
        buzzer.duty_u16(buzzer_volume)
        buzzer.freq(200)
        time.sleep(0.05)
        buzzer.duty_u16(0)
        led.value(0)
    except Exception as e:
        print(f"Error in keypad_entry_indicator: {e}")
    finally:
        buzzer.duty_u16(0)  # Turn off the buzzer
        led.value(0)

# Keypad lock indicator
async def keypad_lock_indicator(locked = True):
    """Play the keypad lock indicator."""
    try:
        buzzer.duty_u16(buzzer_volume)

        led.value(1)

        if locked:
            buzzer.freq(600)
            await asyncio.sleep(0.05)
            buzzer.freq(400)
            await asyncio.sleep(0.05)
            buzzer.freq(200)
            await asyncio.sleep(0.05)
        else:
            buzzer.freq(200)
            await asyncio.sleep(0.05)
            buzzer.freq(400)
            await asyncio.sleep(0.05)
            buzzer.freq(600)
            await asyncio.sleep(0.05)

        buzzer.duty_u16(0)

        led.value(0)
    except Exception as e:
        print(f"Error in keypad_lock_indicator: {e}")
    finally:
        buzzer.duty_u16(0)  # Turn off the buzzer
        led.value(0)

# Alarm mode switch indicator
async def alarm_mode_switch_indicator(silent = True):
    """Play the alarm mode switch indicator."""
    try:
        buzzer.duty_u16(buzzer_volume)

        led.value(1)

        if silent:
            buzzer.freq(1200)
            await asyncio.sleep(0.05)
            buzzer.freq(1000)
            await asyncio.sleep(0.05)
            buzzer.freq(800)
            await asyncio.sleep(0.05)
        else:
            buzzer.freq(800)
            await asyncio.sleep(0.05)
            buzzer.freq(1000)
            await asyncio.sleep(0.05)
            buzzer.freq(1200)
            await asyncio.sleep(0.05)

        buzzer.duty_u16(0)

        led.value(0)
    except Exception as e:
        print(f"Error in alarm_mode_switch_indicator: {e}")
    finally:
        buzzer.duty_u16(0)  # Turn off the buzzer
        led.value(0)

# Matrix keypad lock
async def keypad_lock():
    """Handle locking and unlocking the matrix keypad."""
    global keypad_locked

    try:
        if keypad_locked:
            print("Keypad unlocked.")
            keypad_locked = False
            await keypad_lock_indicator(keypad_locked)
        else:
            print("Keypad locked.")
            keypad_locked = True
            await keypad_lock_indicator(keypad_locked)
    except Exception as e:
        print(f"Error in keypad_lock: {e}")

# Alarm mode switch
async def alarm_mode_switch():
    """Handle switching between alarm modes."""
    global silent_alarm, pushover_api_key

    if not utils.isPicoW():
        print("Unsupported device.")
        await play_dynamic_bell(100, buzzer_volume, 0.05, 1)
        return

    if not utils.isNetworkConnected():
        print("No internet connection available.")
        await play_dynamic_bell(100, buzzer_volume, 0.05, 1)
        return

    key_is_valid = None

    try:
        pushover_api_key = config.get_entry("pushover", "api_key")

        if not pushover_api_key:
            print("A Pushover API key is required for silent alarms.")
            await play_dynamic_bell(100, buzzer_volume, 0.05, 1)
            return

        if not silent_alarm:
            key_is_valid = await validate_pushover_api_key()
            if not key_is_valid:
                print("The configured Pushover API key is invalid.")
                await play_dynamic_bell(100, buzzer_volume, 0.05, 1)
                return

        if silent_alarm:
            print("Alarm mode set to audible.")
            silent_alarm = False
            await alarm_mode_switch_indicator(silent_alarm)
        else:
            print("Alarm mode set to silent.")
            silent_alarm = True
            await alarm_mode_switch_indicator(silent_alarm)
    except Exception as e:
        print(f"Error in alarm_mode_switch: {e}")

# Firmware reset
async def reset_firmware_config():
    """Resets the firmware configuration to factory defaults."""
    global alarm_active, security_code, entering_security_code

    try:
        security_code = config.get_entry("security", "security_code")

        if not security_code:
            security_code = "0000"
            config.set_entry("security", "security_code", security_code)
            await config.write_async()

        if alarm_active:
            print("Stopping alarm...")
            alarm_active = False
            buzzer.duty_u16(0)

        entering_security_code = True

        await play_dynamic_bell(50, buzzer_volume, 0.05, 3)

        print("Waiting for security code")

        result = await enter_security_code(security_code, security_code_max_entry_attempts, security_code_min_length, security_code_max_length)

        if result is None:  # User cancelled
            entering_security_code = False
            return
        elif not result:  # Max attempts reached or incorrect
            entering_security_code = False
            return

        await play_dynamic_bell(300, buzzer_volume, 0.05, 1)

        print("Waiting for second security code")

        final_result = await enter_security_code(security_code, security_code_max_entry_attempts, security_code_min_length, security_code_max_length)

        if final_result is None:  # User cancelled
            entering_security_code = False
            return
        elif not final_result:  # Max attempts reached or incorrect
            entering_security_code = False
            return

        await play_dynamic_bell(300, buzzer_volume, 0.05, 1)

        print("Resetting firmware configuration...")

        await play_dynamic_bell(50, buzzer_volume, 0.05, 5)

        if config_file in uos.listdir(config_directory):
            uos.remove(f"{config_directory}/{config_file}")
        if network_config_file in uos.listdir(config_directory):
            uos.remove(f"{config_directory}/{network_config_file}")

        uos.rmdir(config_directory)

        reset()

        entering_security_code = False
    except Exception as e:
        print(f"Error in reset_firmware_config: {e}")

# Security code entry
async def enter_security_code(security_code, max_attempts, min_length, max_length):
    """Handle security code entry with cancellation support."""
    attempts = 0
    while attempts < max_attempts:
        code = ""
        while len(code) < max_length:
            key = read_keypad_key()
            if key:
                if key == "#":  # Submit code
                    if len(code) < min_length:
                        print(f"Code too short: {code}")
                        return None  # Cancellation
                    print(f"Code entered: {code}")
                    break
                elif key == "*":  # Cancel or clear code
                    if len(code) == 0:
                        print("Code entry cancelled.")
                        return None  # Cancellation
                    print("Code cleared!")
                    code = ""  # Reset
                else:
                    code += key
                    print(f"Key pressed: {key}")
            await asyncio.sleep(0.1)  # Slight delay to avoid multiple detections

        if len(code) == 0:  # Code entry cancelled
            print("Code entry cancelled.")
            return None

        if len(code) < min_length:  # Code too short
            print(f"Code too short: {code}")
            return None

        if code != security_code:  # Incorrect code
            attempts += 1
            print(f"Invalid security code provided. Attempt {attempts}/{max_attempts}.")
            if attempts >= max_attempts:
                print("Maximum attempts reached. Triggering alarm.")
                await alarm("Invalid Security Code Provided.")  # Trigger the alarm after too many attempts
                return False  # Return False to indicate max attempts exceeded
            await alarm("Invalid Security Code Provided.")
            continue

        # Correct code
        print("Access granted.")
        return True  # Success
    return False  # Max attempts exceeded

# Change security code
async def change_security_code():
    global security_code, entering_security_code

    try:
        security_code = config.get_entry("security", "security_code")
        if not security_code:
            security_code = "0000"
            config.set_entry("security", "security_code", security_code)
            await config.write_async()
        if security_code:
            entering_security_code = True
            await play_dynamic_bell(150, buzzer_volume, 0.05, 1)
            await play_dynamic_bell(200, buzzer_volume, 0.05, 1)

            print("Waiting for current security code")
            result = await enter_security_code(security_code, security_code_max_entry_attempts, security_code_min_length, security_code_max_length)

            if result is None:  # User cancelled
                print("User cancelled the security code entry.")
                entering_security_code = False
                await play_dynamic_bell(100, buzzer_volume, 0.05, 1)
                return
            elif not result:  # Max attempts reached or incorrect
                print("Max attempts reached or incorrect code entered.")
                entering_security_code = False
                await play_dynamic_bell(100, buzzer_volume, 0.05, 1)
                return

            await play_dynamic_bell(150, buzzer_volume, 0.05, 1)

            # Helper function for entering and confirming the code
            async def enter_code(prompt):
                print(prompt)
                code = ""
                while len(code) < security_code_max_length:
                    key = read_keypad_key()
                    if key:
                        if key == "#":
                            if code < security_code_min_length:
                                print(f"Code too short: {code}")
                                return None
                            print(f"Code entered: {code}")
                            break
                        elif key == "*":
                            if len(code) == 0:
                                print("Code entry cancelled.")
                                return None
                            print("Code cleared!")
                            code = ""
                        else:
                            code += key
                            print(f"Key pressed: {key}")
                    await asyncio.sleep(0.1)  # Slight delay to avoid multiple detections
                return code

            # Enter new code
            new_code = await enter_code("Enter new security code:")
            if new_code is None:
                entering_security_code = False
                await play_dynamic_bell(100, buzzer_volume, 0.05, 1)
                return

            await play_dynamic_bell(150, buzzer_volume, 0.05, 1)

            # Confirm new code
            new_code_confirmation = await enter_code("Confirm new security code:")
            if new_code_confirmation is None:
                entering_security_code = False
                await play_dynamic_bell(100, buzzer_volume, 0.05, 1)
                return

            if new_code != new_code_confirmation:
                print("Confirmation code does not match.")
                entering_security_code = False
                await play_dynamic_bell(100, buzzer_volume, 0.05, 1)
                return

            # Update the security code
            security_code = new_code
            config.set_entry("security", "security_code", security_code)
            await config.write_async()
            await play_dynamic_bell(150, buzzer_volume, 0.05, 1)
            await play_dynamic_bell(200, buzzer_volume, 0.05, 1)
            print(f"Security code updated. New code: {security_code}")

        entering_security_code = False
    except Exception as e:
        print(f"Error in change_security_code: {e}")
    finally:
        entering_security_code = False

# Configuration checker
async def check_config():
    try:
        # Check if the configuration directory exists
        uos.listdir(config_directory)
        print("Configuration directory exists.")
    except OSError as e:
        print(f"Configuration directory does not exist. Error: {e}")
        try:
            print("Attempting to create configuration directory...")
            uos.mkdir(config_directory)
            print("Configuration directory created successfully.")
        except OSError as e:
            print(f"Failed to create configuration directory. Error: {e}")
            print("Rebooting...")
            reset()

# System start-up
async def system_startup():
    """System firmware initialization."""

    print("Initializing firmware...")

    try:
        await system_startup_indicator()

        if utils.isPicoW():
            await utils.configure_network()

        await utils.initialize_pins(skip_pins=[BUZZER_PIN, PIR_PIN, TILT_SWITCH_PIN, ARM_BUTTON_PIN, ALARM_TEST_BUTTON_PIN, ALARM_SOUND_BUTTON_PIN, keypad_row_pins[0], keypad_row_pins[1], keypad_row_pins[2], keypad_row_pins[3], keypad_col_pins[0], keypad_col_pins[1], keypad_col_pins[2], keypad_col_pins[3], VOLUME_DOWN_BUTTON_PIN, VOLUME_UP_BUTTON_PIN])

        await warmup_pir_sensor()

        await system_ready_indicator()

        print("System ready.")
    except Exception as e:
        print(f"Error in system_startup: {e}")

# PIR sensor warmup
async def warmup_pir_sensor():
    """Waits for 60 seconds to let the PIR sensor warm up."""
    print("Warming up PIR sensor...")

    try:
        for i in range(pir_warmup_time, 0, -1):
            print(f"warming up... {i}s remaining.")
            await play_dynamic_bell(250, buzzer_volume, 0.1, 1)

        print("PIR sensor ready!")
    except Exception as e:
        print(f"Error in warmup_pir_sensor: {e}")

async def system_shutdown():
    """System firmware shutdown."""
    global tasks

    print("Shutting down...")

    for task in tasks:
        task.cancel()
    await asyncio.sleep(0)  # Allow tasks to finish cleanup

# Firmware entry point
async def main():
    """Main coroutine to handle firmware services"""
    global config, tasks, enable_detect_motion, enable_detect_tilt, sensor_cooldown, buzzer_volume

    # Instantiate network specific features
    if utils.isPicoW():
        web_server = SecureMeServer()
        network_manager = NetworkManager(ap_ssid="Goat - SecureMe", ap_password="secureme", sta_web_server=web_server)

        await check_config()

        print("Loading firmware configuration...")

        config = ConfigManager(config_directory, config_file)
        await config.read_async()

        enable_detect_motion = config.get_entry("security", "detect_motion")

        if not isinstance(enable_detect_motion, bool):
            enable_detect_motion = True
            config.set_entry("security", "detect_motion", enable_detect_motion)
            await config.write_async()

        enable_detect_tilt = config.get_entry("security", "detect_tilt")

        if not isinstance(enable_detect_motion, bool):
            enable_detect_tilt = True
            config.set_entry("security", "detect_tilt", enable_detect_tilt)
            await config.write_async()

        sensor_cooldown = config.get_entry("security", "sensor_cooldown")

        if not isinstance(sensor_cooldown, int):
            sensor_cooldown = default_sensor_cooldown
            config.set_entry("security", "sensor_cooldown", sensor_cooldown)
            await config.write_async()

    buzzer_volume = config.get_entry("buzzer", "buzzer_volume")

    if not isinstance(buzzer_volume, int):
        buzzer_volume = default_buzzer_volume
        config.set_entry("buzzer", "buzzer_volume", buzzer_volume)
        await config.write_async()

    await system_startup()

    # Create task list
    tasks = [
        asyncio.create_task(config.start_watching()),
        asyncio.create_task(handle_arming()),
        asyncio.create_task(handle_arming_indicator()),
        asyncio.create_task(handle_alarm_testing()),
        asyncio.create_task(handle_alarm_sound_switching()),
        asyncio.create_task(handle_buzzer_volume()),
        asyncio.create_task(detect_motion()),
        asyncio.create_task(detect_tilt()),
        asyncio.create_task(detect_keypad_keys())
    ]

    if utils.isPicoW():
        tasks.append(asyncio.create_task(network_manager.run()))

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

# Startup and run
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Shutting down firmware...")
finally:
    buzzer.duty_u16(0)
    led.value(0)
    asyncio.run(system_shutdown())
    print("Firmware shutdown complete.")
