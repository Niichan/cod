from structures import *
import rblwatch

def commandRBL(cod, line, splitline, source, destination):
    if failIfNotOper(cod, cod.clients[source]):
        return

    if destination != cod.config["etc"]["snoopchan"]:
        cod.notice(source, "Command may not be used outside %s" % cod.config["etc"]["snoopchan"])
        return

    search = None
    target = splitline[1]

    if splitline[1].find(".") == -1:
        #If we don't have an IP address, we have a nick of a client
        mark = None

        for client in cod.clients:
            if cod.clients[client].nick == target:
                mark = client
                break

        if mark == None:
            cod.notice(source, "%s is not on IRC" % target)

        mark = cod.clients[mark]

        if mark.ip == "0":
            cod.notice(source, "Target is a network service")
            return

        cod.servicesLog("RBL: %s: %s" % (target, cod.clients[source].nick))

        search = rblwatch.RBLSearch(cod, mark.ip)

    else:
        cod.servicesLog("RBL: %s: %s" % (target, cod.clients[source].nick))

        search = rblwatch.RBLSearch(cod, target)

    search.print_results()

