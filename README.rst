pi2graphite
===========

RaspberryPi-targeted app to send OWFS temperature & wifi stats to graphite.

Overview
--------

This is a really quick hack. It's a daemon written in Python, aimed at the
RaspberryPi. It reads `Dallas Semi 1-Wire <https://en.wikipedia.org/wiki/1-Wire>`_
temperature sensors and sends the data to a `Graphite <https://graphiteapp.org/>`_
server on another system. For fun, it also attempts (if the Pi is connected via
  WiFi) to grab WiFi signal strength metrics and send those as well.

Hardware Installation/Setup
---------------------------

OS Installation on RPi
++++++++++++++++++++++

I used this same process for

1. Write the latest `Raspbian Image <https://www.raspberrypi.org/downloads/raspbian/>`_
   to an appropriate SD card. I'm testing using the 2016-11-25 (4.4 kernel)
   "Raspbian Jessie Lite" image.
2. When it's done writing, figure out the device name on your system and, as root,
   run ``setup_raspbian.sh`` to configure it. This will:
    1. Create a temporary directory and mount the SD card partitions in it.
    2. Enable `SSH at boot <https://www.raspberrypi.org/documentation/remote-access/ssh/README.md>`_.
    3. Copy over a specified authorized_keys file to the pi user.
    4. Set the hostname.
    5. If the arguments were specified, configure wifi.
    6. Enable the ``w1-gpio`` kernel module in ``/boot/config.txt``, with the ``pullup=1`` parameter for a pullup resistor.
    7. Umount the SD card and remove the remporary directory.
3. Remove the SD card and put it in the pi, then boot it. Eventually, it _should_
   join your WiFi network and get an IP address, at which point you can SSH to it.
4. When you SSH in, you may want to run `raspi-config <https://github.com/RPi-Distro/raspi-config>`_ to do things such as setting the locale and timezone. If the SSH authorized keys setup failed, the default Raspbian user is named ``pi``, with the password ``raspberry``. You may want to change the password, but I'm
only running mine on an isolated WiFi network, so I didn't.

Miscellaneous
-------------

References
++++++++++

* `RaspberryPi config.txt reference <https://www.raspberrypi.org/documentation/configuration/config-txt.md>`_

WiFi Drivers
++++++++++++

I bought a bunch of _cheap_ USB WiFi dongles, all of which either advertised "Linux support" or were recommended for the RPi.

* `TP-LINK AC600 Archer T2UH <http://www.frys.com/product/8730871>`_ from Fry's (external antenna, 2.4/5GHz) with USB vendor 148f and product 761a, showing up as a MediaTek. I have a package for the driver `here <http://jantman-personal-public.s3-website-us-east-1.amazonaws.com/xtknight-mt7610u-linksys-ae6000-wifi-fixes_1.cd80ce6-1_armhf.deb>`_, built with the below instructions but replacing #5 with ``sudo checkinstall --install=no -D --fstrans --pkgname xtknight_mt7610u-linksys-ae6000-wifi-fixes --pkgversion 1.cd80ce6 --pkgrelease 1 --arch armhf --pkgsource 'https://github.com/xtknight/mt7610u-linksys-ae6000-wifi-fixes/tree/cd80ce63004c0a8880df712173b7def99288c518' --maintainer 'Jason\ Antman\ \<jason@jasonantman.com\>' --provides mt7610u_sta --requires 'raspberrypi-kernel \(= 1.20161215-1\)' --inspect --review-control`` and removing the ``/lib/modules/4.4.38+/modules.*`` files from the file list. After installing that package, you'll still need to create the interface config file in #8 and reboot.

    1. ``apt-get update && apt-get install gcc make git build-essential && apt-get dist-upgrade && apt-get install raspberrypi-kernel-headers`` (it appears that the repo only has headers for the latest kernel, so make sure you're running that)
    2. ``reboot``
    3. ``mkdir ~/src && cd ~/src && git clone https://github.com/xtknight/mt7610u-linksys-ae6000-wifi-fixes.git && cd mt7610u-linksys-ae6000-wifi-fixes``
    4. ``make``
    5. ``sudo make install``
    6. Reboot, or ``sudo modprobe mt7610u_sta``
    7. Ok, ``ifconfig`` should now show you an ``ra0`` interface that's up with a self-assigned (169.254) IP address. ``iw list`` shows ``ra0`` with support for 2.4GHz and 5GHz, as does ``iw phy``. ``iw dev`` shows the device. ``iwlist ra0 scan`` should show results for both 2.4GHz and 5GHz SSIDs.
    8. Create ``/etc/network/interfaces.d/ra0`` with the following:
        ```
        allow-hotplug ra0
        iface ra0 inet manual
            wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
        ```
    9. Reboot. You should now be connected to your network.
* `Glam Hobby 300Mbps 802.11b/g/n <https://www.amazon.com/gp/product/B016Z1UBD8/>`_ from Amazon (external antenna) with USB vendor 0bda and product 818b, showing up as a Realtek 802.11n NIC, which the Internet says is a RTL8192EU. I found `this thread <https://www.raspberrypi.org/forums/viewtopic.php?f=45&t=103989&start=100>`_ by MrEngman on the raspberrypi.org forums that offers precompiled binary drivers for it. My system ``uname -a`` shows ``4.4.38+ #938`` and I was able to grab the actual URL for the driver from his installer script, download it, and make a package that's `here <http://jantman-personal-public.s3-website-us-east-1.amazonaws.com/8192eu_1.4.4.38.938-1_armhf.deb>`_ using his tarball with a Makefile generated from the install script (to just move the two files into place and run depmod) and ``sudo checkinstall --install=no -D --fstrans --pkgname 8192eu --pkgversion 1.4.4.38.938 --pkgrelease 1 --arch armhf --pkgsource 'https://www.raspberrypi.org/forums/viewtopic.php\?t=103989' --maintainer 'Jason\ Antman\ \<jason@jasonantman.com\>' --provides 8192eu --requires 'raspberrypi-kernel \(= 1.20161215-1\)' --inspect --review-control``.
    1. Download that package and ``dpkg -i FILENAME`` it.
    2. Reboot. If you don't see a ``wlan0`` interface, you may need to ``depmod $(uname -r) && modprobe 8192eu``.
* `Kootek Raspberry Pi Wifi Dongle Adapter <https://www.amazon.com/gp/product/B00FWMEFES/>`_ from Amazon (mini bluetooth-style dongle) - worked out of the box

One-Wire Temperature Sensors
++++++++++++++++++++++++++++

I'm using the DS18S20P. I have Ground wired to ground on the Pi, Power (Vdd) wired
to one of the 3v3 pins on the Pi, Data (DQ) wired to GPIO (BCM) 4 on the Pi,
and a 1/4w 4.7k ohm resistor wired between the Data and Power lines. This works
with ``dtoverlay=w1-gpio,pullup=1`` added to ``/boot/config.txt``.
