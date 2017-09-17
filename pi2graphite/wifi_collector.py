"""
The latest version of this package is available at:
<http://github.com/jantman/pi2graphite>

##################################################################################
Copyright 2016 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of pi2graphite, also known as pi2graphite.

    pi2graphite is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    pi2graphite is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with pi2graphite.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
##################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/pi2graphite> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
##################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
##################################################################################
"""

import logging
import time

import pythonwifi.flags
from pythonwifi.iwlibs import Wireless, Iwstats, getWNICnames

logger = logging.getLogger(__name__)


class WifiCollector(object):

    def __init__(self):
        pass

    def poll(self):
        """
        Poll. Return a data list of metric 3-tuples (name, value, timestamp)

        :return: data list of metric 3-tuples (name, value, timestamp)
        :rtype: list
        """
        logger.info('Polling WiFi stats')
        ts = int(time.time())
        stats = []
        try:
            nicnames = getWNICnames()
        except Exception:
            logger.error('Error getting WNIC names; cannot poll wifi',
                         exc_info=True)
            return []
        for n in nicnames:
            try:
                stats.extend(self._poll_nic(ts, n))
            except Exception:
                logger.error('Error polling NIC %s', n, exc_info=True)
        return stats

    def _poll_nic(self, ts, nicname):
        """
        Poll one NIC

        :param ts: data timestamp
        :type ts: int
        :param nicname: NIC name
        :type nicname: str
        :return: data list of metric 3-tuples (name, value, timestamp)
        :rtype: list
        """
        stats = [('%s.associated' % nicname, 1, ts)]
        logger.debug('Polling NIC: %s', nicname)
        wifi = Wireless(nicname)
        if wifi.getAPaddr() == '00:00:00:00:00:00':
            # unassociated; return that one stat now
            logger.warning('%s not associated (AP address 00:00:00:00:00:00',
                           nicname)
            return [('%s.associated' % nicname, 0, ts)]
        # tx power
        try:
            txpwr = wifi.wireless_info.getTXPower().value
        except IOError:
            try:
                txpwr = wifi.getTXPower().split(' ')[0]
            except IOError:
                logger.debug('Could not get TX Power for %s', nicname)
                txpwr = None
        if txpwr is not None:
            stats.append(('%s.txpower_dbm' % nicname, txpwr, ts))
        # bitrate
        try:
            br = wifi.wireless_info.getBitrate().value
            stats.append(('%s.bitrate' % nicname, br, ts))
        except Exception:
            logger.warning('Could not get birtate for %s', nicname, exc_info=1)
        # RTS
        try:
            rts = wifi.wireless_info.getRTS().value
            stats.append(('%s.rts' % nicname, rts, ts))
        except Exception:
            logger.warning('Could not get RTS for %s', nicname, exc_info=1)
        # statistics
        try:
            s = Iwstats(nicname)
            for k in s.discard.keys():
                stats.append(
                    ('%s.discard_%s' % (nicname, k),
                     s.discard.get(k, 0), ts)
                )
            stats.append(('%s.missed_beacons' % nicname, s.missed_beacon, ts))
            # Current Quality
            stats.append(('%s.quality' % nicname, s.qual.quality, ts))
            stats.append(('%s.noise_level' % nicname, s.qual.nlevel, ts))
            stats.append(('%s.signal_level' % nicname, s.qual.siglevel, ts))
        except Exception:
            logger.warning('Could not get stats for %s', nicname, exc_info=1)
        return stats
