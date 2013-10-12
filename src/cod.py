#!/usr/bin/python

VERSION = "0.6"

import config
import socket
import os
import sys
import gc
import sqlite3 as lite

from structures import *
from mpd import MPDClient

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

        self.s2scommands = {"PRIVMSG": []}
        self.botcommands = {}

        self.bursted = False
        self.db = None

        #Load config file
        self.config = config.Config(configpath).config

        #Fork to background if needed
        if self.config["etc"]["production"]:
            print "--- Forking to background"

            try:
                pid = os.fork()
            except OSError, e:
                raise Exception, "%s [%d]" % (e.strerror, e.errno)

            if (hasattr(os, "devnull")):
                REDIRECT_TO = os.devnull
            else:
                REDIRECT_TO = "/dev/null"

            if (pid == 0):
                os.setsid()
            else:
                os._exit(0)

        self.log("Initializing Database")

        self.db = lite.connect(self.config["me"]["dbpath"])
        cur = self.db.cursor()

        try:
            cur.execute("PRAGMA table_info(Thistabledoesnotexist);")
            rows = cur.fetchall()

        except lite.DatabaseError as e:
            self.log("Database at %s unreadable" % self.config["me"]["dbpath"], "!!!")
            print e
            sys.exit(-1)

        self.log("done")

        self.log("Loading core module")

        self.loadmod("s2scommands", False)

        self.log("done")

        self.log("Establishing connection to uplink")

        self.link.connect((self.config["uplink"]["host"], self.config["uplink"]["port"]))

        self.log("done")

        self.log("Sending credentials to remote IRC server")

        self.sendLine("PASS %s TS 6 :%s" %
                (self.config["uplink"]["pass"], self.config["uplink"]["sid"]))
        self.sendLine("CAPAB :QS EX IE KLN UNKLN ENCAP SERVICES EUID EOPMOD")
        self.sendLine("SERVER %s 1 :%s" %
                (self.config["me"]["name"], self.config["me"]["desc"]))

        self.log("done")
        self.log("Creating and bursting client")

        self.client = makeService(self.config["me"]["nick"],
                self.config["me"]["user"], self.config["me"]["host"],
                self.config["me"]["desc"], self.config["uplink"]["sid"] + "CODFIS")

        self.clients[self.config["uplink"]["sid"] + "CODFIS"] = self.client

        self.sendLine(self.client.burst())

        self.log("done")

        #Inform operators that Cod is initialized
        self.snote("Cod initialized", "s")
        self.log("Cod initialized", "!!!")

    def loadmod(self, modname, commit=True):
        """
        Input: module name, whether or not to commit this module to the database

        This function tries to load a module and initialize its commands to
        the bot or s2s command tables. This function does no error checking and
        it is up to functions calling this to do so. Commits module loads to the
        database.
        """

        if commit:
            cur = self.db.cursor()
            cur.execute("INSERT INTO Moduleautoload(Name) VALUES ('%s');" % modname)

            self.db.commit()

        oldpath = list(sys.path)
        sys.path.insert(0, "modules/")

        self.modules[modname] = __import__(modname)
        self.modules[modname].initModule(self)

        if self.bursted:
            self.log("Module %s loaded" % modname)

        sys.path[:] = oldpath

    def unloadmod(self, modname):
        """
        Input: module name

        This function tries to unload a module and destroy its commands to the
        bot or s2s command tables as makes sense. This function does not error
        checking and it is up to functions calling this to do so. Commits module
        unloads to the database.
        """

        cur = self.db.cursor()
        cur.execute("DELETE FROM Moduleautoload WHERE Name = \"%s\";" % modname)

        self.log("Trying to unload module %s" % modname)

        self.modules[modname].destroyModule(self)
        del self.modules[modname]
        del sys.modules[modname]

        #Run the garbage collector
        gc.collect()

        self.log("Module %s unloaded" % modname)

    def rehash(self):
        """
        Input: none

        This function rehashes the configuration in memory with the configuration
        on the disk. It also parts from any extra channels the bot may have
        joined while running.
        """
        self.log("Rehashing...")

        self.config = config.Config("config.json").config

        self.sendLine(self.client.quit())
        self.sendLine(self.client.burst())

        for channel in cod.config["me"]["channels"]:
            cod.join(channel, False)

        self.log("Rehash complete")

    def sendLine(self, line):
        """
        Input: line to send to ircd

        This function will send a line to the upstream ircd. This does no
        checking and will print the line if the program is in debug mode.
        """
        if self.config["etc"]["debug"]:
            self.log(line, ">>>")

        self.link.send("%s\r\n" % line)

    def privmsg(self, target, line, source=None):
        """
        Input: target of message (UID or channel), message to send, source of
        message (default Cod's main client UID)

        A nice macro around PRIVMSG for convenience. Allows for changing the
        source of the message.
        """

        if source == None:
            source = self.client

        self.sendLine(":%s PRIVMSG %s :%s" % (self.client.uid, target, line))

    def notice(self, target, line, source=None):
        """
        Input: target of message (UID or channel), message to send, source of
        message (default Cod's main client UID)

        A nice macro around NOTICE for convenience.Allows for changing the
        source of the message.
        """

        if source == None:
            source = self.client

        self.sendLine(":%s NOTICE %s :%s" % (self.client.uid, target, line))

    def join(self, channel, client=None, op=False):
        """
        Input: channel to join, client to join to the channel (default Cod
        internal client), whether or not the server will set channel op
        status (default off)

        This is a convenience macro around SJOIN (which requires a matching TS)
        to join a channel. Will also let you join another client Cod controls to
        a channel. Also lets you set channel op on join.
        """

        if client == None:
            client = self.client

        channel = self.channels[channel]

        self.sendLine(self.client.join(channel, op))

    def part(self, channel, message, client=None):
        """
        Input: channel to part, client to part from the channel (default Cod
        internal client), part message
        """

        if client == None:
            client = self.client

        self.sendLine(":%s PART %s :%s" % (client.uid, channel, message))

    def snote(self, line, mask="d"):
        """
        Inputs: line to send, target server notice mask

        This function lets you send out a global server notice matching an
        arbitrary SNOMASK, but the default is the debug SNOMASK.
        """
        self.sendLine(":%s ENCAP * SNOTE %s :%s" % \
                (self.config["uplink"]["sid"], mask, line))

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

        if self.bursted and prefix == "---":
            self.snote("%s" % (message))

    def servicesLog(self, line):
        """
        Inputs: line to log to services snoop channel

        This is a convenience function to send a message to the services logging
        channel. This channel is configurable in the config file.
        """
        self.privmsg(self.config["etc"]["snoopchan"], line)

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

print "!!! Cod %s starting up" % VERSION

#XXX: maybe take this as a command line parameter?
cod = Cod("config.json")

#start up

#Read lines from the server
for line in cod.link.makefile('r'):
    #Strip \r\n
    line = line.strip()

    #debug output
    if cod.config["etc"]["debug"]:
        cod.log(line, "<<<")

    splitline = line.split()

    #Ping handler.
    if line[0] != ":":
        if line.split()[0] == "PING":
            cod.sendLine("PONG %s" % splitline[1:][0])

            if not cod.bursted:
                #Join staff and snoop channels
                cod.join(cod.config["etc"]["staffchan"])
                cod.join(cod.config["etc"]["snoopchan"])

                #Load remainder of modules
                cod.loadmod("admin", False) #Required to be hard-coded

                cur = cod.db.cursor()

                cur.execute("PRAGMA table_info(Moduleautoload);")
                pragma = cur.fetchall()

                if pragma == []:
                    cur.execute("CREATE TABLE Moduleautoload(Id INTEGER PRIMARY KEY, Name TEXT);")
                    cod.log ("Created module database table")

                cur.execute("SELECT * FROM Moduleautoload;")

                cod.db.commit()

                rows = cur.fetchall()

                if rows != []:
                    for row in rows:
                        cod.loadmod(row[1], False)

                cod.bursted = True

    #Handle server commands
    else:
        source = splitline[0][1:]

        try:
            for impl in cod.s2scommands[splitline[1]]:
                impl(cod, line, splitline, source)
        except KeyError as e:
            pass

