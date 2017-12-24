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

from w1thermsensor import W1ThermSensor

logger = logging.getLogger(__name__)


class OneWireCollector(object):

    def __init__(self, config):
        self._1w = W1ThermSensor()
        self._config = config

    def poll(self):
        """
        Poll. Return a data list of metric 3-tuples (name, value, timestamp)

        :return: data list of metric 3-tuples (name, value, timestamp)
        :rtype: ``list``
        """
        logger.info('Polling w1')
        ts = int(time.time())
        stats = []
        try:
            sensors = self._1w.get_available_sensors()
        except Exception:
            logger.error("Unable to list 1wire sensors", exc_info=True)
            return []
        for sensor in sensors:
            try:
                stats.extend(self._poll_sensor(sensor, ts))
            except Exception:
                logger.error('Error polling sensor %s', sensor, exc_info=True)
        return stats

    def _poll_sensor(self, sensor, ts):
        """
        Return stats for a single sensor.

        :param sensor: The sensor to return stats for
        :type sensor: ``w1thermsensor.core.W1ThermSensor``
        :param ts: data timestamp
        :type ts: int
        :return: data list of metric 3-tuples (name, value, timestamp)
        :rtype: ``list``
        """
        dirname = '%s%s' % (sensor.slave_prefix, sensor.id)
        name = self._config.metric_name_for_sensor(dirname)
        logger.debug('Polling sensor %s%s (metric name: %s)',
                     sensor.slave_prefix, sensor.id, name)
        temps = sensor.get_temperatures([
            W1ThermSensor.DEGREES_C,
            W1ThermSensor.DEGREES_F])
        return [
            ('%s.temp_c' % name, temps[0], ts),
            ('%s.temp_f' % name, temps[1], ts)
        ]
