#!/bin/bash

# Configure the wake-up watchdog
echo 'Configuring the wake-up watchdog (guaranteed wake mode)...'
i2cset -y 0x01 0x08 49 0x82

# Check the config
echo 'Checking the wake-up watchdog configuration...'
i2cget -y 0x01 0x08 49
echo 'Should return 0x82. If not, please check the configuration.'

# Check the RTC offset
echo 'Checking the RTC offset...'
i2cget -y 1 8 37