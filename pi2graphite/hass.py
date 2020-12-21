# -*- coding: utf-8 -*-
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

import sys
import argparse
import logging

import requests

from pi2graphite.version import VERSION, PROJECT_URL
from pi2graphite.config import Config
from pi2graphite.onewire_collector import OneWireCollector

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()


def parse_args(argv):
    """
    Use Argparse to parse command-line arguments.

    :param argv: list of arguments to parse (``sys.argv[1:]``)
    :type argv: ``list``
    :return: parsed arguments
    :rtype: :py:class:`argparse.Namespace`
    """
    p = argparse.ArgumentParser(
        description='pi2hass - RaspberryPi-targeted app to send 1wire '
                    'temperature stats to HomeAssistant via HTTP Sensor.'
                    ' Sends immediately and exits (cron) - <%s>' % PROJECT_URL
    )
    p.add_argument('-c', '--config', dest='config', type=str,
                   action='store', default='/etc/pi2graphite.json',
                   help='path to config.json (default: /etc/pi2graphite.json)')
    p.add_argument('-v', '--verbose', dest='verbose', action='count',
                   default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-V', '--version', action='version',
                   version='pi2graphite v%s <%s>' % (
                       VERSION, PROJECT_URL
                   ))
    p.add_argument('-u', '--url', dest='url', action='store', type=str,
                   required=True,
                   help='HomeAssistant base URL, '
                        'i.e. http://hostname:8123')
    p.add_argument(
        '-t', '--token', dest='token', action='store', type=str, default=None,
        help='HomeAssistant Long-Lived Access Token'
    )
    args = p.parse_args(argv)
    return args


class HassSender(object):

    def __init__(self, config, url, token=None):
        self._config = config
        self._url = url
        self._token = token
        if not self._url.endswith('/'):
            self._url += '/'
        self._1wire = OneWireCollector(self._config)

    def _do_post(self, name, value):
        sensor_id = 'pi2graphite_1wire_%s' % name
        d = {
            'state': round(value, 2),
            'attributes': {
                'unit_of_measurement': u'°F',
                'friendly_name': '%s Temperature' % name.capitalize()
            }
        }
        url = '%sapi/states/sensor.%s' % (self._url, sensor_id)
        logger.info('POST to %s - %s', url, d)
        kwargs = {'json': d, 'timeout': 10}
        if self._token is not None:
            kwargs['headers'] = {
                'Authorization': 'Bearer %s' % self._token
            }
        r = requests.post(url, **kwargs)
        logger.info('Server response %s: %s', r.status_code, r.text)
        r.raise_for_status()

    def send(self):
        logger.debug('Polling 1-wire sensors')
        result = self._1wire.poll()
        logger.debug('Poll result: %s', result)
        for tup in result:
            parts = tup[0].split('.')
            if parts[1] != 'temp_f':
                continue
            if tup[1] == 185.0:
                logger.error(
                    'Got erroneous temperature of 185.0 F; skipping'
                )
                continue
            self._do_post(parts[0], tup[1])
        logger.info('Done sending results.')


def set_log_info():
    """set logger level to INFO"""
    set_log_level_format(logging.INFO,
                         '%(asctime)s %(levelname)s:%(name)s:%(message)s')


def set_log_debug():
    """set logger level to DEBUG, and debug-level output format"""
    set_log_level_format(
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s"
    )


def set_log_level_format(level, format):
    """
    Set logger level and format.

    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param format: logging formatter format string
    :type format: str
    """
    formatter = logging.Formatter(fmt=format)
    logger.handlers[0].setFormatter(formatter)
    logger.setLevel(level)


def main(args=None):
    """
    Main entry point
    """
    # parse args
    if args is None:
        args = parse_args(sys.argv[1:])

    # set logging level
    if args.verbose > 1:
        set_log_debug()
    elif args.verbose == 1:
        set_log_info()

    # get our config
    config = Config(args.config)
    if args.verbose == 0:
        if config.logging_level == 'DEBUG':
            set_log_debug()
        elif config.logging_level == 'INFO':
            set_log_info()

    HassSender(config, args.url, token=args.token).send()


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
