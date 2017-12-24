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

from pi2graphite.version import VERSION, PROJECT_URL
from pi2graphite.config import Config
from pi2graphite.handler import MetricsHandler

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
        description='pi2graphite - RaspberryPi-targeted app to send 1wire '
                    'temperature & wifi stats to graphite. - <%s>' % PROJECT_URL
    )
    p.add_argument('-c', '--config', dest='config', type=str,
                   action='store', default='/etc/pi2graphite.json',
                   help='path to config.json (default: /etc/pi2graphite.json)')
    p.add_argument('-v', '--verbose', dest='verbose', action='count',
                   default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('--example-config', dest='example_config', default=False,
                   action='store_true',
                   help='write example config file to STDOUT')
    p.add_argument('-V', '--version', action='version',
                   version='pi2graphite v%s <%s>' % (
                       VERSION, PROJECT_URL
                   ))
    args = p.parse_args(argv)
    return args


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

    # dump example config if that action
    if args.example_config:
        conf, doc = Config.example_config()
        print(conf)
        sys.stderr.write(doc + "\n")
        return

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

    handler = MetricsHandler(config)
    handler.run()


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
