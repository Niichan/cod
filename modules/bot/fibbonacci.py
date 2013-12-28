#!/usr/bin/python

NAME="fibbonacci number generator"
DESC="Outputs fibbonacci numbers"

"""
Code taken from wikipedia
"""

def initModule(cod):
    cod.addBotCommand("FIB", fibCMD)

def destroyModule(cod):
    cod.delBotCommand("FIB")

def rehash():
    pass

def fibCMD(cod, line, splitline, source, destination):
    "Syntax: FIB <num> - outputs num'th fibbonacci number"

    if len(splitline) < 2:
        cod.reply(source, destination, "Syntax: FIB <num> - outputs num'th fibbonacci number")
        return

    num = int(splitline[1])

    cod.reply(source, destination, "%d: %d" % (num, smart_recur_fib(num)))

fibs = {}

def smart_recur_fib(x):
    global fibs

    if x not in fibs:
        if x <= 2:
            fibs[x] = 1;
        else:
            fibs[x] = smart_recur_fib(x-1) + smart_recur_fib(x-2)
    return fibs[x]

