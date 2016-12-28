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
import os
from textwrap import dedent
from platform import node

from pi2graphite.utils import pretty_json, read_json_file

logger = logging.getLogger(__name__)


class InvalidConfigError(Exception):
    """Raised for configuration errors"""

    def __init__(self, message):
        msg = "Invalid Configuration File: %s" % message
        self._orig_message = message
        self.message = msg
        super(InvalidConfigError, self).__init__(msg)


class Config(object):

    _example = {
        'graphite': {
            'host': '127.0.0.1',
            'port': 2003,
            'metricPrefix': 'pi2graphite.%HOSTNAME%'
        },
        'send_wifi_metrics': True,
        'sensor_names': {
            '10-0008010ff558': 'tempA',
            '10-0008010ff563': 'tempB'
        },
        'logging_level': 'INFO',
        'polling_interval': 60
    }

    _example_docs = """
    Configuration description:

    graphite - Graphite server configuration:

      - 'host' - (string) Graphite hostname
      - 'port' - (int) Graphite plaintext port number to use
      - 'metricPrefix' - (string) Prefix to use for all metrics. "%HOSTNAME%"
        will be replaced with the system's current hostname.

    send_wifi_metrics - (boolean) Whether or not to send WiFi metrics.

    sensor_names - dict of sensor address (directory under /sys/bus/w1/devices/)
      to meaningful name to use instead of address, in metric names.

    logging_level - the Python logging level (constant name) to set for the
      lambda function. Defaults to INFO.

    polling_interval - (int) polling interval in seconds
    """

    def __init__(self, path):
        """
        Initialize configuration.

        :param path: path to configuration file on disk
        :type path: str
        """
        self.path = path
        self._config = self._load_config(path)
        self._validate_config()

    def _validate_config(self):
        """
        Validate configuration file.
        :raises: RuntimeError
        """
        # while set().issubset() is easier, we want to tell the user the names
        # of any invalid keys
        logger.debug('Validating configuration')
        bad_keys = []
        for k in self._config.keys():
            if k not in self._example.keys():
                bad_keys.append(k)
        if len(bad_keys) > 0:
            raise InvalidConfigError('Invalid keys: %s' % bad_keys)
        levels = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']
        if ('logging_level' in self._config and
                self._config['logging_level'] not in levels):
            raise InvalidConfigError('logging_level must be one of %s' % levels)
        logger.debug('Configuration validated.')

    def get(self, key):
        """
        Get the value of the specified configuration key. Return None if the
        key does not exist in the configuration.

        :param key: name of config key
        :type key: str
        :return: configuration value at specified key
        :rtype: object
        """
        return self._config.get(key, None)

    def _load_config(self, path):
        """
        Load configuration from JSON

        :param path: path to the JSON config file
        :type path: str
        :return: config dictionary
        :rtype: dict
        """
        p = os.path.abspath(os.path.expanduser(path))
        logger.debug('Loading configuration from: %s', p)
        return read_json_file(p)

    def metric_name_for_sensor(self, sensor_id):
        """
        Given a sensor ID (directory under /sys/bus/w1/devices/), return the
        desired human-readable metric name for it, or the original sensor_id
        if none is set.

        :param sensor_id: directory under /sys/bus/w1/devices/
        :type sensor_id: str
        :return: metric name to send
        :rtype: str
        """
        return self._config['sensor_names'].get(sensor_id, sensor_id)

    @property
    def graphite_host(self):
        """
        Return the Graphite hostname or IP

        :return: Graphite hostname or IP
        :rtype: str
        """
        return self._config['graphite'].get('host', '127.0.0.1')

    @property
    def graphite_port(self):
        """
        Return the Graphite plaintext port

        :return: Graphite port
        :rtype: int
        """
        return self._config['graphite'].get('port', 2003)

    @property
    def metric_prefix(self):
        """
        Return the Graphite metric prefix

        :return: Graphite metric prefix
        :rtype: str
        """
        pfx = self._config['graphite'].get(
            'metricPrefix', 'pi2graphite.%HOSTNAME%')
        hostname = node().replace('.', '_')
        return pfx.replace('%HOSTNAME%', hostname)

    @property
    def send_wifi_metrics(self):
        """
        Return whether or not to send wifi metrics.

        :return: whether or not to send wifi metrics
        :rtype: bool
        """
        return self._config.get('send_wifi_metrics', True)

    @property
    def polling_interval(self):
        """
        Return the polling interval in seconds.

        :return: polling interval in seconds
        :rtype: int
        """
        return self._config.get('polling_interval', 60)

    @property
    def logging_level(self):
        """
        Return the string name of the logging module level constant to set
        in the lambda function.

        :return: logging level constant name
        :rtype: str
        """
        level = self.get('logging_level')
        if level is None:
            level = 'INFO'
        return level

    @staticmethod
    def example_config():
        """
        Return a 2-tuple of example configuration file as a pretty-printed
        JSON string and documentation about it as a string.

        :rtype: tuple
        :returns: 2-tuple of (example config file as pretty-printed JSON string,
          documentation about it (str))
        """
        ex = pretty_json(Config._example)
        return ex, dedent(Config._example_docs)
