#!/bin/bash

# Configure the wake-up watchdog
echo 'Configuring the wake-up watchdog (guaranteed wake mode)...'
i2cset -y 0x01 0x08 49 0x81

# Check the config
echo 'Checking the wake-up watchdog configuration...'
i2cget -y 0x01 0x08 49
echo 'Should return 0x81. If not, please check the configuration.'
