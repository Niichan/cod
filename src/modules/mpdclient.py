from mpd import MPDClient
from utils import *

mpd = MPDClient()

def initModule(cod):
    cod.log("Establishing connection to MPD server", "===")

    mpd.timeout = 10
    mpd.idletimeout = None
    mpd.connect(cod.config["mpd"]["host"], cod.config["mpd"]["port"])

    cod.log("done", "===")

    cod.botcommands["MPD"] = [commandMPD]

def destroyModule(cod):
    cod.log("Disconnecting from MPD server", "===")

    mpd.close()
    mpd.disconnect()

    del cod.botcommands["MPD"]

def commandMPD(cod, line, splitline, source, destination):
    if len(splitline) < 2:
        reply(cod, destination, source, "Not enough arguments")
        return

    if splitline[1].upper() == "FIND":
        query = " ".join(splitline[2:])

        reply(cod, destination, source, "Searching for %s" % query)

        results = mpd.find("any", query)

        client = cod.clients[source]

        for result in results:
            reply(cod, destination, source, "%s: %s -- %s" % \
                    (client.nick, result["artist"], result["title"]))
    elif splitline[1].upper() == "STATUS":
        mpd.update()
        cur = mpd.currentsong()

        reply(cod, destination, source, "%s -- %s -- %4.2f%%" % \
                (cur["artist"], cur["title"], float(cur["pos"])/float(cur["time"])))

