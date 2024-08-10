# Driver for ds3231 with utc

## Use-case

In some situations, a precision RTC like the DS3221 is the better option to provide real-time-clock information with battery backup. The excisting drivers for micropython are doing the job well but could be extended with some features e.g. to handle UTC (daylight saving, +1, +2), remote time adjustment and why not TCXO temperature readout.

## ds3231_radmo3.py

This driver is based upon the work of Peter Hinch, extended with features as:

- get_time(YY, MM, DD, hh, mm, ss, wday, yday)
- set_utc(1, 2)
- get_utc() 
- set_time(+h, +m, +s)
- get_tcxo_temp()
- get_code()

# get_time()

This command returns as an extra: weekday and day in the year. 

# set_utc()

When set-forward (UTC+1 > +2) and set-back (UTC+2 > +1) are implemented based on arrays, containing the day to switch to +2 and back to +1, this is not only fast in execution but then it is important to know the 3231 RTC state after a power-down. This feature is provided with set_utc() and get_utc(). This info is saved in unused RTC alarm registers, the argument has a range check. The
set_utc() command is location independent since it's in fact just a way to memorize the RTC UTC state.

# set_time()

Applications are more than ever wifi and broker connected. Even though 3231 is a precision RTC, now and then the time needs te be corrected. This is also the case for UTC change.
Set_time(h, m, s) can increase(+) or decrease(-) h, m and s settings individually with a value set in the argument of set_time.
e.g. set_time(+1,0,0) will set the hour 1 unit forward
e.g. set_time(0,0, -5) will adjust the seconds -5 units backwards.
The arguments have a range check.

# get_tcxo_temp()

Returns the tcxo temp, usually in the order of 32°C. This feature allows to supervice the stability of the 3231 RTC.

# get_code()

As a general practice, i always put in line 1 the reserved variable named code='ds3231_radmo3.py'. Also in this driver. The command get_code() returns this variable as a general means to verify if the right driver is used.
