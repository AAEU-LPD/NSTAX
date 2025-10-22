1. Introduction

1.1 Purpose
  End user guide to setup test environment and execute already developed test scripts

2. Test System Requirement
  2.1 Hardware Requirement:
    1. Any PC/MAC/Linux machine capable of running python 3.x.
    2. Misc. cables / switches as connectors and peripherals required for specific tests

  2.2 Software Requirements:
    1. ###

  2.3 Network Requirements:
    1. WLAN or Wired ETH connection for internet access (only for installation / package DL)
    2. TBD: For logfile email feature

3. HW Installation
  3.1 Connect the RTC module to the pi system. Wiring diagram looks like below:
    - RTC VCC <=> Pi_GPIO_Pin4 (DS1307: 5V)
    - RTC VCC <=> Pi_GPIO_Pin1 (PCF8523 or DS3231: 3V)
    - RTC GND <=> Pi_GPIO_Pin6
    - RTC SDA <=> Pi_GPIO_Pin3
    - RTC SCL <=> Pi_GPIO_Pin5

  3.2 Connect the DUT in with PPK2 in series. The power bank powers the Raspberry Pi, Raspberry Pi powers the PPK2. Details in the following diagram:

4. SW Installation
  4.1 Setup OS
    1. Install Ubuntu [Server 23.04] in the SD card. Boot the systems. Example how-to: https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi
    2. Create user: "labpi" with any password (example pw: asdf1234)
    3. Boot the system
  4.2 Setup automatic booting of the system
    4.2.1. Edit /etc/systemd/logind.conf, add following lines
      [Login]
      NAutoVTs=1
      ReservedVT=2
    4.2.2. Create service directory
      sudo mkdir /etc/systemd/system/getty@tty1.service.d/
    4.2.3. Edit /etc/systemd/system/getty@tty1.service.d/override.conf to add the following lines:
      [Service]
      ExecStart=
      ExecStart=-/sbin/agetty --noissue --autologin labpi %I $TERM
      Type=idle
    4.2.4. Reboot
  4.3 Logger setup
    4.3.1. Link python3 to python command for convenience:
      sudo apt install python-is-python3
    4.3.2. Copy/Clone the logger package in the following directory: /home/labpi/dev/
    4.3.3. Schedule the script to be run every 30 minutes:
      crontab -e
      Add the line: "*/30 * * * * /usr/bin/python /home/labpi/dev/ppk2-logger/ppk2_logger_main.py"
      Note: cron logs are visible in /var/log/syslog
  4.4 Setup RTC
    4.4.1 Make RTC as the clock source:
      sudo apt install -y i2c-tools
      sudo i2cdetect -y 1 (to detect RTC module by ubuntu, ideally over the position 68)
      sudo modprobe rtc-ds1307 (load relevant kernel module)
      sudo echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device (must be run on bash)
      sudo i2cdetect -y 1 (to detect RTC module by ubuntu, now will show "UU" in position 68)
    4.4.2 Set RTC time. Example:
      sudo apt install util-linux-extra (to install hwclock)
      sudo hwclock -w
      sudo hwclock -r
    4.4.3 Make RTC as the default clock source
      TBD
    4.4.4 Persistence on reboot
      sudo echo dtoverlay=i2c-rtc,ds1307,addr=0x68 >> /boot/firmware/config.txt (in bash)
      sudo reboot
      sudo i2cdetect -y 1 (to detect RTC module by ubuntu, now will show "UU" in position 68)
    4.4.5 Kill RF (Bluetooth and WiFi)


sudo apt-get install -y rfkill
sudo rfkill blick wifi
sudo rfkill blick bluetooth

timedatectl set-ntp false
