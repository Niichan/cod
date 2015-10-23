Cod
===

Extended IRC services in Python

[![Bitdeli Badge](https://d2weczhvl823v0.cloudfront.net/lyska/cod/trend.png)](https://bitdeli.com/free "Bitdeli Badge") [![Ohloh badge](https://www.ohloh.net/p/cod-services/widgets/project_thin_badge.gif)](https://www.ohloh.net/p/cod-services "Ohloh Badge")

This project is deprecated in favor of its replacement [Tetra](https://github.com/Xe/Tetra).

Installation directions are in `doc/INSTALL.markdown`. Directions for setting
up Atheme integration are in `doc/funserv.markdown`. IRCd-specific directions 
are in `doc/IRCD.markdown`. This project is under the terms of the zlib 
license, a copy of this license is included at `doc/LICENSE.markdown`. Some 
files in this project are **not** under the terms of this license and are 
licensed per file as appropriate.

### Features:
 - Asynchronous I/O
   (and an easy way for modules to add socket handlers)
 - Forking to background
 - Logging to snoop channel
 - Modular loading and unloading
 - No specific libc dependency (tested on glibc, uclibc and musl)
 - Rehashing config file
 - Separation of user and oper commands
 - SQLite database
 - SpanningTree/TS6 link protocol support
   - Charybdis 3.4.2 +
   - Elemental-IRCd 6.5 +
   - Tethys 0.1 +
 - Virtual environment support

The official channel for Cod is `#cod` on `irc.yolo-swag.com`. Come take
a visit and say hi! Anyone with halfop (`%`) or higher has direct push access 
and the live instance is called `ShadowNET`.

