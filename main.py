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
from machine import Pin, PWM, ADC
import time
import uasyncio as asyncio
import uos

# Pin constants
LED_PIN = 25
BUZZER_PIN = 1
PIR_PIN = 2
TILT_SWITCH_PIN = 3
ARM_BUTTON_PIN = 4
ALARM_TEST_BUTTON_PIN = 5
ALARM_SOUND_BUTTON_PIN = 6
POTENTIOMETER_PIN = 27

# Define the GPIO pins for keypad rows and columns
keypad_row_pins = [7, 8, 9, 10]
keypad_col_pins = [11, 12, 13, 14]

# Initialize all pins
NUM_PINS = 30

# Configure required pins
led = Pin(LED_PIN, Pin.OUT)
buzzer = PWM(Pin(BUZZER_PIN))
potentiometer = ADC(Pin(POTENTIOMETER_PIN))
arm_button = Pin(ARM_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
alarm_test_button = Pin(ALARM_TEST_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
alarm_sound_button = Pin(ALARM_SOUND_BUTTON_PIN, Pin.IN, Pin.PULL_DOWN)
pir = Pin(PIR_PIN, Pin.IN, Pin.PULL_DOWN)
tilt = Pin(TILT_SWITCH_PIN, Pin.IN, Pin.PULL_UP)

# Initialize keypad row pins as outputs
keypad_rows = [Pin(pin, Pin.OUT) for pin in keypad_row_pins]
# Initialize keypad column pins as inputs
keypad_cols = [Pin(pin, Pin.IN, Pin.PULL_DOWN) for pin in keypad_col_pins]

# Global variables
config_file = "alarm_config.txt"
security_code_config_file = "security_config.txt"
is_armed = True
alarm_active = False
alarm_sound = 0
buzzer_volume = 0
security_code = "0000"
entering_security_code = False
security_code_max_entry_attempts = 3
security_code_min_length = 4
security_code_max_length = 8
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
    - initial_volume: Initial volume (range 0-1023 for duty cycle)
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
    global buzzer_volume, alarm_active

    try:
        buzzer_volume = get_buzzer_volume()

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
async def alarm():
    """Run the alarm when a sensor detects motion."""
    global buzzer_volume, alarm_active, alarm_sound, entering_security_code

    if alarm_active:
        return

    if entering_security_code:
        return

    alarm_active = True

    try:
        alarm_sound = await load_alarm_sound_from_file()

        if not alarm_sound == 0 and not alarm_sound == 1 and not alarm_sound == 2 and not alarm_sound == 3:
            alarm_sound = 0

        buzzer_volume = get_buzzer_volume()

        if buzzer_volume is None or buzzer_volume == 0:
            raise ValueError("Invalid buzzer volume.")

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
    global is_armed, buzzer_volume, alarm_active, security_code, entering_security_code

    try:
        buzzer_volume = get_buzzer_volume()
        security_code = await load_security_code_from_file()

        while True:
            if arm_button.value() == 1:  # Button pressed
                if is_armed:
                    if alarm_active:
                        print("Stopping alarm...")
                        alarm_active = False
                        buzzer.duty_u16(0)  # Stop the buzzer immediately
                    security_code = await load_security_code_from_file()
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
                    buzzer_volume = get_buzzer_volume()
                    is_armed = False
                    await play_dynamic_bell(250, buzzer_volume)
                    await system_ready_indicator()
                else:
                    security_code = await load_security_code_from_file()
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
                    buzzer_volume = get_buzzer_volume()
                    await play_dynamic_bell(250, buzzer_volume)
                    await system_ready_indicator()
                    is_armed = True
            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in handle_arming: {e}")

# Alarm test handler
async def handle_alarm_testing():
    """Test the alarm buzzer."""
    global buzzer_volume, alarm_active

    try:
        buzzer_volume = get_buzzer_volume()

        while True:
            if alarm_test_button.value() == 1:  # Button pressed
                if alarm_active:
                    continue
                print("Testing alarm...")
                await alarm()
            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in handle_alarm_testing: {e}")

# Alarm sound switching handler
async def handle_alarm_sound_switching():
    """Handle switching the alarm sound for the system."""
    global buzzer_volume, alarm_sound, config_file

    try:
        # Load the saved alarm sound value or default
        alarm_sound = await load_alarm_sound_from_file()

        buzzer_volume = get_buzzer_volume()

        while True:
            if alarm_sound_button.value() == 1:  # Button pressed
                print("Switching alarm sound")
                buzzer_volume = get_buzzer_volume()
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

                # Save the updated alarm sound to the file
                await save_alarm_sound_to_file()

            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in handle_alarm_sound_switching: {e}")

# Motion detection
async def detect_motion():
    """Detect motion using the PIR sensor."""
    global is_armed, entering_security_code

    try:
        print("Detecting movement...")

        while True:
            if is_armed and pir.value() == 1:
                if entering_security_code:
                    await asyncio.sleep(0.05)
                    continue
                print("Movement detected.")
                await alarm()
                print("Detecting movement...")
            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in detect_motion: {e}")

# Tilt detection
async def detect_tilt():
    """Detect tilting using the tilt switch sensor."""
    global is_armed, entering_security_code

    try:
        print("Detecting tilt...")

        while True:
            if is_armed and tilt.value() == 1:
                if entering_security_code:
                    await asyncio.sleep(0.05)
                    continue
                print("Tilt detected.")
                await alarm()
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
    global is_armed, keypad_locked, entering_security_code

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
                elif key == "D":
                    print("Initiating change_security_code.")
                    await change_security_code()
                else:
                    print(f"Unhandled key press detected: {key}")

            await asyncio.sleep(0.05)  # Polling interval
    except Exception as e:
        print(f"Error in detect_keypad_keys: {e}")

# Unused pin initialization function
async def initialize_pins(skip_pins=None):
    """
    Initializes pins as outputs and sets them low, excluding specified pins.

    Args:
        skip_pins: List of pin numbers to skip during initialization (default: None).
    """
    if skip_pins is None:
        skip_pins = []

    for pin_number in range(NUM_PINS):
        if pin_number in skip_pins:
            continue  # Skip pins in the exclusion list
        try:
            # Initialize the pin as output and set it low
            pin = Pin(pin_number, Pin.OUT)
            pin.value(0)  # Drive the pin low
        except ValueError:
            # Ignore invalid pin numbers or configuration errors
            pass

# Alarm sound loading function
async def load_alarm_sound_from_file():
    """Load the alarm sound value from a file."""
    try:
        if config_file in uos.listdir("/"):
            with open(config_file, "r") as f:
                return int(f.read().strip())
        else:
            return 0
    except Exception as e:
        print(f"Error reading config file: {e}")
        return 0

# Alarm sound saving function
async def save_alarm_sound_to_file():
    """Save the current alarm sound to a file."""
    try:
        with open(config_file, "w") as f:
            f.write(str(alarm_sound))
    except Exception as e:
        print(f"Error writing to config file: {e}")

# Security code loading function
async def load_security_code_from_file():
    """Load the security code value from a file."""
    try:
        if security_code_config_file in uos.listdir("/"):
            with open(security_code_config_file, "r") as f:
                return str(f.read().strip())
        else:
            return str("0000")
    except Exception as e:
        print(f"Error reading config file: {e}")
        return str("0000")

# Security code saving function
async def save_security_code_to_file():
    """Save the current security code to a file."""
    try:
        with open(security_code_config_file, "w") as f:
            f.write(str(security_code))
    except Exception as e:
        print(f"Error writing to config file: {e}")

# Buzzer volume retrieval
def get_buzzer_volume():
    """Read the current potentiometer value to use as the buzzer volume."""
    return potentiometer.read_u16()

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

# System startup indicator
async def system_startup_indicator():
    """Play the system startup indicator."""
    global buzzer_volume

    try:
        buzzer_volume = get_buzzer_volume()
        led.value(1)
        buzzer.duty_u16(buzzer_volume)
        buzzer.freq(500)
        time.sleep(0.1)
        buzzer.freq(1000)
        time.sleep(0.1)
        buzzer.freq(1500)
        time.sleep(0.1)
        buzzer.freq(2000)
        time.sleep(0.1)
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
    global buzzer_volume

    try:
        buzzer_volume = get_buzzer_volume()

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

# Keypad entry indicator
def keypad_entry_indicator():
    """Play the keypad entry indicator."""
    global buzzer_volume

    try:
        buzzer_volume = get_buzzer_volume()

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
def keypad_lock_indicator(locked = True):
    """Play the keypad lock indicator."""
    global buzzer_volume

    try:
        buzzer_volume = get_buzzer_volume()

        buzzer.duty_u16(buzzer_volume)

        led.value(1)

        if locked:
            buzzer.freq(400)
            time.sleep(0.05)
            buzzer.freq(200)
            time.sleep(0.05)
        else:
            buzzer.freq(200)
            time.sleep(0.05)
            buzzer.freq(400)
            time.sleep(0.05)

        buzzer.duty_u16(0)

        led.value(0)
    except Exception as e:
        print(f"Error in keypad_entry_indicator: {e}")
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
            keypad_lock_indicator(keypad_locked)
        else:
            print("Keypad locked.")
            keypad_locked = True
            keypad_lock_indicator(keypad_locked)
    except Exception as e:
        print(f"Error in keypad_lock: {e}")

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
                await alarm()  # Trigger the alarm after too many attempts
                return False  # Return False to indicate max attempts exceeded
            await alarm()
            continue

        # Correct code
        print("Access granted.")
        return True  # Success
    return False  # Max attempts exceeded

# Change security code
async def change_security_code():
    global security_code, entering_security_code

    try:
        security_code = await load_security_code_from_file()
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
            await save_security_code_to_file()
            await play_dynamic_bell(150, buzzer_volume, 0.05, 1)
            await play_dynamic_bell(200, buzzer_volume, 0.05, 1)
            print(f"Security code updated. New code: {security_code}")

        entering_security_code = False
    except Exception as e:
        print(f"Error in change_security_code: {e}")
    finally:
        entering_security_code = False

# System start-up
async def system_startup():
    """System firmware initialization."""
    global buzzer_volume

    print("Starting...")

    try:
        await initialize_pins(skip_pins=[LED_PIN, BUZZER_PIN, PIR_PIN, TILT_SWITCH_PIN, POTENTIOMETER_PIN, ARM_BUTTON_PIN, ALARM_TEST_BUTTON_PIN, ALARM_SOUND_BUTTON_PIN, keypad_row_pins[0], keypad_row_pins[1], keypad_row_pins[2], keypad_row_pins[3], keypad_col_pins[0], keypad_col_pins[1], keypad_col_pins[2], keypad_col_pins[3]])

        await system_startup_indicator()

        print("Warming up PIR...")

        buzzer_volume = get_buzzer_volume()

        for i in range(10, 0, -1):
            print(f"warming up... {i}s remaining.")
            await play_dynamic_bell(250, buzzer_volume, 0.1, 1)
        print("PIR sensor ready!")
        await system_ready_indicator()
    except Exception as e:
        print(f"Error in system_startup: {e}")

async def system_shutdown():
    """System firmware shutdown."""
    print("Shutting down...")
    for task in asyncio.all_tasks():
        task.cancel()
    await asyncio.sleep(0)  # Allow tasks to finish cleanup

# Firmware entry point
async def main():
    """Main coroutine to handle firmware services"""
    global buzzer_volume

    buzzer_volume = get_buzzer_volume()

    await system_startup()

    # Run all tasks concurrently
    await asyncio.gather(
        handle_arming(),
        handle_alarm_testing(),
        handle_alarm_sound_switching(),
        detect_motion(),
        detect_tilt(),
        handle_arming_indicator(),
        detect_keypad_keys()
    )

# Startup and run
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program stopped.")
finally:
    buzzer.duty_u16(0)
    led.value(0)
    system_shutdown()
    print("Cleaned up resources.")
