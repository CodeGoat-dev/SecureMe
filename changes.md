# Goat - SecureMe Version History

This document outlines the changes made between versions of the **Goat - SecureMe** firmware.

## V1.3.6

### Changes

#### Pico Network Manager

Updated Pico Network Manager to v1.1.2.

## V1.3.5

### Changes

### Web Interface

Improved decoding of form data in the web interface to improve compatibility with non-alphanumeric entries.

## V1.3.4

### Changes

#### Pico Network Manager

Updated Pico Network Manager to v1.1.1.

## V1.3.3

### Bug Fixes

#### Automatic Update

Fixes an issue where the latest update would be continuously offered.

## V1.3.2

### Changes

#### Web Interface

Adds the current system date and time to all web interface pages.

## V1.3.1

### Bug Fixes

#### Initialization

Fixes an issue with Pico Network Manager class instantiation.

## V1.3.0

### Bug Fixes

#### Initialisation

Fixed an issue with configuration reflection where some settings would not be correctly reflected.

### Changes

#### Time Synchronisation

Time synchronisation can now be configured. You can enable/disable time synchronisation and specify the time synchronisation server to use.

#### Web Interface

Added a **Time Synchronisation Settings** page to the web interface.

#### Pico Network Manager

Updated Pico Network Manager to v1.1.0.

## V1.2.6

### Bug Fixes

#### Web Interface

Fixed formatting issues on the **Detection Settings** page.

Fixed unexpected authorization error notifications when authenticating.

## V1.2.5

### Changes

#### Automatic Update

Automatic update can now be enabled/disabled. The update interval is also customisable.

#### Web Interface

Added an **Automatic Update Settings** page to the web interface.

## V1.2.4

### Changes

#### Automatic Update

Implemented configuration watching to enable the automatic updater to keep track of configuration changes.

Added a delay before rebooting after an update to give any notifications a chance to be sent.

## V1.2.3

### Bug Fixes

#### Automatic Update

Fixes an incorrect configuration reference for update notifications.

## V1.2.2

### Bug Fixes

#### Web Interface

Fixes an invalid reference to the HTTP401 Unauthorized page which caused the web interface to be inaccessible.

## V1.2.1

### Changes

#### System Notifications

SecureMe can now send system status notifications for firmware updates.

#### Web Interface

Added an option to enable/disable firmware update notifications.

## V1.2.0

### New Features

#### Time Synchronisation

The system date and time is now automatically synchronised via an internally hosted API when connected to the internet.

#### System Notifications

SecureMe can now send system notifications via **Pushover** for various system events including initialization, arming/disarming, alarm mode switching, security code changes and configuration reset.

Security code entry notifications can be sent when incorrect codes are entered.

When configuration changes are made via the web interface, notifications can also be sent.

System notifications including notification types can be configured via the web interface on the **Pushover Settings** page.

### Changes

#### Compilation

SecureMe is now compiled to byte code to improve initialization speed and memory usage in constrained environments.

SecureMe can still be executed from source, however it is recommended to build before deploying to improve performance.

#### Web Interface

Renamed the **Pushover Credentials** page to **Pushover Settings** and added the new **System Notifications** settings.

Improved HTTP401 Unauthorized and HTTP400 Not Found errors to provide more information.

Implemented system status notifications support to send notifications when configuration changes are made.

#### Configuration

Implemented conditional checking for Pico W specific configuration settings. When running on Pico, these settings will not be checked.

#### Pico Network Manager

Updated Pico Network Manager to v1.0.4.

#### Automatic Update

Update files are now downloaded using MIP which is designed for installing modules and libraries.

#### Notifications

Notifications are now sent using background tasks to improve performance.

#### Alarm

Improved system performance when sounding an alarm by using background tasks.

## V1.1.6

### Bug Fixes

#### Automatic Update

Implemented a user agent in update requests to prevent access errors.

### Changes

#### Automatic Update

Automatic update is currently disabled due to memory allocation issues and will be re-enabled when resolved.

Automatic update now waits for 30 seconds before initializing to give the system time to settle.

Reduced the automatic update check interval to 30 minutes.

## V1.1.5

### Changes

#### Automatic Update

Automatic update now supports directory structures.

## V1.1.4

### Bug Fixes

#### Detection

Fixed missing global references which could cause issues with detection.

#### Automatic Update

Fixed an issue where the wrong repository URL was used.

Fixed an issue where incorrect API endpoints were queried for update information.

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
