"""
Copyright (c) 2014, Sam Dodrill
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

import requests

from bs4 import BeautifulSoup
from time import time

NAME="SC2 name"
DESC="Grabs nicknames from the starcraft koreanizer"

def initModule(cod):
    cod.addBotCommand("SC2NAME", commandSC2NAME)

def destroyModule(cod):
    cod.delBotCommand("SC2NAME")

def getSC2Name():
    r = requests.get("http://oldmanclub.org/sc2/")
    soup = BeautifulSoup(r.text)

    name = soup("h2")[0].text

    return name

def commandSC2NAME(cod, line, splitline, source, destination):
    nick = getSC2Name()
    cod.reply(source, destination, "Your name should be %s" % nick)
    if cod.config["etc"]["production"] == False:
        cod.sendLine(":%s ENCAP * RSFNC %s %s %d %s" % (cod.sid, source, nick,
            int(time()), source.ts))
        source.ts = int(time())

