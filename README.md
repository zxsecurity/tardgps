#tardgps
tardgps is a tool which will move the boardcase time of GPS backwards to a preset time in the configuration file. This will be a conference talk at [Kiwicon 2016](https://kiwicon.org/the-con/talks/#e225).

##Requirements
1. A GPS Device that will talk to [GPSd](http://www.catb.org/gpsd/)
1. GPSd installed
1. Python
1. Python library [gps3](https://pypi.python.org/pypi/gps3/)
1. A copy of [bladeGPS](https://github.com/osqzss/bladeGPS), I have been using the [keith-citrenbaum fork](https://github.com/keith-citrenbaum/bladeGPS)

##Running
1. Configure the options in tardgps.cfg
1. Run gpsd `sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock`
1. Run tardgps `./tardgps.py`