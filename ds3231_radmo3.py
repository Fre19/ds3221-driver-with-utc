code='ds3231_radmo3.py'
'''
 Simplified driver based on ds3231_radmon.py & ds3231_port.py,
 portable driver for the DS3231 1ppm precison real time clock.
 Adapted from WiPy driver at https://github.com/scudderfish/uDS3231
 Copyright Peter Hinch 2018 Released under the MIT license.
 
 'ds3231_radmo2.py' driver:
 Extended by: Freddy Withagels to enable:
 yday, hh-mm-ss correction, tcxo temp, UTC status, get_code,
 yday is needed to handle UTC+1/+2 switch in application 'Radmon',
 the UTC status is saved into a free Alarm register of the ds3231,
 this status is managed by Radmon and is required to know if hr+1
 is required after a power down or if DS3231 has been set already to UTC.
 get_code is used to verify in Radmon if the correct ds3231 driver is used.
'''

import utime
import machine
import sys
DS3231_I2C_ADDR = 104 # decimal

def bcd2dec(bcd):
    return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))

def dec2bcd(dec):
    tens, units = divmod(dec, 10)
    return (tens << 4) + units

def tobytes(num):
    return num.to_bytes(1, 'little')

class DS3231():
    def __init__(self, i2c): # Class 'constructor'
        self.ds3231 = i2c    # self. is a variable within instance within class DS3231
        self.datetimebuf = bytearray(7)
        self.timebuf = bytearray(3)
        
        if DS3231_I2C_ADDR not in self.ds3231.scan():
            raise RuntimeError("DS3231 not found on I2C bus at %d" % DS3231_I2C_ADDR)

    def get_time(self): # Instance of the class DS3231
        self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.datetimebuf)
        
        data = self.datetimebuf
        ss = bcd2dec(data[0])
        mm = bcd2dec(data[1])
        if data[2] & 0x40:
            hh = bcd2dec(data[2] & 0x1f)
            if data[2] & 0x20:
                hh += 12
        else:
            hh = bcd2dec(data[2])
        wday = data[3]
        DD = bcd2dec(data[4])
        MM = bcd2dec(data[5] & 0x1f)
        YY = bcd2dec(data[6])
        if data[5] & 0x80:
            YY += 2000
        else:
            YY += 1900
         
        days = [0,31,28,31,30,31,30,31,31,30,31,30,31]
        if YY % 400 == 0:
            days[2] +=1
        elif YY % 4 == 0 and YY % 100 != 0:
            days[2] += 1
        for i in range (1, len(days)):
            days[i] += days[i-1]
        yday = days[MM - 1] + DD

        result = YY, MM, DD, hh, mm, ss, wday -1, yday     
        return result
    
    def save_utime2dsrtc(self): # new syntax save_
        (YY, MM, DD, hh, mm, ss, wday, yday) = utime.localtime()   
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 0, tobytes(dec2bcd(ss)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 1, tobytes(dec2bcd(mm)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 2, tobytes(dec2bcd(hh)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 3, tobytes(dec2bcd(wday + 1)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 4, tobytes(dec2bcd(DD)))
        if YY >= 2000:
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 5, tobytes(dec2bcd(MM) | 0b10000000))
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 6, tobytes(dec2bcd(YY-2000)))
        else:
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 5, tobytes(dec2bcd(MM)))
            self.ds3231.writeto_mem(DS3231_I2C_ADDR, 6, tobytes(dec2bcd(YY-1900)))

    # args: c_ss/mm to adjust ss/mm (+/-), c_hh to adjust daylight saving hh (+/-)
    def set_time(self, c_hh, c_mm, c_ss): # set hh m ss independent from utime!
        self.ds3231.readfrom_mem_into(DS3231_I2C_ADDR, 0, self.timebuf)
        data = self.timebuf
        ss = bcd2dec(data[0])
        ss += int(c_ss)
        ss = 0 if ss < 0 else ss
        ss = 59 if ss > 59 else ss
        mm = bcd2dec(data[1])
        mm += int(c_mm)
        mm = 0 if mm < 0 else mm
        mm = 59 if mm > 59 else mm        
        hh = bcd2dec(data[2])
        hh += int(c_hh)
        hh = 0 if hh < 0 else hh
        hh = 23 if hh > 23 else hh    
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 0, tobytes(dec2bcd(ss)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 1, tobytes(dec2bcd(mm)))
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 2, tobytes(dec2bcd(hh)))    
    
    def set_utc(self, utc):
        u = utc  # assignment first !       
        u = 1 if utc < 1 else u
        u = 2 if utc > 2 else u
        self.ds3231.writeto_mem(DS3231_I2C_ADDR, 0x07, tobytes(u))
        return u
    
    def get_utc(self):
        utc = self.ds3231.readfrom_mem(DS3231_I2C_ADDR, 0x07, 1)
        return int.from_bytes(utc, 'little')
    
    def get_tcxo_temp(self):   # = tcxo via temp registers, snipet 2
        t = self.ds3231.readfrom_mem(DS3231_I2C_ADDR, 0x11, 2)
        d = ((t[1] & 0xc0 ) >> 6 ) * 0.25
        s = (t[0] & 0x80 )
        sign = -1 if s else 1
        return ((t[0] & 0xff ) + d) * sign
    
    def get_code(self):
        return code
    