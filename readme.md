# Goat - SecureMe

A portable, movable security system designed for versatility and ease of use.

## Overview

**Goat - SecureMe** is a DIY security system that offers advanced functionality using simple and affordable hardware. Perfect for hobbyists and beginners, it provides a customizable solution for personal or property security.

With features like motion detection, network connectivity, and a web interface, SecureMe ensures you can monitor and manage your system effortlessly. Whether you’re protecting a room, a bag, or any valuable item, SecureMe is your portable guardian.

---

## Features

SecureMe comes packed with the following features:

- **Motion Detection**  
  Detect movement using a PIR sensor to trigger alarms or notifications.

- **Tilt Detection**  
  Monitor tilt or movement of the device itself using a tilt sensor.

- **Alarm Sounds**  
  Choose between various alarm sounds emitted by the onboard buzzer to suit your environment.

- **Activity Feedback**  
  Visual and audio feedback through flashing LEDs and distinct buzzer tones.

- **Security Features**  
  Protect your system with a customizable security code to arm/disarm, switch alarm modes, or reset the configuration.

- **Network Connectivity**  
  Connect to Wi-Fi networks using a captive portal for seamless setup.

- **Web Interface**  
  Configure and manage SecureMe through a user-friendly, password-protected web interface.

- **Customizable Sensor Cooldown**  
  Set cooldown times for connected sensors to prevent redundant triggers.

- **Silent Alarm**  
  Enable silent mode to receive push notifications without sounding a physical alarm.

---

## Getting Started

### Requirements

To build and deploy Goat - SecureMe, you will need:

1. **Hardware Components**:
   - Microcontroller (e.g., Raspberry Pi Pico or Pico W for wireless connectivity)
   - PIR motion sensor
   - Tilt sensor
   - Passive buzzer
   - Matrix keypad (4x4)
   - System LED is used
   - Breadboard or prototyping PCB
   - Power supply or battery pack
   - Jumper wires and resistors as needed

2. **Software**:
   - MicroPython or CircuitPython
   - Required Python libraries (all native to the SecureMe firmware distribution)

---

## Setup Instructions

1. **Hardware Setup**:
   - Place the power supply in the top of your breadboard.
   - Place the microcontroller just under the power supply (making sure to leave room for USB).
   - Connect VSYS on the Pico to VCC and then connect GND.
   - Place the tilt switch sensor just beneath the microcontroller.
   - Place the passive buzzer beneath the tilt switch sensor.
   - Mount two small buttons for volume control on one side of the board beside the buzzer.
   - Mount three larger buttons vertically down the middle of the board.
   - Connect one leg of the buzzer to the GND rail and the other leg to GPIO1.
   - Connect the left leg of the PIR sensor to the 5V power rail and the right leg to GND, then connect the middle leg to GPIO2.
   - Connect one leg of the tilt switch to VCC and the other leg to GPIO3.
   - Connect the vertical buttons starting from the bottom to VCC and GPIO4, 5, and 6.
   - Connect the four pins on the right side of the matrix keypad to GPIO7, 8, 9, and 10 starting from the leftmost pin.
   - Connect the four pins on the left side of the matrix keypad to GPIO11, 12, 13, and 14 starting from the leftmost pin.
   - Connect the two volume buttons to VCC and GPIO15 and 16.
   - Ensure all connections are secure and components are powered.

2. **Software Setup**:
   - Flash the microcontroller with MicroPython/CircuitPython firmware.
   - Upload the SecureMe source code and dependencies to the microcontroller.

3. **Network Configuration**:
   - Connect to the device's hotspot to access the captive portal.
   - Note that the password ***secureme*** is required for the hotspot.
   - Connect to the captive portal. If not automatically redirected, visit [http://192.168.4.1](http://192.168.4.1).
   - Scan for wireless networks and enter your Wi-Fi credentials to establish network connectivity.

4. **Web Interface**:
   - Access the web interface using the device's IP address to configure and customize settings.

---

## Usage Scenarios

- **Portable Bag Security**: Attach SecureMe to a bag for motion and tilt detection.
- **Home Monitoring**: Place SecureMe in a room to detect intrusions or unauthorized access.
- **Silent Alarm Setup**: Monitor spaces discreetly with silent push notifications.

---

## Future Enhancements

The project roadmap includes:
- Enhanced notification options (SMS, email alerts).
- Support for additional sensors (e.g., ultrasonic).
- Integration with third-party automation systems.

---
