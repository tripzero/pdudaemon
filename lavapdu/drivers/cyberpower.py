#! /usr/bin/env python

#
#  cyberpower PUD driver derived heavily from apcbase.py
#

#
#  Copyright (C) 2017 Intel Corporation
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.


import logging
import pexpect
from lavapdu.drivers.driver import PDUDriver
log = logging.getLogger(__name__)

class CyberPower(PDUDriver):

    def __init__(self, hostname, settings):
        self.hostname = hostname
        log.debug(settings)
        self.settings = settings
        self.username = "cyber"
        self.password = "cyber"
        telnetport = 23
        self.product_name = "PDU81002"

        if "telnetport" in settings:
            telnetport = settings["telnetport"]
        if "username" in settings:
            self.username = settings["username"]
        if "password" in settings:
            self.password = settings["password"]
        if "product" in settings:
            self.product_name = settings["product"]

        self.exec_string = "/usr/bin/telnet %s %d" % (hostname, telnetport)
        self.get_connection()
        super(PDUDriver, self).__init__()


    @classmethod
    def accepts(cls, drivername):
        if drivername == "pdu81002":
            return True
        return False


    def _activate_port(self, port, command):
        self.connection.expect("Command Information: Step 1")
        log.debug("process output: {}".format(self.connection.before))
        self.connection.expect("> ")
        log.debug("process output: {}".format(self.connection.before))
        self.connection.send("{}\r".format(port))

        self.connection.expect("Command Information: Step 2")
        log.debug("process output: {}".format(self.connection.before))
        self.connection.expect("> ")
        log.debug("process output: {}".format(self.connection.before))

        if command == "on":
            self.connection.send("1\r")
        elif command == "off":
            self.connection.send("2\r")
        elif command == "reboot":
            self.connection.send("3\r")

        # confirm the step
        self.connection.expect("Command Information: Step 3")
        log.debug("process output: {}".format(self.connection.before))
        self.connection.expect("> ")
        log.debug("process output: {}".format(self.connection.before))
        self.connection.send("yes\r")

        self.connection.expect("Outlet Control")
        log.debug("process output: {}".format(self.connection.before))


    def port_interaction(self, command, port_number):
        log.debug("Attempting command: %s port: %i", command, port_number)
        # make sure in main menu here
        self._back_to_main()
        log.debug("sending RETURN")

        self.connection.send("\r")

	#Main Menu

        log.debug("process output: {}".format(self.connection.before))
        self.connection.expect("1- Device Manager")
        self.connection.expect("> ")
        log.debug("Entering Device Manager")
        log.debug("process output: {}".format(self.connection.before))

        log.debug("sending 1 and RETURN")
        self.connection.send("1\r")
        log.debug("process output: {}".format(self.connection.before))

	#Device Manager Menu

        self.connection.expect("{}".format(self.product_name))
	self.connection.expect("> ")
        log.debug("process output: {}".format(self.connection.before))
        self.connection.send("2\r")

	#

        self.connection.expect("1- Start a Control Command")
        log.debug("process output: {}".format(self.connection.before))
        self.connection.expect("> ")
        log.debug("process output: {}".format(self.connection.before))

        log.debug("sending 1 and RETURN")
        self.connection.send("1\r")
        log.debug("process output: {}".format(self.connection.before))

        self._activate_port(port_number, command)


    def _bombout(self):
        log.debug("Bombing out of driver: %s", self.connection)
        self.connection.close(force=True)
        del self


    def _cleanup(self):
        self._pdu_logout()


    def _pdu_logout(self):
        self._back_to_main()
        log.debug("Logging out")
        log.debug("sending RETURN")
        self.connection.send("\r")
        self.connection.expect("> ")
        log.debug("sending 4 and RETURN")
        self.connection.send("4\r")


    def _back_to_main(self):
        log.debug("Returning to main menu")
        self.connection.send("\r")
        self.connection.expect('>')
        res = 1
        for _ in range(1, 20):
            log.debug("sending ESC and RETURN")
            self.connection.send('\x1B')
            self.connection.send("\r")
            res = self.connection.expect(["4- Logout", "> "])
            log.debug("process output: {}".format(self.connection.before))
            if res == 0:
                log.debug("Back at main menu")
                break

        if res != 0:
            raise Exception("Failed to get back to main menu: ({})".format(res))




    def get_connection(self):
        log.debug("Connecting to CyberPower PDU with: %s", self.exec_string)
        # only uncomment this line for FULL debug when developing
        # self.connection = pexpect.spawn(self.exec_string, logfile=sys.stdout)
        self.connection = pexpect.spawn(self.exec_string)
        self.connection.delaybeforesend = 0.5
        self._pdu_login(self.username, self.password)


    def _pdu_login(self, username, password):
        log.debug("attempting login with username %s, password %s",
                  username, password)
        self.connection.expect("CyberPowerSystems Inc., Command Shell v1.0")
        self.connection.expect("Login Name: ")
        log.debug("process output: {}".format(self.connection.before))
        self.connection.send("%s\r" % username)
        self.connection.expect("Login Password: ")
        log.debug("process output: {}".format(self.connection.before))
        self.connection.send("%s\r" % password)
        self.connection.expect("Please wait for authentication...")
        log.debug("process output: {}".format(self.connection.before))
