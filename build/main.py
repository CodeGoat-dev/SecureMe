# Firmware entry point

# Imports
import machine

# Try to import and run the SecureMe firmware
try:
    import SecureMe
except Exception as e:
    print(f"Unable to start: {e}")
    machine.reset()
