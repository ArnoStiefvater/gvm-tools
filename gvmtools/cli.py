# -*- coding: utf-8 -*-
# Copyright (C) 2018 Greenbone Networks GmbH
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import getpass
import logging
import sys

from gvm.protocols.latest import Gmp
from gvm.transforms import CheckCommandTransform

from gvmtools.parser import create_parser, create_connection


logger = logging.getLogger(__name__)

HELP_TEXT = """
    Command line tool to access services via GMP (Greenbone Management Protocol) and OSP (Open Scanner Protocol)

    Examples:
      gvm-cli socket --help
      gvm-cli tls --help
      gvm-cli ssh --help

      gvm-cli socket --xml "<get_version/>"
      gvm-cli socket --xml "<commands><authenticate><credentials><username>myuser</username><password>mypass</password></credentials></authenticate><get_tasks/></commands>"
      gvm-cli socket --gmp-username foo --gmp-password foo < myfile.xml

    The protocol specifications for GMP and OSP are available at:
      https://docs.greenbone.net/index.html#api_documentation"""


def main():
    parser = create_parser(description=HELP_TEXT, logfilename='gvm-cli.log')

    parser.add_argument('-X', '--xml', help='XML request to send')
    parser.add_argument('-r', '--raw', help='Return raw XML',
                        action='store_true', default=False)
    parser.add_argument('infile', nargs='?', type=open, default=sys.stdin)

    args = parser.parse_args()

    # If timeout value is -1, then the socket has no timeout for this session
    if args.timeout == -1:
        args.timeout = None

    xml = ''

    if args.xml is not None:
        xml = args.xml
    else:
        # If this returns False, then some data are in sys.stdin
        if not args.infile.isatty():
            try:
                xml = args.infile.read()
            except (EOFError, BlockingIOError) as e:
                print(e)

    # If no command was given, program asks for one
    if len(xml) == 0:
        xml = input()

    # Ask for password if none are given
    if args.gmp_username and not args.gmp_password:
        args.gmp_password = getpass.getpass('Enter password for ' +
                                            args.gmp_username + ': ')

    connection = create_connection(**vars(args))

    if args.raw:
        transform = None
    else:
        transform = CheckCommandTransform()

    gvm = Gmp(connection, transform=transform)

    if args.gmp_username:
        gvm.authenticate(args.gmp_username, args.gmp_password)

    try:
        result = gvm.send_command(xml)

        print(result)
    except Exception as e: # pylint: disable=broad-except
        print(e)
        sys.exit(1)

    gvm.disconnect()

    sys.exit(0)


if __name__ == '__main__':
    main()
