# Goat - SecureMe Version History

This document outlines the changes made between versions of the **Goat - SecureMe** firmware.

## V1.1.4

### Bug Fixes

#### Detection

Fixed missing global references which could cause issues with detection.

#### Automatic Update

Fixed an issue where the wrong repository URL was used.

## V1.1.3

### Changes

#### Automatic Updater

The automatic updater now checks the network connection before attempting to update.

Added a network request timeout to ensure the system doesn't hang when unable to download files.

The correct content URL is now used when fetching files.

Update files are now stored in a temporary location and moved after successful download to prevent firmware corruption.

Improved verbosity for debugging.

## V1.1.2

### Changes

#### Web Interface

Added a GitHub repository link to the web interface.

## V1.1.1

### Changes

#### Automatic Updater

The automatic updater now downloads files directly as a pose to downloading and extracting a tarball.

## V1.1.0

### New Features

#### Detection

Implemented support for sound detection using a high intensity microphone sensor.

#### Pushover Notifications

You must now register your own Pushover application and specify your application token in the SecureMe web interface to receive push notifications.

#### Automatic Update

SecureMe is now automatically updated when new releases become available.

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
