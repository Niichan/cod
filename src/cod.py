#!/usr/bin/python

"""
Copyright (c) 2013, Sam Dodrill
All rights reserved.

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

    1. The origin of this software must not be misrepresented; you must not
    claim that you wrote the original software. If you use this software
    in a product, an acknowledgment in the product documentation would be
    appreciated but is not required.

    2. Altered source versions must be plainly marked as such, and must not be
    misrepresented as being the original software.

    3. This notice may not be removed or altered from any source
    distribution.
"""

VERSION = "0.1"

from niilib import config
from niilib import log
from niilib.message import IRCMessage
from niilib.b36 import *
from select import select

import socket
import os
import sys
import ssl
import gc
import sqlite3 as lite

from structures import *
from utils import *


class Cod():

    def __init__(self, configpath):
        """
        The main Cod class. This holds all the data structures needed
        for Cod to function. The socket, command tables, server data,
        client tables, and other variables needed for Cod to work
        properly are initialized here.
        """
        self.version = VERSION

        self.link = socket.socket()

        self.clients = {}
        self.channels = {}
        self.servers = {}
        self.modules = {}

        self.socks = [self.link]
        self.sockhandlers = {self.link: self.process}

        self.lastid = 60466176 # 100000 in base 36

        self.loginFunc = None

        self.s2scommands = {"PRIVMSG": []}
        self.botcommands = {}
        self.opercommands = {}

        self.bursted = False
        self.db = None
        self.sid = ""

        #Load config file
        self.config = config.Config(configpath).config

        #logger instance
        self.logger = log.Logger(self.config["etc"]["logfile"])

        #Fork to background if needed
        if self.config["etc"]["production"]:
            self.log("Forking to background")

            try:
                pid = os.fork()
            except OSError, e:
                raise Exception, "%s [%d]" % (e.strerror, e.errno)

            if (pid == 0):
                os.setsid()
            else:
                os._exit(0)

        if self.config["uplink"]["ssl"]:
            self.link = ssl.wrap_socket(self.link)
            self.log("SSL enabled")

        #pid value
        self.pid = os.getpid()

        self.log("Initializing Database")

        self.db = lite.connect(self.config["me"]["dbpath"])
        cur = self.db.cursor()

        try:
            cur.execute("PRAGMA table_info(Thistabledoesnotexist);")
            rows = cur.fetchall()

        except lite.DatabaseError as e:
            self.log("Database at %s unreadable" %
                    self.config["me"]["dbpath"], "!!!")
            print e
            sys.exit(-1)

        self.log("done")

        self.log("Establishing connection to uplink")

        self.link.connect((self.config["uplink"]["host"],
            self.config["uplink"]["port"]))

        self.log("done")

        self.sid = self.getSID()

        self.log("SID is %s" % self.sid)

        self.log("Loading %s protocol module" %
                self.config["uplink"]["protocol"])

        self.loadmod(self.config["uplink"]["protocol"])

        self.log("Sending credentials to remote IRC server")

        self.loginFunc(self)

        self.log("done")
        self.log("Creating and bursting client")

        self.client = makeService(self.config["me"]["nick"],
                self.config["me"]["user"], self.config["me"]["host"],
                self.config["me"]["desc"], self.getUID())

        self.clients[self.client.uid] = self.client

        self.burstClient(self, self.client.nick, self.client.user,
                self.client.host, self.client.gecos, self.client.uid)

        self.log("done")

        #Inform operators that Cod is initialized
        self.log("Cod initialized", "!!!")

    def getUID(self, sid=None):
        """
        Returns a valid, unique TS6 UID for use with services clients
        """

        if sid == None:
            sid = self.sid

        ret = self.lastid
        self.lastid = self.lastid + 1

        return sid + base36encode(ret)

    def getSID(self, string=None):
        """
        Returns a server ID number based on the string provided, default is
        the configured server name and description, much like how inpsircd
        does SID generation.
        """

        if string is None:
            string = self.config["me"]["name"] + self.config["me"]["desc"]

        hashval = 1
        for char in string:
            char = ord(char)
            hashval = hashval * (char * (char + 1))

        return str(hashval)[:3]

    def loadmod(self, modname):
        """
        Input: module name

        This function tries to load a module and initialize its commands to
        the bot or s2s command tables. This function does no error checking and
        it is up to functions calling this to do so.
        """

        if modname in self.modules:
            return

        oldpath = list(sys.path)
        sys.path.insert(0, "modules/")
        sys.path.insert(1, "modules/protocol")
        sys.path.insert(2, "modules/core")
        sys.path.insert(3, "modules/experimental")
        sys.path.insert(4, "modules/bot")
        sys.path.insert(5, "modules/services")
        sys.path.insert(6, "modules/announcer")
        sys.path.insert(7, "modules/scrapers")

        self.modules[modname] = __import__(modname)
        self.modules[modname].initModule(self)
        self.log("Module %s loaded" % modname)

        sys.path[:] = oldpath

    def unloadmod(self, modname):
        """
        Input: module name

        This function tries to unload a module and destroy its commands to the
        bot or s2s command tables as makes sense. This function does not error
        checking and it is up to functions calling this to do so.
        """

        self.modules[modname].destroyModule(self)
        del self.modules[modname]
        del sys.modules[modname]

        #Run the garbage collector
        gc.collect()

        self.log("Module %s unloaded" % modname)

    def addBotCommand(self, command, func, oper=False):
        """
        Adds a botcommand to the bot commands table, optionally adding it
        to the special table full of oper-only commands.
        """

        wheretoadd = self.botcommands

        if oper:
            wheretoadd = self.opercommands

        wheretoadd[command] = [func]

    def delBotCommand(self, command):
        """
        Removes a bot command from the oper-only and normal user level bot commands
        tables if applicable
        """

        try:
            del self.botcommands[command]
        except KeyError:
            del self.opercommands[command]

    def rehash(self):
        """
        Input: none

        This function rehashes the configuration in memory with the
        configuration on the disk.
        """
        self.log("Rehashing...")

        self.config = config.Config("config.json").config

        for module in self.modules:
            cod.log("Rehashing %s" % module, "===")
            try:
                self.modules[module].rehash()
            except:
                pass

        self.log("Rehash complete")

    def sendLine(self, line):
        """
        Input: line to send to ircd

        This function will send a line to the upstream ircd. This does no
        checking and will print the line if the program is in debug mode.
        """
        if self.config["etc"]["debug"]:
            self.log(line, ">>>")

        # Check for \r\n in message, closes issue #17
        if "\r" in line:
            "".join(line.split("\r"))

        if "\n" in line:
            "".join(line.split("\n"))

        self.link.send("%s\r\n" % line)

    def privmsg(self, target, line, source=None):
        """
        Input: target of message (UID or channel), message to send, source of
        message (default Cod's main client UID)

        A nice macro around PRIVMSG for convenience. Allows for changing the
        source of the message.
        """

        if source is None:
            source = self.client

        self.sendLine(":%s PRIVMSG %s :%s" % (self.client.uid, target, line))

    def notice(self, target, line, source=None):
        """
        Input: target of message (UID or channel), message to send, source of
        message (default Cod's main client UID)

        A nice macro around NOTICE for convenience.Allows for changing the
        source of the message.
        """

        if source is None:
            source = self.client

        self.sendLine(":%s NOTICE %s :%s" % (self.client.uid, target, line))

    def kill(self, target, source=None, message="Connection has been terminated."):
        """
        Wrapper function to kill off clients and remove their client data
        """

        if source is None:
            source = self.client

        self.sendLine(":%s KILL %s :spacing %s" % (source.uid,
            target.uid, message))

        self.clients.pop(target.uid)

    def join(self, channel, client=None):
        """
        Input: channel to join, client to join to the channel (default Cod
        internal client)

        This is a convenience macro around SJOIN (which requires a matching TS)
        to join a channel. Will also let you join another client Cod controls to
        a channel. Also lets you set channel op on join.
        """

        if client is None:
            client = self.client

        if channel not in self.channels:
            self.channels[channel] = Channel(channel, int(time.time()))

        channel = self.channels[channel]

        self.sendLine(client.join(channel))

        client.channels.append(channel.name)

    def part(self, channel, message, client=None):
        """
        Input: channel to part, client to part from the channel (default Cod
        internal client), part message
        """

        if client is None:
            client = self.client

        self.sendLine(":%s PART %s :%s" % (client.uid, channel, message))

        idx = client.channels.index(channel)
        client.channels.pop(idx)

    def snote(self, line, mask="d"):
        """
        Inputs: line to send, target server notice mask

        This function lets you send out a global server notice matching an
        arbitrary SNOMASK, but the default is the debug SNOMASK.
        """
        self.sendLine(":%s ENCAP * SNOTE %s :%s" % \
                (self.sid, mask, line))

    def log(self, message, prefix="---"):
        """
        Inputs: message to log, prefix to prepend to message (default "---")

        This function prints a message to the screen unless we are forked to
        the background (not checking that messes things up). If the prefix is
        the default prefix, it will also send out a debug snote with the log
        message.
        """
        if not self.config["etc"]["production"]:
            print prefix, message

        if self.bursted and prefix == "!!!":
            self.snote("%s" % (message))

        self.logger.log("%s %s" % (prefix, message))

    def servicesLog(self, line, client=None):
        """
        Inputs: line to log to services snoop channel

        This is a convenience function to send a message to the services logging
        channel. This channel is configurable in the config file.
        """

        if client is None:
            client = self.client

        self.privmsg(self.config["etc"]["snoopchan"], line, client)

        self.logger.log("SVS: %s: %s" % (client.nick, line))

    def findClientByNick(self, nick):
        """
        Inputs: nickname to find client data structure of

        This searches the Cod client table for a client matching a nick. If
        no matching client is found, None will be returned.
        """
        nick = nick.lower()

        for client in self.clients:
            if cod.clients[client].nick.lower() == nick:
                return cod.clients[client]

        return None

    def reply(self, source, destination, line):
        """
        Inputs: source of message, destination of message, line to send

        According to the IRC RFC's, bots should use NOTICE to reply to private
        messages and PRIVMSG to reply to channel messages. This simplifies
        functions returning data to clients over PRIVMSG/NOTICE to call one
        function instead of choosing between two.
        """
        if source == destination:
            #PM
            cod.notice(destination, line)
        else:
            #Channel message
            cod.privmsg(destination, line)

    def go(self):
        """
        Cod's main function
        """

        self.buf = ""

        while True:
            try:
                inputready, outputready, execeptready = select(self.socks,[],[])

                for s in inputready:
                    self.sockhandlers[s]([cod, s])
            except KeyboardInterrupt:
                print " <-- Control-C pressed, dying"
                self.servicesLog("DIE: KEYBOARD")

                self.db.close()
                self.sendLine(self.client.quit())

                for module in self.modules:
                    if module == "elemental-ircd":
                        continue
                    elif module == "admin":
                        continue
                    try:
                        self.modules[module].destroyModule(self)
                    except Exception:
                        print "Lol can't unload %s" % module

                self.sendLine("SQUIT :Killed.")

                os.system("killall %d" % self.pid)

                sys.exit()


        self.log("Oh, I am slain.")

    def process(self, args):
        tbuf = self.link.recv(2048)
        tbuf = self.buf + tbuf

        lines = tbuf.split("\r\n")

        self.buf = lines[-1]
        lines = lines[:-1]

        self.processLines(lines)

    def processLines(self, lines):
        """
        This checks and does all the module call handlers for lines from the
        upstream socket.
        """

        for line in lines:
            lineobj = IRCMessage(line)

            #debug output
            if self.config["etc"]["debug"]:
                self.log(line, "<<<")

            splitline = line.split()

            #Ping handler.
            if lineobj.source == None:
                if lineobj.verb == "PING":
                    self.sendLine("PONG %s" % splitline[1:][0])

                    if not self.bursted:
                        #Join staff and snoop channels
                        self.join(self.config["etc"]["staffchan"])
                        self.join(self.config["etc"]["snoopchan"])
                        cod.privmsg("NickServ", "IDENTIFY %s" % cod.config["me"]["servicespass"])

                        #Load admin module
                        self.loadmod("admin") #Required to be hard-coded

                        self.bursted = True
                    continue

            #Handle server commands
            try:
                for impl in self.s2scommands[lineobj.verb]:
                    try:
                        impl(cod, lineobj)
                    except Exception as e:
                        continue
            except KeyError:
                pass

if __name__ == "__main__":
    print "!!! Cod %s starting up" % VERSION

    cod = None

    if len(sys.argv) < 2:
        cod = Cod("config.json")
    else:
        cod = Cod(sys.argv[1])

    #start up

    cod.go()

