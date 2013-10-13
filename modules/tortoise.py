import requests
from structures import *
from utils import *

NAME="Tortoise Labs interface"
DESC="Interface to tortoise labs API"

"""
Prints DNS pool information when your pool is set up on Tortoise Labs.
"""

global client

def initModule(cod):
    global client

    client = makeService(cod.config["dns"]["nick"], cod.config["dns"]["user"],
            cod.config["dns"]["host"], cod.config["dns"]["gecos"],
            cod.config["uplink"]["sid"] + "DNSSRV")

    cod.s2scommands["PRIVMSG"].append(handleMessages)

    cod.clients[client.uid] = client

    cod.sendLine(client.burst())

    cod.sendLine(client.join(cod.channels[cod.config["etc"]["snoopchan"]]))
    cod.sendLine(client.join(cod.channels[cod.config["etc"]["staffchan"]]))

def destroyModule(cod):
    global client

    idx = cod.s2scommands["PRIVMSG"].index(handleMessages)
    cod.s2scommands["PRIVMSG"].pop(idx)

    cod.sendLine(client.quit())

    cod.clients.pop(client.uid)

def handleMessages(cod, line, splitline, source):
    global client

    if splitline[2] != client.uid:
        return

    line = ":".join(line.split(":")[2:])
    splitline = line.split()

    if splitline[0].upper() == "POOL":
        if failIfNotOper(cod, client, cod.clients[source]):
            return

        auth = (cod.config["tortoiselabs"]["username"],
                cod.config["tortoiselabs"]["apikey"])

        request = requests.get("http://manage.tortois.es/dns/zones", auth=auth)

        for line in request.json["zones"]:
            if line["name"] == cod.config["dns"]["name"]:
                for record in line["records"]:
                    if record["name"] == cod.config["dns"]["pool"]:
                        cod.sendLine(client.privmsg(source, record["content"]))
                cod.sendLine(client.privmsg(source, "End of pool %s" % cod.config["dns"]["pool"]))

    else:
        cod.sendLine(client.notice(source, "Valid commands are:"))
        cod.sendLine(client.notice(source, " - POOL: Show DNS pool"))
