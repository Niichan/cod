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

NAME="Help command"
DESC="Lol, as if there's help yet."

def initModule(cod):
    cod.botcommands["HELP"] = [commandHELP]

def destroyModule(cod):
    del cod.botcommands["HELP"]

def rehash():
    pass

def commandHELP(cod, line, splitline, source, destination):
    commandlist = " ".join(cod.botcommands)
    opercmdlist = " ".join(cod.opercmds)

    if cod.clients[source].isOper:
        commandlist += " (%s)" % opercmdlist

    cod.reply(source, destination, "Commands: %s" % commandlist)

