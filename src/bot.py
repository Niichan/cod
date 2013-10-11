from structures import *
from botcommands import *

commands = {}

def relayHostServToOpers(cod, line, splitline, source):
    if splitline[2] == "#services":
        if cod.clients[source].nick == "HostServ":
            cod.sendLine(cod.client.privmsg(cod.config["etc"]["staffchan"],
                "HostServ: " + " ".join (splitline[3:])[1:]))

def prettyPrintMessages(cod, line, splitline, source):
    if not self.config["etc"]["production"]:
        client = cod.clients[source]

        print "{0}: <{1}> {2}".format(splitline[2], client.nick, " ".join (splitline[3:])[1:])

def handlePRIVMSG(cod, line, splitline, source):
    destination = splitline[2]
    line = ":".join(line.split(":")[2:])
    splitline = line.split()

    command = ""
    pm = True

    if destination[0] == "#":
        if line[0] == cod.config["me"]["prefix"]:
            command = splitline[0].upper()
            command = command[1:]
            pm = False
    else:
        command = command = splitline[0].upper()

    try:
        for impl in commands[command]:
            if pm:
                impl(cod, line, splitline, source, source)
            else:
                impl(cod, line, splitline, source, destination)

    except KeyError as e:
        pass

commands["TEST"] = [commandTEST]
commands["JOIN"] = [commandJOIN]
commands["RBL"] = [commandRBL]
commands["MPD"] = [commandMPD]
commands["OPNAME"] = [commandOPNAMEinit, commandOPNAME]
commands["REHASH"] = [commandREHASH]
commands["DIE"] = [commandDIE]

