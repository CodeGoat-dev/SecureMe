# Goat - SecureMe utility methods
# Utility methods for the Goat - SecureMe - Portable Security System
# Used throughout the SecureMe firmware to provide various utilities.

# Imports
from machine import Pin, PWM
import sys
import uasyncio as asyncio

# Constants
NUM_PINS = 30

def isRP2040():
    """Checks if running on an RP2040 based microcontroller."""
    return "RP2040" in sys.implementation[2]

# Check if running on a PicoW microcontroller
def isPicoW():
    """Checks if the current microcontroller is wi-fi enabled."""
    try:
        # Try to import the network module, which is only available on Pico W
        import network
        return True  # Pico W has Wi-Fi, so return True
    except ImportError:
        # If the network module is unavailable, it's a regular Pico
        return False

# Check if the network is connected
def isNetworkConnected():
    """Checks if the station interface is currently connected."""
    try:
        import network
        sta = network.WLAN(network.STA_IF)
        if sta.isconnected():
            return True  # Network is connected
        else:
            return False  # Network is not connected
    except ImportError:
        # If the network module is unavailable, the network is not connected.
        return False

# Unused pin initialization function
async def initialize_pins(skip_pins=None):
    """
    Initializes pins as outputs and sets them low, excluding specified pins.

    Args:
        skip_pins: List of pin numbers to skip during initialization (default: None).
    """
    print("Configuring unused GPIO pins...")

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

# Pin de-initialization function
async def deinitialize_pins(skip_pins=None):
    """
    Deinitializes pins, excluding specified pins.

    Args:
        skip_pins: List of pin numbers to skip during de-initialization (default: None).
    """
    print("De-initializing GPIO pins...")

    if skip_pins is None:
        skip_pins = []

    for pin_number in range(NUM_PINS):
        if pin_number in skip_pins:
            continue  # Skip pins in the exclusion list
        try:
            pin = Pin(pin_number)
            pin.init(Pin.OUT)  # Re-initialize the pin as an output
            pin.value(0)  # Drive the pin low
        except ValueError:
            # Ignore invalid pin numbers or configuration errors
            pass

# Pin type checker
def pin_is_input(pin):
    """
    Checks if a GPIO pin is configured as an input.

    Args:
    - pin: The GPIO pin object to check.
    """
    try:
        pin.value(1)  # Try to set the pin high
        pin.value(0)  # Reset it
        return False
    except:
        return True

# Configure network interfaces on PicoW
async def configure_network():
    """Configures all network interfaces with a default disabled state."""
    print("Initializing network interfaces...")

    import network

    ap = network.WLAN(network.AP_IF)
    sta = network.WLAN(network.STA_IF)

    try:
        ap.deinit()
        ap.config(essid="", password="")
        ap.active(False)
        sta.deinit()
        sta.active(False)
    except Exception as e:
        print(f"Error in configure_network: {e}")

# Minimal URL encoding function for MicroPython
def urlencode(data):
    """Encode a dictionary into a URL-encoded string."""
    return "&".join(f"{key}={value}" for key, value in data.items())

def urldecode(value):
    """Decodes percent-encoded characters in a URL-encoded string."""
    result = []
    i = 0
    while i < len(value):
        if value[i] == "%" and i + 2 < len(value):
            hex_value = value[i+1:i+3]
            try:
                result.append(chr(int(hex_value, 16)))  # Convert hex to char
                i += 3
            except ValueError:
                result.append(value[i])  # If invalid, keep character as is
                i += 1
        else:
            result.append(value[i])
            i += 1
    return "".join(result)
