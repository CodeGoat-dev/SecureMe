# Goat SecureMe
# Firmware bootstrap utility
# © (c) 2024-2025 Goat Technologies
# https://github.com/CodeGoat-dev/SecureMe
# Description:
# Launches the Goat - SecureMe byte-compiled firmware.
# Byte-compiled code cannot be automatically started so must be bootstrapped using a non-compiled main script.

# Imports
import machine

# Try to import the compiled SecureMe firmware
try:
    import SecureMe
except Exception as e:
    print(f"Unable to start: {e}")
    machine.reset()
