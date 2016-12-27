# pi2graphite

RaspberryPi-targeted app to send OWFS temperature & wifi stats to graphite.

## Overview

This is a really quick hack. It's a daemon written in Python, aimed at the
RaspberryPi. It reads [Dallas Semi 1-Wire](https://en.wikipedia.org/wiki/1-Wire)
temperature sensors and sends the data to a [Graphite](https://graphiteapp.org/)
server on another system. For fun, it also attempts (if the Pi is connected via
  WiFi) to grab WiFi signal strength metrics and send those as well.

## Hardware Installation/Setup

### OS Installation on RPi

I used this same process for

1. Write the latest [Raspbian Image](https://www.raspberrypi.org/downloads/raspbian/)
   to an appropriate SD card. I'm testing using the 2016-11-25 (4.4 kernel)
   "Raspbian Jessie Lite" image.
2. When it's done writing, figure out the device name on your system and, as root,
   run ``setup_raspbian.sh`` to configure it. This will:
    1. Create a temporary directory and mount the SD card partitions in it.
    2. Enable [SSH at boot](https://www.raspberrypi.org/documentation/remote-access/ssh/README.md).
    3. Copy over a specified authorized_keys file to the pi user.
    4. Set the hostname.
    5. If the arguments were specified, configure wifi.
    6. Umount the SD card and remove the remporary directory.
3. Remove the SD card and put it in the pi, then boot it. Eventually, it _should_
   join your WiFi network and get an IP address, at which point you can SSH to it.
4. When you SSH in, you may want to run [``raspi-config``](https://github.com/RPi-Distro/raspi-config) to do things such as setting the locale and timezone. If the SSH authorized keys setup failed, the default Raspbian user is named ``pi``, with the password ``raspberry``. You may want to change the password, but I'm
only running mine on an isolated WiFi network, so I didn't.

## Miscellaneous

### References

* [RaspberryPi config.txt reference](https://www.raspberrypi.org/documentation/configuration/config-txt.md)

### WiFi Drivers

I bought a bunch of _cheap_ USB WiFi dongles, all of which either advertised "Linux support" or were recommended for the RPi.

* [TP-LINK AC600 Archer T2UH](http://www.frys.com/product/8730871) from Fry's (external antenna, 2.4/5GHz) -
    1. ``apt-get update && apt-get install gcc make git build-essential && apt-get dist-upgrade && apt-get install raspberrypi-kernel-headers``
    2. ``reboot``
    3. ``mkdir ~/src && cd ~/src && git clone https://github.com/lixz789/mt7610u_wifi_sta_v3002_dpo_20130916.git && cd mt7610u_wifi_sta_v3002_dpo_20130916``
    4. ``make``
    5. ``sudo make install && cp RT2870STA.dat /etc/Wireless/RT2870STA/``
    6. Reboot.
    7. Ok, ``ifconfig`` should now show you an ``ra0`` interface. ``iwlist ra0 scan`` shows results for 2.4GHz only, and ``iw phy`` and ``iw dev`` report nothing... Because apparently this driver doesn't play nice with ``iw`` or anything else, and is supposed to be configured via that ``/etc/Wireless/RT2870STA/RT2870STA.dat`` file... because this driver is based on a vendor driver, which likely was written by someone who either (a) was told to write a driver as cheap and quick as possible, or (b) has been modifying the same driver source since the 2.0 kernel was released.
* [Glam Hobby 300Mbps 802.11b/g/n](https://www.amazon.com/gp/product/B016Z1UBD8/) from Amazon (external antenna) -
* [Kootek Raspberry Pi Wifi Dongle Adapter](https://www.amazon.com/gp/product/B00FWMEFES/) from Amazon (mini bluetooth-style dongle) - worked out of the box
