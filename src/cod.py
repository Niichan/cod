#!/usr/bin/python

import config
import socket
from structures import *
from commands import *
from bot import *

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
commands["PRIVMSG"] = [handlePRIVMSG, relayHostServToOpers, prettyPrintMessages]
commands["NOTICE"] = [handlePRIVMSG]

config = config.Config("../config.json").config

class Cod():
    def __init__(self, host, port, password, SID, name, realname):
        self.link = socket.socket()

        self.clients = {}
        self.channels = {}
        self.servers = {}

        self.bursted = False

        self.link.connect((host, port))

        self.sid = SID
        self.name = name
        self.realname = realname

        self.sendLine("PASS %s TS 6 :%s" % (password, SID))
        self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP TB SERVICES EUID EOPMOD MLOCK")
        self.sendLine("SERVER %s 1 :%s" % (name, realname))

        self.client = makeService(config["me"]["nick"], config["me"]["user"],
                config["me"]["host"], config["me"]["desc"], SID + "CODFIS")

        self.clients[SID + "CODFIS"] = self.client

        self.sendLine(self.client.burst())

        self.config = config

    def sendLine(self, line):
        print ">>> %s" % line
        self.link.send("%s\r\n" % line)

    def privmsg(self, target, line):
        self.sendLine(":%s PRIVMSG %s :%s" % (self.client.uid, target, line))

    def join(self, channel, op=True):
        channel = self.channels[channel]

        self.sendLine(self.client.join(channel, op))

    def servicesLog(self, line):
        self.privmsg("#services", line)

cod = Cod(config["uplink"]["host"], config["uplink"]["port"],
        config["uplink"]["pass"], config["uplink"]["sid"], config["me"]["name"],
        config["me"]["desc"])
SNOOPCHAN = "#services"

for line in cod.link.makefile('r'):
    line = line.strip()

    print "<<< " + line
    splitline = line.split()

    if line[0] != ":":
        if line.split()[0] == "PING":
            cod.sendLine("PONG %s" % splitline[1:][0])

            if not cod.bursted:
                cod.bursted = True

                for channel in config["me"]["channels"]:
                    cod.join(channel)

    else:
        source = splitline[0][1:]

        try:
            for impl in commands[splitline[1]]:
                impl(cod, line, splitline, source)
        except KeyError as e:
            continue

