#
# Copyright (c) 2009 William Pitcock <nenolod@atheme.org>.
#
# This file is licensed under the Atheme license.
#

import time

from xmlrpclib import ServerProxy, Fault

class AthemeNickServMethods(object):
    """
    Parse Atheme NickServ responses.  Since the XML interface provides the same output as the IRC interface, we
    have to do this.  It"s kind of a pain in the ass.
    """
    def __init__(self, parent):
        self.parent = parent
        self.flags = ["Hold", "HideMail", "NeverOp", "NoOp", "NoMemo",
                "EMailMemos", "Private"]

    def _parse_access(self, data):
        raw_lines = data.split("\n")

        list = []
        for line in raw_lines:
            fields = line.split(" ")

            if fields[0] != "Access":
                continue
            try:
                tuple = {"channel": fields[4], "flags": fields[2]}
            except:
                pass
            list.append(tuple)

        return list

    def list_own_access(self):
        return self._parse_access(self.parent.atheme.command(self.parent.authcookie,
            self.parent.username, self.parent.ipaddr, "NickServ", "LISTCHANS"))

    def list_access(self, target):
        return self._parse_access(self.parent.atheme.command(self.parent.authcookie,
            self.parent.username, self.parent.ipaddr, "NickServ", "LISTCHANS",
            target))

    def get_info(self, target):
        data = self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "NickServ", "INFO", target)
        raw_lines = data.split("\n")

        tuple = {}
        for line in raw_lines:
            if "Information on" in line:
                continue
            if ":" not in line:
                continue

            fields = line.split(":", 1)
            try:
                tuple[fields[0].strip()] = fields[1].strip()
            except:
                pass

        return tuple

    def get_account_flags(self, target):
        data = self.get_info(target)
        flags = data["Flags"]

        tuple = {}
        for flag in self.flags:
            if flag in flags:
                tuple[flag] = True
            else:
                tuple[flag] = False

        return tuple

    def set_password(self, password):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "NickServ", "SET", "PASSWORD", password)

    def set_email(self, email):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "NickServ", "SET", "EMAIL", email)

class AthemeChanServMethods(object):
    """
    Parse Atheme ChanServ responses.  Since the XML interface provides the same output as the IRC interface, we
    have to do this.  It"s kind of a pain in the ass.
    """
    def __init__(self, parent):
        self.parent = parent
        self.flags = ["HOLD", "SECURE", "VERBOSE", "VERBOSE_OPS", "RESTRICTED",
                "KEEPTOPIC", "TOPICLOCK", "GUARD", "FANTASY", "PRIVATE",
                "LIMITFLAGS"]

    def kick(self, channel, victim, reason):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "ChanServ", "KICK", channel, victim, reason)

    def get_access_list(self, channel):
        data = self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "ChanServ", "FLAGS",
                channel)
        raw_lines = data.split("\n")

        list = []
        for line in raw_lines:
            tuple = {}

            try:
                data = line.split(None, 3)
                tuple["id"] = int(data[0])
                tuple["nick"] = data[1]
                tuple["flags"] = data[2]
                list.append(tuple)
            except ValueError:
                continue

        return list

    def get_access_flags(self, channel, nick):
        return self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "ChanServ", "FLAGS",
                channel, nick)

    def set_access_flags(self, channel, nick, flags):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "ChanServ", "FLAGS", channel,
                nick, "=" + flags)

    def get_channel_info(self, channel):
        data = self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "ChanServ", "INFO",
                channel)
        raw_lines = data.split("\n")

        tuple = {}
        for line in raw_lines:
            if line[0] == "*" or "Information on" in line:
                continue

            fields = line.split(" : ", 2)
            try:
                tuple[fields[0].strip()] = fields[1].strip()
            except:
                pass
        return tuple

    def get_channel_flags(self, channel):
        data = self.get_channel_info(channel)
        flags = data["Flags"]

        tuple = {}
        for flag in self.flags:
            if flag in flags:
                tuple[flag] = True
            else:
                tuple[flag] = False

        return tuple

    def set_channel_flag(self, channel, flag, value):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "ChanServ", "SET", channel, flag, value)

class AthemeMemoServMethods(object):
    """
    Parse Atheme MemoServ responses.  Since the XML interface provides the same output as the IRC interface, we
    have to do this.  It"s kind of a pain in the ass.
    """
    def __init__(self, parent):
        self.parent = parent

    def list(self):
        list = []

        data = self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "MemoServ", "LIST")
        raw_lines = data.split("\n")

        for line in raw_lines:
            if line[0] != "-":
                continue

            data = line.split(" ", 5)
            tuple = {"from": data[3], "sent": data[5]}

            list.append(tuple)

        return list

    def read(self, number):
        data = self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "MemoServ", "READ",
                number)
        raw_lines = data.split("\n")

        fields = raw_lines[0].split(" ", 6)
        tuple = {"from": fields[5][0:-1], "sent": fields[6], "message": raw_lines[2]}

        return tuple

    def send(self, target, message):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "MemoServ", "SEND", target, message)

    def send_ops(self, target, message):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "MemoServ", "SENDOPS", target, message)

    def forward(self, target, message_id):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "MemoServ", "FORWARD", target, message_id)

    def delete(self, message_id):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "MemoServ", "DELETE", message_id)

    def ignore_add(self, target):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "MemoServ", "IGNORE", "ADD", target)

    def ignore_delete(self, target):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "MemoServ", "IGNORE", "DEL", target)

    def ignore_list(self):
        data = self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "MemoServ", "IGNORE",
                "LIST")
        raw_lines = data.split("\n")

        list = []
        for line in raw_lines:
            tuple = {}

            try:
                data = line.split(" ")
                tuple["id"] = int(data[0])
                tuple["account"] = data[2]
                list.append(tuple)
            except ValueError:
                continue

        return list

    def ignore_clear(self):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "MemoServ", "IGNORE", "CLEAR")

class AthemeOperServMethods(object):
    def __init__(self, parent):
        self.parent = parent

    def akill_add(self, mask, reason="Requested"):
        return self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "OperServ", "AKILL",
                "ADD", mask, reason)

    def akill_list(self):
        akills = self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "OperServ", "AKILL",
                "LIST", "FULL").split("\n")[1:-1]
        akillset = {}

        for i in akills:
            ak = i.split(" - ", 3)
            aki = {"num": int(ak[0].split(" ")[0].strip(":")),
                    "mask": ak[0].split(" ")[1],
                    "setter": ak[1].split(" ")[1],
                    "expiry": ak[2],
                    "reason": ak[3][1:-1]}
            akillset[aki["num"]] = aki

        return akillset

    def akill_del(self, num):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "OperServ", "AKILL", "DEL", num)

    def kill(self, target):
        return self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "OperServ", "KILL", target)

    def mode(self, modestring):
        return self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "OperServ", "MODE",
                modestring)

class AthemeHostServMethods(object):
    def __init__(self, parent):
        self.parent = parent

    def activate(self, account):
        self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "HostServ",
                "ACTIVATE", account)

    def listvhost(self, mask="*"):
        vhosts = self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "HostServ", "LISTVHOST",
                mask)

        reply = []

        for vhost in vhosts.split("\n")[:-1]:
            vhost = vhost.split()
            res = {}

            res["nick"] = vhost[1]
            res["vhost"] = vhost[2]

            reply.append(res)

        return reply

    def request(self, vhost):
        self.parent.atheme.command(self.parent.authcookie, self.parent.username,
                self.parent.ipaddr, "HostServ", "REQUEST", vhost)

    def reject(self, account, reason=None):
        if reason is not None:
            self.parent.atheme.command(self.parent.authcookie,
                    self.parent.username, self.parent.ipaddr, "HostServ",
                    "REJECT", account, reason)
        else:
            self.parent.atheme.command(self.parent.authcookie,
                    self.parent.username, self.parent.ipaddr, "HostServ",
                    "REJECT", account)

    def waiting(self):
        waitinglist = self.parent.atheme.command(self.parent.authcookie,
                self.parent.username, self.parent.ipaddr, "HostServ",
                "WAITING").split("\n")
        vhosts = []

        for line in waitinglist:
            nick = line.split("Nick:")[1].split(",")[0]
            vhost = line.split(", vhost:")[1].split(" (")[0]
            date = line.split(" (")[1].split(" - ")[1][:-1]

            vhosts.append({"nick": nick, "vhost": vhost, "date": date})

        return vhosts

class AthemeXMLConnection(object):
    def __init__(self, url, ipaddr="0.0.0.0"):
        self.proxy    = ServerProxy(url)
        self.chanserv = AthemeChanServMethods(self)
        self.memoserv = AthemeMemoServMethods(self)
        self.nickserv = AthemeNickServMethods(self)
        self.operserv = AthemeOperServMethods(self)
        self.hostserv = AthemeHostServMethods(self)
        self._privset = None
        self.ipaddr   = ipaddr

    def __getattr__(self, name):
        return self.proxy.__getattr__(name)

    def login(self, username, password):
        self.username = username
        self.authcookie = self.atheme.login(username, password)

    def logout(self):
        self.atheme.logout(self.authcookie, self.username)

    def get_privset(self):
        if self._privset is not None:
            return self._privset

        self._privset = self.atheme.privset(self.authcookie, self.username).split()
        return self._privset

    def has_privilege(self, priv):
        try:
            if self.get_privset().index(priv):
                return True
            else:
                return False
        except ValueError, e:
            return False

    def register(self, username, password, email):
        try:
            return self.atheme.command("*", "*", "*", "NickServ", "REGISTER",
                    username, password, email)
        except Fault, e:
            if e.faultString == "A user matching this account is already on IRC.":
                return "Error: " + e.faultString + "  If you are already connected to IRC using this nickname, please complete the registration procedure through IRC."

            return "Error: " + e.faultString

class CodAthemeConnector():
    def __init__(self, cod):
        self.cod = cod
        self.xmlrpc = cod.config["atheme"]["xmlrpc"]

        self.atheme = AthemeXMLConnection(self.xmlrpc)

        self.__login()

    def __getattr__(self, name):
        if time.time() > self.time + 900:
            self.__login()
        return getattr(self.atheme, name)

    def __login(self):
        self.atheme.login(self.cod.config["me"]["nick"],
                self.cod.config["me"]["servicespass"])
        self.time = time.time()

        self.cod.log("Logged into XMLRPC")

