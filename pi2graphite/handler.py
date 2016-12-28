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
from datetime import datetime, timedelta
from time import sleep

from pi2graphite.graphiteclient import CachingGraphiteClient
from pi2graphite.wifi_collector import WifiCollector
from pi2graphite.onewire_collector import OneWireCollector

logger = logging.getLogger(__name__)


class MetricsHandler(object):

    def __init__(self, config):
        """
        Initialize the metrics handler.

        :param config: configuration
        :type config: pi2graphite.config.Config
        """
        logger.debug('Initializing MetricsHandler')
        self._config = config
        self._poll_delta = timedelta(seconds=config.polling_interval)
        self._graphite = CachingGraphiteClient(
            self._config.graphite_host,
            port=self._config.graphite_port,
            metric_prefix=self._config.metric_prefix
        )
        self._1wire = OneWireCollector(self._config)
        if self._config.send_wifi_metrics:
            self._wifi_collector = WifiCollector()

    def _poll_and_send(self):
        """
        Run one iteration of metrics polling and sending.
        """
        logger.info('Polling...')
        data = self.do_poll()
        self._graphite.send_data(data)

    def do_poll(self):
        """
        Do a single metrics poll. Return the result data as a list of 3-tuples,
        (metric name, value, integer timestamp).

        :return: poll result metric data
        :rtype: tuple
        """
        results = []
        results.extend(self._1wire.poll())
        if self._config.send_wifi_metrics:
            results.extend(self._wifi_collector.poll())
        return results

    def run(self):
        """
        Enter the main metrics polling loop.
        """
        logger.info('Entering main loop')
        while True:
            start = datetime.now()
            self._poll_and_send()
            poll_len = datetime.now() - start
            if poll_len > self._poll_delta:
                logger.info('Poll took longer than configured interval '
                            '(interval=%s, poll took %s)',
                            self._poll_delta, poll_len)
            else:
                s = (self._poll_delta - poll_len).total_seconds()
                logger.debug('Sleeping %s seconds until next poll', s)
                sleep(s)
