# Goat - SecureMe Version History

This document outlines the changes made between versions of the **Goat - SecureMe** firmware.

## V1.1.0

### New Features

#### Detection

Implemented support for sound detection using a high intensity microphone sensor.

#### Pushover Notifications

You must now register your own Pushover application and specify your application token in the SecureMe web interface to receive push notifications.

### Bug Fixes

#### Initialization

Tilt sensor configuration was incorrectly validated against the motion detection setting.

#### Web Interface

   - Missing configuration values could not be written on initialization.

### Changes

#### Web Interface

   - The **SecureMeServer** class has been renamed to **WebServer**.

## V1.0.1

### New Features

#### Security

   - Security code errors now have an indicator.

### Bug Fixes

#### Web Interface

   - The **Arming Cooldown** setting would incorrectly take the value of the **Sensor Cooldown** setting.

## V1.0.0

Initial release.
