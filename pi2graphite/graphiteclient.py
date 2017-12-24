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
import socket
import os
import time

logger = logging.getLogger(__name__)


class CachingGraphiteClient(object):
    """
    Graphite client that caches data locally and sends when connection
    resumes.
    """

    def __init__(self, host, port=2003, metric_prefix=''):
        """
        Initialize CachingGraphiteClient.

        :param host: graphite host name or IP
        :type host: str
        :param port: graphite plaintext port
        :type port: int
        :param metric_prefix: prefix to prepend to all metrics
        :type metric_prefix: str
        """
        self._host = host
        self._port = port
        self._metric_prefix = metric_prefix
        self._cache_dir = '/var/lib/pi2graphite'
        if not os.path.exists(self._cache_dir):
            logger.info('Creating cache directory at: %s', self._cache_dir)
            os.mkdir(self._cache_dir)

    def _graphite_str(self, data_list):
        """
        Generate a string to send to Graphite.

        :param data_list: list of 3-tuples:
          (metric name, value, integer timestamp)
        :type data_list: ``list``
        :return: string to send to Graphite
        :rtype: str
        """
        parts = [
            "%s.%s %s %d" % (
                self._metric_prefix, t[0], t[1], t[2]) for t in data_list
        ]
        return "\n".join(parts) + "\n"

    def _graphite_send(self, send_str):
        """
        Send data to graphite

        :param send_str: data string to send
        :type send_str: str
        :returns: True if send succeeded, False if exception caught
        :rtype: bool
        """
        try:
            logger.debug('Opening socket connection to %s:%s',
                         self._host, self._port)
            sock = socket.create_connection((self._host, self._port), 10)
            logger.debug('Sending data: "%s"', send_str)
            sock.sendall(send_str)
            logger.info('Data sent to Graphite')
            sock.close()
            return True
        except Exception:
            logger.error('Caught exception sending to Graphite', exc_info=True)
        return False

    def _flush_cache(self):
        """
        Find and flush all cached metrics.
        """
        files = [
            f for f in os.listdir(self._cache_dir)
            if os.path.isfile(os.path.join(self._cache_dir, f))
        ]
        if len(files) == 0:
            logger.debug('No cache files to flush')
            return
        logger.info('Found %d data cache files to send', len(files))
        for f in files:
            fpath = os.path.join(self._cache_dir, f)
            with open(fpath, 'r') as fh:
                data = fh.read()
            res = self._graphite_send(data)
            if not res:
                logger.error('Error: graphite send failed during cache flush')
                return
            os.unlink(fpath)
        logger.debug('Done flushing cache')
        self.send_data(
            [(
                'pi2graphite.cached_sets_flushed',
                len(files),
                int(time.time())
            )]
        )

    def _cache_data(self, data_str):
        """
        Cache data that we couldn't send on disk.
        :param data_str: string of data to send
        :type data_str: str
        """
        fname = os.path.join(self._cache_dir, '%d.json' % int(time.time()))
        logger.warning('Caching un-sendable data at: %s', fname)
        with open(fname, 'w') as fh:
            fh.write(data_str)

    def send_data(self, data_list):
        """
        Send metrics to Graphite.

        :param data_list: list of 3-tuples:
          (metric name, value, integer timestamp)
        :type data_list: ``list``
        """
        data_s = self._graphite_str(data_list)
        res = self._graphite_send(data_s)
        if res:
            logger.info('Successfully sent data to Graphite')
            self._flush_cache()
            return
        # sending failed
        logger.error('Sending data to Graphite failed; caching on disk.')
        self._cache_data(data_s)
