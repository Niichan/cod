#!/usr/bin/python

import config
import socket
from structures import *
from commands import *
from bot import *
from mpd import MPDClient

commands = {}

commands["EUID"] = [handleEUID]
commands["QUIT"] = [handleQUIT]
commands["SJOIN"] = [handleSJOIN]
commands["NICK"] = [handleNICK]
commands["BMASK"] = [handleBMASK]
commands["MODE"] = [handleMODE]
commands["TMODE"] = [handleTMODE]
commands["CHGHOST"] = [handleCHGHOST]
commands["WHOIS"] = [handleWHOIS]
commands["PRIVMSG"] = [handlePRIVMSG]
commands["NOTICE"] = [handlePRIVMSG]
commands["JOIN"] = [handleJOIN]
commands["SID"] = [handleSID]
commands["KILL"] = [handleKILL]

commands["AWAY"] = [nullCommand]
commands["PING"] = [nullCommand]
commands["ENCAP"] = [nullCommand]

class Cod():
    def __init__(self):
        self.link = socket.socket()

        self.clients = {}
        self.channels = {}
        self.servers = {}

        self.bursted = False

        self.config = config.Config("../config.json").config

        print "--- Establishing connection to uplink"

        self.link.connect((self.config["uplink"]["host"], self.config["uplink"]["port"]))

        print "--- done"
        print "--- Establishing connection to MPD server"

        self.mpd = MPDClient()
        self.mpd.timeout = 10
        self.mpd.idletimeout = None
        self.mpd.connect(self.config["mpd"]["host"], self.config["mpd"]["port"])

        print "--- done"
        print "--- Sending credentials to remote IRC server"

        self.sendLine("PASS %s TS 6 :%s" %
                (self.config["uplink"]["pass"], self.config["uplink"]["sid"]))
        self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP SERVICES EUID EOPMOD")
        self.sendLine("SERVER %s 1 :%s" %
                (self.config["me"]["name"], self.config["me"]["desc"]))

        print "--- done"
        print "--- Creating and bursting client"

        self.client = makeService(self.config["me"]["nick"],
                self.config["me"]["user"], self.config["me"]["host"],
                self.config["me"]["desc"], self.config["uplink"]["sid"] + "CODFIS")

        self.clients[self.config["uplink"]["sid"] + "CODFIS"] = self.client

        self.sendLine(self.client.burst())

        print "--- done"

        if self.config["etc"]["prettyprint"]:
            commands["PRIVMSG"].append(prettyPrintMessages)

        if self.config["etc"]["relayhostserv"]:
            commands["PRIVMSG"].append(relayHostServToOpers)

        print "!!! Cod initialized"

    def rehash(self):
        self.config = config.Config("../config.json").config

        self.mpd = MPDClient()
        self.mpd.timeout = 10
        self.mpd.idletimeout = None
        self.mpd.connect(self.config["mpd"]["host"], self.config["mpd"]["port"])

        for channel in cod.config["me"]["channels"]:
            cod.join(channel)

    def sendLine(self, line):
        if self.config["etc"]["debug"]:
            print ">>> %s" % line

        self.link.send("%s\r\n" % line)

    def privmsg(self, target, line):
        self.sendLine(":%s PRIVMSG %s :%s" % (self.client.uid, target, line))

    def notice(self, target, line):
        self.sendLine(":%s NOTICE %s :%s" % (self.client.uid, target, line))

    def join(self, channel, op=True):
        channel = self.channels[channel]

        self.sendLine(self.client.join(channel, op))

    def servicesLog(self, line):
        self.privmsg(self.config["etc"]["snoopchan"], line)

print "!!! Cod 0.1 starting up"
cod = Cod()

for line in cod.link.makefile('r'):
    line = line.strip()

    if cod.config["etc"]["debug"]:
        print "<<< %s" % line

    splitline = line.split()

    if line[0] != ":":
        if line.split()[0] == "PING":
            cod.sendLine("PONG %s" % splitline[1:][0])

            if not cod.bursted:
                cod.bursted = True

                for channel in cod.config["me"]["channels"]:
                    cod.join(channel)

    else:
        source = splitline[0][1:]

        try:
            for impl in commands[splitline[1]]:
                impl(cod, line, splitline, source)
        except KeyError as e:
            pass

