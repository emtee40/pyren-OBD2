#!/usr/bin/env python
"""
   module contains class for working with ELM327
   version: 180408
"""

import mod_globals
import sys
import re
import time
import string
import threading
import socket
from datetime import datetime
from collections import OrderedDict

try:
    import androidhelper as android
    
    mod_globals.os = 'android'
except:
    try:
        import android
        
        mod_globals.os = 'android'
    except:
        pass

if mod_globals.os != 'android':
    import serial  # sudo easy_install pyserial
    from serial.tools import list_ports

# List of commands which may require to open another Developer session (option --dev)
DevList = ['27', '28', '2E', '30', '31', '32', '34', '35', '36', '37', '3B', '3D']

# List of commands allowed in any mode
AllowedList = ['12', '19', '1A', '21', '22', '23']

# Max frame burst for Flow Control
MaxBurst = 0x7

#  Functional_2_CAN address translation tables for Renault cars 
snat = {"01":"760","02":"724","04":"762","06":"791","07":"771","08":"778","09":"7EB",
        "0D":"775","0E":"76E","0F":"770","11":"7C9","12":"7C3","13":"732","1A":"731",
        "1B":"7AC","1C":"76B","1E":"768","23":"773","24":"77D","25":"700","26":"765",
        "27":"76D","28":"7D7","29":"764","2A":"76F","2B":"735","2C":"772","2E":"7BC",
        "2F":"76C","32":"776","3A":"7D2","3C":"7DB","40":"727","46":"7CF","47":"7A8",
        "4D":"7BD","50":"738","51":"763","57":"767","58":"767","59":"734","5B":"7A5",
        "5D":"18DAF25D","60":"18DAF160","61":"7BA","62":"7DD","63":"73E","64":"7D5",
        "66":"739","67":"793","68":"77E","6B":"7B5","6E":"7E9","77":"7DA","78":"7BD",
        "79":"7EA","7A":"7E8","7C":"77C","81":"761","82":"7AD","86":"7A2",
        "87":"7A0","91":"7ED","93":"7BB","95":"7EC","97":"7C8","A1":"76C","A5":"725",
        "A6":"726","A7":"733","A8":"7B6","C0":"7B9","D1":"7EE","D2":"18DAF1D2",
        "D3":"7EE","DE":"69C","DF":"5C1","E0":"58B","E1":"5BA","E2":"5BB","E3":"4A7",
        "E4":"757","E6":"484","E7":"7EC","E8":"5C4","E9":"762","EA":"4B3","EB":"5B8",
        "EC":"5B7","ED":"704","F7":"736","F8":"737","FA":"77B","FD":"76F","FE":"76C",
        "FF":"7D0"}

dnat = {"01":"740","02":"704","04":"742","06":"790","07":"751","08":"758","09":"7E3",
		"0D":"755","0E":"74E","0F":"750","11":"7C3","12":"7C9","13":"712","1A":"711",
		"1B":"7A4","1C":"74B","1E":"748","23":"753","24":"75D","25":"70C","26":"745",
		"27":"74D","28":"78A","29":"744","2A":"74F","2B":"723","2C":"752","2E":"79C",
		"2F":"74C","32":"756","3A":"7D6","3C":"7D9","40":"707","46":"7CD",
		"47":"788","4D":"79D","50":"718","51":"743","57":"747","58":"747","59":"714",
		"5B":"785","5D":"18DA5DF2","60":"18DA60F1","61":"7B7","62":"7DC","63":"73D",
		"64":"7D4","66":"719","67":"792","68":"75A","6B":"795","6E":"7E1","77":"7CA",
		"78":"79D","79":"7E2","7A":"7E0","7C":"75C","81":"73F","82":"7AA",
		"86":"782","87":"780","91":"7E5","93":"79B","95":"7E4","97":"7D8","A1":"74C",
		"A5":"705","A6":"706","A7":"713","A8":"796","C0":"799","D1":"7E6","D2":"18DAD2F1",
		"D3":"7E6","DE":"6BC","DF":"641","E0":"60B","E1":"63A","E2":"63B","E3":"73A",
		"E4":"74F","E6":"622","E7":"7E4","E8":"644","E9":"742","EA":"79A","EB":"638",
		"EC":"637","ED":"714","F7":"716","F8":"717","FA":"75B","FD":"74F","FE":"74C",
		"FF":"7D0"}

# Code snippet from https://github.com/rbei-etas/busmaster
# Negative responses
negrsp = {"10": "NR: General Reject",
          "11": "NR: Service Not Supported",
          "12": "NR: SubFunction Not Supported",
          "13": "NR: Incorrect Message Length Or Invalid Format",
          "21": "NR: Busy Repeat Request",
          "22": "NR: Conditions Not Correct Or Request Sequence Error",
          "23": "NR: Routine Not Complete",
          "24": "NR: Request Sequence Error",
          "31": "NR: Request Out Of Range",
          "33": "NR: Security Access Denied- Security Access Requested  ",
          "35": "NR: Invalid Key",
          "36": "NR: Exceed Number Of Attempts",
          "37": "NR: Required Time Delay Not Expired",
          "40": "NR: Download not accepted",
          "41": "NR: Improper download type",
          "42": "NR: Can not download to specified address",
          "43": "NR: Can not download number of bytes requested",
          "50": "NR: Upload not accepted",
          "51": "NR: Improper upload type",
          "52": "NR: Can not upload from specified address",
          "53": "NR: Can not upload number of bytes requested",
          "70": "NR: Upload Download NotAccepted",
          "71": "NR: Transfer Data Suspended",
          "72": "NR: General Programming Failure",
          "73": "NR: Wrong Block Sequence Counter",
          "74": "NR: Illegal Address In Block Transfer",
          "75": "NR: Illegal Byte Count In Block Transfer",
          "76": "NR: Illegal Block Transfer Type",
          "77": "NR: Block Transfer Data Checksum Error",
          "78": "NR: Request Correctly Received-Response Pending",
          "79": "NR: Incorrect ByteCount During Block Transfer",
          "7E": "NR: SubFunction Not Supported In Active Session",
          "7F": "NR: Service Not Supported In Active Session",
          "80": "NR: Service Not Supported In Active Diagnostic Mode",
          "81": "NR: Rpm Too High",
          "82": "NR: Rpm Too Low",
          "83": "NR: Engine Is Running",
          "84": "NR: Engine Is Not Running",
          "85": "NR: Engine RunTime TooLow",
          "86": "NR: Temperature Too High",
          "87": "NR: Temperature Too Low",
          "88": "NR: Vehicle Speed Too High",
          "89": "NR: Vehicle Speed Too Low",
          "8A": "NR: Throttle/Pedal Too High",
          "8B": "NR: Throttle/Pedal Too Low",
          "8C": "NR: Transmission Range In Neutral",
          "8D": "NR: Transmission Range In Gear",
          "8F": "NR: Brake Switch(es)NotClosed (brake pedal not pressed or not applied)",
          "90": "NR: Shifter Lever Not In Park ",
          "91": "NR: Torque Converter Clutch Locked",
          "92": "NR: Voltage Too High",
          "93": "NR: Voltage Too Low"}


# noinspection PyBroadException,PyUnresolvedReferences
class Port:
    """This is a serial port or a TCP-connection
    if portName looks like a 192.168.0.10:35000
    then it is wifi and we should open tcp connection
    else try to open serial port
    """
    
    portType = 0  # 0-serial 1-tcp/bt 2-androidBlueTooth
    ipaddr = '192.168.0.10'
    tcpprt = 35000
    portName = ""
    portTimeout = 5  # don't change it here. Change in ELM class
    
    droid = None
    btcid = None
    
    hdr = None
    
    kaLock = False
    rwLock = False
    lastReadTime = 0
    #ka_timer = None
    
    atKeepAlive = 2  # period of sending AT during inactivity
    
    def __init__(self, portName, speed, portTimeout):
        
        self.portTimeout = portTimeout
        
        portName = portName.strip ()

        if re.match (r"^[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}$", portName):
            try:
                self.macaddr = portName
                self.channel = 1
                self.portType = 1
                self.hdr = socket.socket (socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                self.hdr.settimeout(10)
                self.hdr.connect ((self.macaddr, self.channel))
                self.hdr.setblocking (True)
            except Exception, e:
                print " \n\nERROR: Can not connect to Bluetooth ELM\n\n", e
                mod_globals.opt_demo = True
                sys.exit()
        elif re.match (r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$", portName):
            try:
                self.ipaddr, self.tcpprt = portName.split (':')
                self.tcpprt = int (self.tcpprt)
                self.portType = 1
                self.hdr = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
                self.hdr.setsockopt (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.hdr.settimeout(3)
                self.hdr.connect ((self.ipaddr, self.tcpprt))
                self.hdr.setblocking (True)
            except:
                print " \n\nERROR: Can not connect to WiFi ELM\n\n"
                mod_globals.opt_demo = True
                sys.exit()
        elif mod_globals.os == 'android' and portName == 'bt':
            self.portType = 2
            self.droid = android.Android ()
            self.droid.toggleBluetoothState (True)
            try:
                self.droid.bluetoothConnect ('00001101-0000-1000-8000-00805F9B34FB')
            except:
                pass

            if len (self.droid.bluetoothActiveConnections ().result) != 0:
                self.btcid = list (self.droid.bluetoothActiveConnections ().result.keys ())[0]

        else:
            self.portName = portName
            self.portType = 0
            try:
                self.hdr = serial.Serial (self.portName, baudrate=speed, timeout=portTimeout)
            except:  # serial.SerialException:
                print "ELM not connected or wrong COM port defined."
                iterator = sorted (list (list_ports.comports ()))
                print ""
                print "Available COM ports:"
                for port, desc, hwid in iterator:
                    print "%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc.decode ("windows-1251"), hwid)
                print ""
                mod_globals.opt_demo = True
                exit (2)
            # print self.hdr.BAUDRATES
            self.check_elm ()
        
        #self.elm_at_KeepAlive ()
    
    def __del__(self):
        pass
        #if self.ka_timer:
        #    self.ka_timer.cancel ()

    def reinit(self):
        '''
        Need for wifi adapters with short connection timeout
        '''
        if self.portType != 1: return

        if not hasattr(self, 'macaddr'):
          self.hdr.close()
          self.hdr = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
          self.hdr.setsockopt (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
          self.hdr.connect ((self.ipaddr, self.tcpprt))
          self.hdr.setblocking (True)

        self.write("AT\r")
        self.expect(">",1)

    '''
    def elm_at_KeepAlive(self):
      
      try:
  
          if not self.rwLock and time.time () > self.lastReadTime + self.atKeepAlive:
        
            self.kaLock = True
            data = 'AT\r'
            try:
              if self.portType == 1:
                self.hdr.sendall (data)
              elif self.portType == 2:
                self.droid.bluetoothWrite (data)
              else:
                self.hdr.write (data)
        
              tb = time.time ()  # start time
              tmpBuff = ""
              while True:
                if not mod_globals.opt_demo:
                  byte = self.read ()
                else:
                  byte = '>'
            
                if byte == '\r': byte = '\n'
            
                tmpBuff += byte
                tc = time.time ()
                if '>' in tmpBuff:
                  return
                if (tc - tb) > 0.01:
                  return
            except:
              pass

      finally:
        self.lastReadTime = time.time ()
        self.kaLock = False
        if self.ka_timer:
          self.ka_timer.cancel ()
        if self.atKeepAlive > 0:
          self.ka_timer = threading.Timer (self.atKeepAlive, self.elm_at_KeepAlive)
          self.ka_timer.setDaemon(True)
          self.ka_timer.start ()
    '''
    
    def read(self):
        byte = ""
        try:
            if self.portType == 1:
                try:
                    byte = self.hdr.recv (1)
                except:
                    pass
            elif self.portType == 2:
                byte = self.droid.bluetoothRead (1).result
            else:
                inInputBuffer = self.hdr.inWaiting()
                if inInputBuffer:
                    if mod_globals.opt_obdlink:
                        byte = self.hdr.read(inInputBuffer)
                    else:
                        byte = self.hdr.read(1)
        except:
            print '*' * 40
            print '*       Connection to ELM was lost'
            mod_globals.opt_demo = True
            exit (2)
        return byte
    
    def write(self, data):
        
        # dummy sync
        self.rwLock = True
        i = 0
        while self.kaLock and i < 10:
            time.sleep (0.02)
            i = i + 1
        
        try:
            if self.portType == 1:
                try:
                    rcv_bytes = self.hdr.sendall(data)
                except:
                    self.reinit()
                    rcv_bytes = self.hdr.sendall(data)
                return rcv_bytes
            elif self.portType == 2:
                # return self.droid.bluetoothWrite(data , self.btcid)
                return self.droid.bluetoothWrite (data)
            else:
                return self.hdr.write (data)
        except:
            print '*' * 40
            print '*       Connection to ELM was lost'
            mod_globals.opt_demo = True
            exit (2)
    
    def expect(self, pattern, time_out=1):
        
        tb = time.time ()  # start time
        self.buff = ""
        try:
            while True:
                if not mod_globals.opt_demo:
                    byte = self.read ()
                else:
                    byte = '>'
                
                if '\r' in byte: byte = byte.replace('\r', '\n')
                self.buff += byte
                tc = time.time ()
                if pattern in self.buff:
                    self.lastReadTime = time.time ()
                    self.rwLock = False
                    return self.buff
                if (tc - tb) > time_out:
                    self.lastReadTime = time.time ()
                    self.rwLock = False
                    return self.buff + "TIMEOUT"
        except:
            self.rwLock = False
            pass
        self.lastReadTime = time.time ()
        self.rwLock = False
        return ''
    
    def check_elm(self):
        
        self.hdr.timeout = 2
        
        for s in [38400, 115200, 230400, 500000, 1000000, 2000000]:
            print "\r\t\t\t\t\rChecking port speed:", s,
            sys.stdout.flush ()
            
            self.hdr.baudrate = s
            self.hdr.flushInput ()
            self.write ("\r")
            
            # search > string
            tb = time.time ()  # start time
            self.buff = ""
            while True:
                if not mod_globals.opt_demo:
                    byte = self.read ()
                else:
                    byte = '>'
                self.buff += byte
                tc = time.time ()
                if '>' in self.buff:
                    mod_globals.opt_speed = s
                    print "\nStart COM speed: ", s
                    self.hdr.timeout = self.portTimeout
                    return
                if (tc - tb) > 1:
                    break
        print "\nELM not responding"
        sys.exit ()
    
    def soft_boudrate(self, boudrate):
        
        if mod_globals.opt_demo:
            return
        
        if self.portType == 1:  # wifi is not supported
            print "ERROR - wifi/bluetooth do not support changing boud rate"
            return
        
        # stop any read/write
        self.rwLock = False
        self.kaLock = False
        #if self.ka_timer:
        #    self.ka_timer.cancel ()
        
        print "Changing baud rate to:", boudrate,
        
        if mod_globals.opt_obdlink:
            self.write("ST SBR " + str(boudrate) + "\r")
        else:
            if boudrate == 38400:
                self.write ("at brd 68\r")
            elif boudrate == 57600:
                self.write ("at brd 45\r")
            elif boudrate == 115200:
                self.write ("at brd 23\r")
            elif boudrate == 230400:
                self.write ("at brd 11\r")
            elif boudrate == 500000:
                self.write ("at brd 8\r")
        
        # search OK
        tb = time.time ()  # start time
        self.buff = ""
        while True:
            if not mod_globals.opt_demo:
                byte = self.read ()
            else:
                byte = 'OK'
            if byte == '\r' or byte == '\n':
                self.buff = ""
                continue
            self.buff += byte
            tc = time.time ()
            if 'OK' in self.buff:
                break
            if (tc - tb) > 1:
                print "ERROR - command not supported"
                return
        
        self.hdr.timeout = 1
        self.hdr.baudrate = boudrate
        
        # search ELM
        tb = time.time ()  # start time
        self.buff = ""
        while True:
            if not mod_globals.opt_demo:
                byte = self.read ()
            else:
                byte = 'ELM'
            if byte == '\r' or byte == '\n':
                self.buff = ""
                continue
            self.buff += byte
            tc = time.time ()
            if 'ELM' or 'STN' in self.buff:
                break
            if (tc - tb) > 1:
                print "ERROR - rate not supported. Let's go back."
                self.hdr.timeout = self.portTimeout
                self.hdr.baudrate = mod_globals.opt_speed
                self.rwLock = False
                # disable at_keepalive
                #self.elm_at_KeepAlive ()
                return
        
        self.write ("\r")
        
        # search >
        tb = time.time ()  # start time
        self.buff = ""
        while True:
            if not mod_globals.opt_demo:
                byte = self.read ()
            else:
                byte = '>'
            if byte == '\r' or byte == '\n':
                self.buff = ""
                continue
            self.buff += byte
            tc = time.time ()
            if '>' in self.buff:
                mod_globals.opt_rate = mod_globals.opt_speed
                break
            if (tc - tb) > 1:
                print "ERROR - something went wrong. Let's back."
                self.hdr.timeout = self.portTimeout
                self.hdr.baudrate = mod_globals.opt_speed
                self.rwLock = False
                # disable at_keepalive
                #self.elm_at_KeepAlive ()
                return
        
        print "OK"
        self.rwLock = False
        # disable at_keepalive
        #self.elm_at_KeepAlive ()
        
        return


# noinspection PyUnusedLocal
class ELM:
    """ELM327 class"""
    
    port = 0
    lf = 0
    vf = 0
    
    keepAlive = 4  # send startSession to CAN after silence if startSession defined
    busLoad = 0  # I am sure than it should be zero
    srvsDelay = 0  # the delay next command requested by service
    lastCMDtime = 0  # time when last command was sent to bus
    portTimeout = 5  # timeout of port (com or tcp)
    elmTimeout = 0  # timeout set by ATST
    performanceModeLevel = 1 # number of dataids, that can be sent in one 22 request
    
    # error counters
    error_frame = 0
    error_bufferfull = 0
    error_question = 0
    error_nodata = 0
    error_timeout = 0
    error_rx = 0
    error_can = 0
    
    response_time = 0
    screenRefreshTime = 0

    buff = ""
    currentprotocol = ""
    currentsubprotocol = ""
    currentaddress = ""
    startSession = ""
    lastinitrsp = ""
    
    currentScreenDataIds = [] #dataids displayed on current screen
    rsp_cache = OrderedDict()  # cashes responses for current screen
    l1_cache = {}  # save number of frames in responces
    tmpNotSupportedCommands = {} #temporary list for requests that were positive and became negative for no reason
    notSupportedCommands = {} # save them to not slow down polling
    ecudump = {}  # for demo only. contains responses for all 21xx and 22xxxx requests
    
    ATR1 = True
    ATCFC0 = False
    
    # The next variables is used for fake adapter detection
    supportedCommands = 0
    unsupportedCommands = 0
    
    portName = ""
    
    lastMessage = ""
    
    monitorThread = None
    monitorCallBack = None
    monitorSendAllow = None
    run_allow_event = None
    dmf = None

    waitedFrames = ""
    endWaitingFrames = True
    rspLen = 0
    fToWait = 0


    def __init__(self, portName, speed, log, startSession='10C0'):
        
        self.portName = portName
        
        # debug
        # print 'Port Open'
        
        if not mod_globals.opt_demo:
            # self.port = serial.Serial(portName, baudrate=speed, timeout=self.portTimeout)
            self.port = Port (portName, speed, self.portTimeout)
        
        if len(mod_globals.opt_log)>0: # and mod_globals.opt_demo==False:
            self.lf = open ("./logs/elm_" + mod_globals.opt_log, "at")
            self.vf = open ("./logs/ecu_" + mod_globals.opt_log, "at")

        if mod_globals.opt_debug and mod_globals.debug_file==None:
            mod_globals.debug_file = open ("./logs/debug.txt", "at")

        self.lastCMDtime = 0
        self.ATCFC0 = mod_globals.opt_cfc0

        if self.lf != 0:
            tmstr = datetime.now ().strftime ("%x %H:%M:%S.%f")[:-3]
            self.lf.write('#' * 60 + "\n#[" + tmstr + "] Check ELM type\n" + '#' * 60 + "\n")
            self.lf.flush()

        # check OBDLink
        elm_rsp = self.cmd("STI")
        if elm_rsp and '?' not in elm_rsp:
            firmware_version = elm_rsp.split(" ")[-1]
            try:
                firmware_version = firmware_version.split(".")
                version_number = int(''.join([re.sub('\D', '', version) for version in firmware_version]))
                stpx_introduced_in_version_number = 420 #STN1110 got STPX last in version v4.2.0
                if version_number >= stpx_introduced_in_version_number:
                    mod_globals.opt_obdlink = True
            except:
                raw_input("\nCannot determine OBDLink version.\n" +
                "OBDLink performance may be decreased.\n" + 
                "Press any key to continue...\n")

            # check STN
            elm_rsp = self.cmd("STP 53")
            if '?' not in elm_rsp:
                mod_globals.opt_stn = True
        
        # Max out the UART speed for the fastest polling rate
        if mod_globals.opt_csv and not mod_globals.opt_demo:
            if mod_globals.opt_obdlink:
                self.port.soft_boudrate(2000000)
            elif self.port.portType == 0:
                self.port.soft_boudrate(230400)

    def __del__(self):
        if not mod_globals.opt_demo:
            print '*' * 40
            print '*       RESETTING ELM'
            #if self.port.ka_timer:
            #    self.port.ka_timer.cancel ()
            self.port.write ("atz\r")
            self.port.atKeepAlive = 0
            if self.run_allow_event:
                self.run_allow_event.clear ()
            # if self.monitorThread:
            #     self.monitorThread.clear ()
        print '*' * 40
        print '* '
        print '*       ERRORS STATISTIC'
        print '* '
        print '* error_frame      = ', self.error_frame
        print '* error_bufferfull = ', self.error_bufferfull
        print '* error_question   = ', self.error_question
        print '* error_nodata     = ', self.error_nodata
        print '* error_timeout    = ', self.error_timeout
        print '* error_rx         = ', self.error_rx
        print '* error_can        = ', self.error_can
        print '*'
        print '*       RESPONSE TIME (Average)'
        print '* '
        print '* response_time    = ', '{0:.3f}'.format(self.response_time)
        print '* '
        print '*' * 40
        print self.lastMessage
    
    def clear_cache(self):
        """ Clear L2 cache before screen update
        """
        #print 'Clearing L2 cache'
        self.rsp_cache = OrderedDict()

        # if not mod_globals.opt_demo:
        #  self.rsp_cache = {}
    
    def setDump(self, ecudump):
        """ define ecudum for demo mode"""
        self.ecudump = ecudump

    def loadDump(self, dumpname):

        print 'Loading dump:', dumpname

        df = open(dumpname, 'rt')
        lines = df.readlines()
        df.close()

        ecudump = {}

        for l in lines:
            l = l.strip().replace('\n', '')
            if l.count(':') == 1:
                req, rsp = l.split(':')
                ecudump[req] = rsp

        self.setDump(ecudump)

    def debugMonitor(self):
        byte = ""
        try:
            if self.dmf is None:
                self.dmf = open ("./logs/" + mod_globals.opt_log, "rt")
            byte = self.dmf.read (1)
        except:
            pass
        if not byte:
            self.dmf = None
            byte = ' '
        
        if byte == '\n':
            time.sleep (0.001)
        
        return byte
    
    def monitor(self, callback, send_allow, c_t=0.1, c_f=10):
        self.monitorCallBack = callback
        self.monitorSendAllow = send_allow
        
        coalescing_time = c_t
        coalescing_frames = c_f
        
        lst = time.time ()  # last send time
        frameBuff = ""
        frameBuffLen = 0
        buff = ""
        
        if not mod_globals.opt_demo:
            self.cmd ("at h1")
            self.cmd ("at d1")
            self.cmd ("at s1")
            self.port.write ("at ma\r\n")
        
        self.mlf = 0
        if not mod_globals.opt_demo and len (mod_globals.opt_log) > 0:
            self.mlf = open ("./logs/" + mod_globals.opt_log, "wt")
        
        while self.run_allow_event.isSet ():
            if not mod_globals.opt_demo:
                byte = self.port.read ()
            else:
                byte = self.debugMonitor ()

            ct = time.time ()  # current time
            if (ct - lst) > coalescing_time:  # and frameBuffLen>0:
                if self.monitorSendAllow is None or not self.monitorSendAllow.isSet ():
                    self.monitorSendAllow.set ()
                    #print 'time callback'
                    callback (frameBuff)
                    #print 'return from callback'
                lst = ct
                frameBuff = ""
                frameBuffLen = 0
            
            if len (byte) == 0: continue
            
            if byte == '\r' or byte == '\n':
                
                line = buff.strip()
                buff = ""
                
                if len (line) < 6:
                    continue

                if ':' in line:
                    line = line.split(':')[-1].strip()
                
                if ord (line[4:5]) < 0x31 or ord (line[4:5]) > 0x38: continue
                
                dlc = int (line[4:5])
                
                if len (line) < (dlc * 3 + 5): continue
                
                frameBuff = frameBuff + line + '\n'
                frameBuffLen = frameBuffLen + 1
                
                # save log
                if self.mlf:
                    #self.mlf.write (line + '\n')

                    #debug
                    tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    self.mlf.write(tmstr + ' : ' + line + '\n')
                
                if frameBuffLen >= coalescing_frames:
                    if self.monitorSendAllow is None or not self.monitorSendAllow.isSet ():
                        self.monitorSendAllow.set ()
                        #print 'frame callback'
                        callback (frameBuff)
                        #print 'return from callback'
                    lst = ct
                    frameBuff = ""
                    frameBuffLen = 0
                
                continue

            buff += byte
            if byte == '>':
                self.port.write ("\r")

    def setMonitorFilter(self, filt, mask):
        if mod_globals.opt_demo or self.monitorCallBack is None: return
        # if len(filter)!=3 or len(mask)!=3: return
        
        print
        print "Filter : " + filt
        print "Mask   : " + mask
        sys.stdout.flush ()
        
        # stop monitor
        self.stopMonitor ()

        if len (filt) != 3 or len (mask) != 3 or filt == '000':
            self.cmd ("at cf 000")
            self.cmd ("at cm 000")
        else:
            self.cmd ("at cf " + filt)
            self.cmd ("at cm " + mask)
        
        self.startMonitor (self.monitorCallBack, self.monitorSendAllow)
    
    def startMonitor(self, callback, sendAllow=None, c_t=0.1, c_f=10):
        if self.currentprotocol != "can":
            print "Monitor mode is possible only on CAN bus"
            return
        self.run_allow_event = threading.Event ()
        self.run_allow_event.set ()
        self.monitorThread = threading.Thread (target=self.monitor, args=(callback, sendAllow, c_t, c_f))
        self.monitorThread.setDaemon(True)
        self.monitorThread.start ()
    
    def stopMonitor(self):
        if not mod_globals.opt_demo:
          self.port.write ("\r\n")
        self.run_allow_event.clear ()
        time.sleep (0.2)
        if mod_globals.opt_demo or self.monitorCallBack is None: return

        tmp = self.portTimeout
        self.portTimeout = 0.3
        self.cmd("at")
        self.cmd("at h0")
        self.cmd("at d0")
        self.cmd("at s0")
        self.portTimeout = tmp

    def nr78_monitor(self, callback, send_allow, c_t=0.1, c_f=1):
        self.monitorCallBack = callback
        self.monitorSendAllow = send_allow

        coalescing_time = c_t
        coalescing_frames = c_f

        lst = time.time()  # last send time
        frameBuff = ""
        frameBuffLen = 0
        buff = ""

        if not mod_globals.opt_demo:
            self.port.write("at ma\r\n")

        while self.run_allow_event.isSet():
            #there should be no nr78 in demo mode
            #if not mod_globals.opt_demo:
            #    byte = self.port.read()
            #else:
            #    byte = self.debugMonitor()

            byte = self.port.read()

            ct = time.time()  # current time
            if (ct - lst) > coalescing_time:  # and frameBuffLen>0:
                if self.monitorSendAllow is None or not self.monitorSendAllow.isSet():
                    self.monitorSendAllow.set()
                    # print 'time callback'
                    callback(frameBuff)
                    # print 'return from callback'
                lst = ct
                frameBuff = ""
                frameBuffLen = 0

            if len(byte) == 0: continue

            if byte == '\r' or byte == '\n':

                line = buff.strip()
                buff = ""
                if len(line) < 2: continue
                if 'atma' in line.replace(' ', '').lower() : continue
                if 'stopped' in line.lower() : continue

                frameBuff = frameBuff + line + '\n'
                frameBuffLen = frameBuffLen + 1

                # save log
                if self.lf:
                    tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    self.lf.write('mon: '+tmstr + ' : ' + line + '\n')

                if frameBuffLen >= coalescing_frames:
                    if self.monitorSendAllow is None or not self.monitorSendAllow.isSet():
                        self.monitorSendAllow.set()
                        # print 'frame callback'
                        callback(frameBuff)
                        # print 'return from callback'
                    lst = ct
                    frameBuff = ""
                    frameBuffLen = 0

                continue

            buff += byte
            if byte == '>':
                self.port.write("\r")

    def nr78_startMonitor(self, callback, sendAllow=None, c_t=0.1, c_f=1):
        if self.currentprotocol != "can":
            print "Monitor mode is possible only on CAN bus"
            return
        self.run_allow_event = threading.Event()
        self.run_allow_event.set()
        self.monitorThread = threading.Thread(target=self.nr78_monitor, args=(callback, sendAllow, c_t, c_f))
        self.monitorThread.setDaemon(True)
        self.monitorThread.start()

    def nr78_stopMonitor(self):
        if not mod_globals.opt_demo:
            self.port.write("\r")
        self.run_allow_event.clear()
        time.sleep(0.2)
        if mod_globals.opt_demo or self.monitorCallBack is None: return

        tmp = self.portTimeout
        self.portTimeout = 0.3
        self.send_raw("AT")
        self.portTimeout = tmp

    def waitFramesCallBack(self, frames ):

        for l in frames.split('\n'):
            l = l.strip()
            if len(l)==0: continue
            l = l.replace(' ', '')
            if l[:4].upper()=='037F' and l[6:8]=='78':
                # wait again
                self.rspLen = 0
                self.fToWait = 0
                break

            self.waitedFrames = self.waitedFrames + l

            if l[:1]=='3':  #flow control
                self.endWaitingFrames = True


            elif l[:1]=='0':  #single frame
                nBytes = int( l[1:2], 16 )
                if nBytes<8:
                    self.rspLen = 1
                    self.fToWait = 0 # becouse we've recieved it
                else:
                    print '\n ERROR #1 in waitFramesCallBack'
                self.endWaitingFrames = True

            elif l[:1]=='1':  #first frame
                nBytes = int( l[1:4], 16 )
                nBytes = nBytes - 6  # becouse we've recieved first frame
                self.rspLen = nBytes/7 + bool( nBytes%7 )
                #self.fToWait = min(self.rspLen,MaxBurst)
                self.endWaitingFrames = True  # stop waiting and send FlowControl

            elif l[:1]=='2':  #consecutive frame
                self.rspLen = self.rspLen - 1
                self.fToWait = self.fToWait - 1
                if self.fToWait == 0:
                    self.endWaitingFrames = True

        self.monitorSendAllow.clear()
        return

    def waitFrames(self, timeout ):

        self.waitedFrames = ""
        self.endWaitingFrames = False
        self.fToWait = min(self.rspLen, MaxBurst)

        sendAllow = threading.Event()
        sendAllow.clear()
        self.nr78_startMonitor( self.waitFramesCallBack, sendAllow, 0.1, 1 )

        beg = time.time ()

        while not self.endWaitingFrames and ( time.time()-beg < timeout ):
            time.sleep(0.01)

        #debug
        #print '>>>> ', self.waitedFrames
        self.nr78_stopMonitor()

        #debug
        #print '>>>> ', self.waitedFrames

        return self.waitedFrames

    def getFromCache(self, req ):
        if mod_globals.opt_demo and req in self.ecudump.keys():
            return self.ecudump[req]

        if req in self.rsp_cache.keys():
            return self.rsp_cache[req]

        return ''

    def delFromCache(self, req ):
        if not mod_globals.opt_demo and  req in self.rsp_cache.keys():
            del self.rsp_cache[req]

    def checkIfCommandUnsupported(self, req, res):
        if "NR" in res:
            nr = res.split (':')[1]
            if nr in ['12']:
                if mod_globals.opt_csv_only: # all unsupported commands must be removed immediately in csv_only mode
                    self.notSupportedCommands[req] = res
                else:
                    if req in self.tmpNotSupportedCommands.keys():
                        del self.tmpNotSupportedCommands[req]
                        self.notSupportedCommands[req] = res
                    else:
                        self.tmpNotSupportedCommands[req] = res
        else:
            if req in self.tmpNotSupportedCommands.keys(): # if previous response was negative and now it is positive
                del self.tmpNotSupportedCommands[req]  # remove it from negative commands queue, because of false negative

    def request(self, req, positive='', cache=True, serviceDelay="0"):
        """ Check if request is saved in L2 cache.
        If not then
          - make real request
          - convert responce to one line
          - save in L2 cache
        returns response without consistency check
        """
        
        if mod_globals.opt_demo and req in self.ecudump.keys ():
            return self.ecudump[req]
        
        if cache and req in self.rsp_cache.keys ():
            return self.rsp_cache[req]
        
        # send cmd
        rsp = self.cmd (req, int(serviceDelay))

        # parse responce
        res = ""
        if self.currentprotocol != "can":
            # Trivially reject first line (echo)
            rsp_split = rsp.split ('\n')[1:]
            for s in rsp_split:
                if '>' not in s and len (s.strip ()):
                    res += s.strip () + ' '
        else:
            for s in rsp.split ('\n'):
                if ':' in s:
                    res += s[2:].strip () + ' '
                else:  # responce consists only from one frame
                    if s.replace (' ', '').startswith (positive.replace (' ', '')):
                        res += s.strip () + ' '
        
        rsp = res
        
        # populate L2 cache
        if req[:2] in AllowedList:
            self.rsp_cache[req] = rsp
        
        # save log
        if self.vf != 0 and 'NR' not in rsp :
            tmstr = datetime.now ().strftime ("%H:%M:%S.%f")[:-3]

            tmp_addr = self.currentaddress
            if self.currentaddress in dnat.keys():
                tmp_addr = dnat[self.currentaddress]
            self.vf.write (tmstr + ";" + tmp_addr + ";" + req + ";" + rsp + "\n")
            self.vf.flush ()
        
        return rsp

    # noinspection PyUnboundLocalVariable
    def cmd(self, command, serviceDelay=0):
        
        command = command.upper ()

        # check if command not supported
        if command in self.notSupportedCommands.keys():
            return self.notSupportedCommands[command]
        
        tb = time.time ()  # start time
        
        devmode = False
        
        # Ensure time gap between commands
        # dl = self.busLoad + self.srvsDelay - tb + self.lastCMDtime
        if ((tb - self.lastCMDtime) < (self.busLoad + self.srvsDelay)) and command.upper()[:2] not in ['AT','ST']:
            time.sleep (self.busLoad + self.srvsDelay - tb + self.lastCMDtime)
        
        tb = time.time ()  # renew start time

        # save current session
        saveSession = self.startSession

        # If dev mode then temporary switch to Development Session
        if mod_globals.opt_dev and command[0:2] in DevList:
            
            devmode = True
            
            # open Development session
            self.start_session (mod_globals.opt_devses)
            self.lastCMDtime = time.time ()
            
            # log switching event
            if self.lf != 0:
                tmstr = datetime.now ().strftime ("%H:%M:%S.%f")[:-3]
                self.lf.write ("#[" + tmstr + "]" + "Switch to dev mode\n")
                self.lf.flush ()
                
        # If we are on CAN and there was more than keepAlive seconds of silence
        # then send startSession command again
        if (tb - self.lastCMDtime) > self.keepAlive and len (self.startSession) > 0:
            
            # log KeepAlive event
            if self.lf != 0:
                tmstr = datetime.now ().strftime ("%H:%M:%S.%f")[:-3]
                self.lf.write ("#[" + tmstr + "]" + "KeepAlive\n")
                self.lf.flush ()
                
            # send keepalive
            #if not mod_globals.opt_demo:
            #  self.port.reinit() #experimental
            self.send_cmd (self.startSession)
            self.lastCMDtime = time.time ()  # for not to get into infinite loop
        
        # send command and check for ask to wait
        cmdrsp = ""
        rep_count = 3
        while rep_count > 0:
            rep_count = rep_count - 1
            no_negative_wait_response = True
            
            self.lastCMDtime = tc = time.time ()
            cmdrsp = self.send_cmd (command)
            
            self.checkIfCommandUnsupported(command, cmdrsp) # check if response for this command is NR:12

            # if command[0:2] not in AllowedList:
            #  break

            for line in cmdrsp.split ('\n'):
                line = line.strip ().upper ()
                nr = ''
                if line.startswith ("7F") and len (line) == 8 and line[6:8] in negrsp.keys ():
                    nr = line[6:8]
                if line.startswith ("NR"):
                    nr = line.split (':')[1]
                if nr in ['21', '23']:  # it is look like the ECU asked us to wait a bit
                    time.sleep (0.5)
                    no_negative_wait_response = False
                elif nr in ['78']:
                    self.send_raw ('at at 0')
                    self.send_raw ('at st ff')
                    self.lastCMDtime = tc = time.time ()
                    cmdrsp = self.send_cmd (command)
                    self.send_raw ('at at 1')
                    break
            
            if no_negative_wait_response:
                break
                
        # If dev mode then switch back from Development Session
        if devmode:
            
            # restore current session
            self.startSession = saveSession
            self.start_session (self.startSession)
            self.lastCMDtime = time.time ()
            
            # log switching event
            if self.lf != 0:
                tmstr = datetime.now ().strftime ("%H:%M:%S.%f")[:-3]
                self.lf.write ("#[" + tmstr + "]" + "Switch back from dev mode\n")
                self.lf.flush ()
                
                # add srvsDelay to time gap before send next command
        self.srvsDelay = float (serviceDelay) / 1000.
        
        # check for negative response from k-line (CAN NR processed in send_can***)
        for line in cmdrsp.split ('\n'):
            line = line.strip ().upper ()
            if line.startswith ("7F") and len (line) == 8 and line[6:8] in negrsp.keys () and self.currentprotocol != "can":
                # if not mod_globals.state_scan: print line, negrsp[line[6:8]]
                if self.lf != 0:
                    # tm = str (time.time ())
                    self.lf.write ("#[" + str (tc - tb) + "] rsp:" + line + ":" + negrsp[line[6:8]] + "\n")
                    self.lf.flush ()
                if self.vf != 0:
                    tmstr = datetime.now ().strftime ("%H:%M:%S.%f")[:-3]

                    tmp_addr = self.currentaddress
                    if self.currentaddress in dnat.keys():
                        tmp_addr = dnat[self.currentaddress]

                    self.vf.write (tmstr + ";" + tmp_addr + ";" + command + ";" + line + ";" + negrsp[line[6:8]] + "\n")
                    self.vf.flush ()

        return cmdrsp
    
    def send_cmd(self, command):
        
        command = command.upper ()
        
        # deal with exceptions
        # boudrate 38400 not enough to read full information about errors
        if not mod_globals.opt_obdlink and len (command) == 6 and command[:4] == '1902':
            command = '1902AF'
        
        if command.upper()[:2] in ["AT","ST"] or self.currentprotocol != "can":
            return self.send_raw (command)

        if self.ATCFC0:
            return self.send_can_cfc0 (command)
        else:
            if mod_globals.opt_obdlink:
                if mod_globals.opt_caf:
                    rsp = self.send_can_cfc_caf(command)
                else:
                    rsp = self.send_can_cfc(command)
            else:
                rsp = self.send_can (command)
            if self.error_frame > 0 or self.error_bufferfull > 0:  # then fallback to cfc0
                self.ATCFC0 = True
                self.cmd ("at cfc0")
                rsp = self.send_can_cfc0 (command)
            return rsp
    
    def send_can(self, command):
        command = command.strip ().replace (' ', '').upper ()
        isCommandInCache = command in self.l1_cache.keys()

        if len(command) == 0:
            return
        if len (command) % 2 != 0:
            return "ODD ERROR"
        if not all (c in string.hexdigits for c in command):
            return "HEX ERROR"
        
        # do framing
        raw_command = []
        cmd_len = len (command) / 2
        if cmd_len < 8:  # single frame
            # check L1 cache here
            if isCommandInCache and int('0x' + self.l1_cache[command], 16) < 16:
                raw_command.append (("%0.2X" % cmd_len) + command + self.l1_cache[command])
            else:
                raw_command.append (("%0.2X" % cmd_len) + command)
        else:
            # first frame
            raw_command.append ("1" + ("%0.3X" % cmd_len)[-3:] + command[:12])
            command = command[12:]
            # consecutive frames
            frame_number = 1
            while len (command):
                raw_command.append ("2" + ("%X" % frame_number)[-1:] + command[:14])
                frame_number = frame_number + 1
                command = command[14:]
         
        responses = []
        
        # send farmes
        for f in raw_command:
            # send next frame
            frsp = self.send_raw (f)
            # analyse response (1 phase)
            for s in frsp.split ('\n'):
                if s.strip () == f:  # echo cancelation
                    continue
                s = s.strip ().replace (' ', '')
                if len (s) == 0:  # empty string
                    continue
                if all (c in string.hexdigits for c in s):  # some data
                    if s[:1] == '3':  # flow control, just ignore it in this version
                        continue
                    responses.append (s)
        
        # analise response (2 phase)
        result = ""
        noerrors = True
        cframe = 0  # frame counter
        nbytes = 0  # number bytes in response
        nframes = 0  # numer frames in response
        
        if len (responses) == 0:  # no data in response
            return ""
        
        if len (responses) > 1 and responses[0].startswith ('037F') and responses[0][6:8] == '78':
            responses = responses[1:]
            mod_globals.opt_n1c = True
        
        if len (responses) == 1:  # single freme response
            if responses[0][:1] == '0':
                nbytes = int (responses[0][1:2], 16)
                nframes = 1
                result = responses[0][2:2 + nbytes * 2]
            else:  # wrong response (not all frames received)
                self.error_frame += 1
                noerrors = False
        else:  # multi frame response
            if responses[0][:1] == '1':  # first frame
                nbytes = int (responses[0][1:4], 16)
                nframes = nbytes / 7 + 1
                cframe = 1
                result = responses[0][4:16]
            else:  # wrong response (first frame omitted)
                self.error_frame += 1
                noerrors = False
            
            for fr in responses[1:]:
                if fr[:1] == '2':  # consecutive frames
                    tmp_fn = int (fr[1:2], 16)
                    if tmp_fn != (cframe % 16):  # wrong response (frame lost)
                        self.error_frame += 1
                        noerrors = False
                        continue
                    cframe += 1
                    result += fr[2:16]
                else:  # wrong response
                    self.error_frame += 1
                    noerrors = False
        
        # Check for negative
        if result[:2] == '7F': noerrors = False
        
        # populate L1 cache
        if noerrors and command[:2] in AllowedList and not mod_globals.opt_n1c:
            self.l1_cache[command] = str(hex(nframes))[2:].upper()
        
        if len (result) / 2 >= nbytes and noerrors:
            # split by bytes and return
            result = ' '.join (a + b for a, b in zip (result[::2], result[1::2]))
            return result
        else:
            # check for negative response (repeat the same as in cmd())
            if result[:2] == '7F' and result[4:6] in negrsp.keys ():
                if self.vf != 0:
                    tmstr = datetime.now ().strftime ("%H:%M:%S.%f")[:-3]

                    #debug
                    #print result

                    self.vf.write (
                        tmstr + ";" + dnat[self.currentaddress] + ";" + command + ";" + result + ";" + negrsp[result[4:6]] + "\n")
                    self.vf.flush ()
                return "NR:" + result[4:6] + ':' + negrsp[result[4:6]]
            else:
                return "WRONG RESPONSE"

    # Can be used only with OBDLink based ELM, wireless especially.
    def send_can_cfc_caf(self, command):
        if len(command) == 0:
            return
        if len(command) % 2 != 0:
            return "ODD ERROR"
        if not all(c in string.hexdigits for c in command):
            return "HEX ERROR"

        frsp = self.send_raw('STPX D:' + command + ',R:' + '1')

        responses = []

        for s in frsp.split('\n'):
            if s.strip()[:4] == "STPX":  # echo cancelation
                continue

            s = s.strip().replace(' ', '')
            if len(s) == 0:  # empty string
                continue

            responses.append(s)
        
        result = ""
        noerrors = True

        if len (responses) == 0:  # no data in response
            return ""

        nodataflag = False
        for s in responses:

            if 'NO DATA' in s:
                nodataflag = True
                break

            if all(c in string.hexdigits for c in s):  # some data
                result = s

        # Check for negative
        if result[:2] == '7F': noerrors = False

        if noerrors:
            # split by bytes and return
            result = ' '.join(a + b for a, b in zip(result[::2], result[1::2]))
            return result
        else:
            # check for negative response (repeat the same as in cmd())
            # debug
            # print "Size error: ", result
            if result[:2] == '7F' and result[4:6] in negrsp.keys():
                if self.vf != 0:
                    tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    self.vf.write(
                        tmstr + ";" + dnat[self.currentaddress] + ";" + command + ";" + result + ";" + negrsp[
                            result[4:6]] + "\n")
                    self.vf.flush()
                return "NR:" + result[4:6] + ':' + negrsp[result[4:6]]
            else:
                return "WRONG RESPONSE"
    
    # Can be used only with OBDLink based ELM
    def send_can_cfc(self, command):

        command = command.strip().replace(' ', '').upper()
        init_command = command

        if len(command) == 0:
            return
        if len(command) % 2 != 0:
            return "ODD ERROR"
        if not all(c in string.hexdigits for c in command):
            return "HEX ERROR"

        # do framing
        raw_command = []
        cmd_len = len(command) / 2
        if cmd_len < 8:  # single frame
            raw_command.append(("%0.2X" % cmd_len) + command)
        else:
            # first frame
            raw_command.append("1" + ("%0.3X" % cmd_len)[-3:] + command[:12])
            command = command[12:]
            # consecutive frames
            frame_number = 1
            while len(command):
                raw_command.append("2" + ("%X" % frame_number)[-1:] + command[:14])
                frame_number = frame_number + 1
                command = command[14:]

        responses = []

        # send frames
        BS = 1  # Burst Size
        ST = 0  # Frame Interval
        Fc = 0  # Current frame
        Fn = len(raw_command)  # Number of frames
        frsp = ''

        if raw_command[Fc].startswith('0') and init_command in self.l1_cache.keys():
            frsp = self.send_raw ('STPX D:' + raw_command[Fc] + ',R:' + self.l1_cache[init_command])
        elif raw_command[Fc].startswith('1'):
            frsp = self.send_raw ('STPX D:' + raw_command[Fc] + ',R:' + '1')
        else:
            frsp = self.send_raw ('STPX D:' + raw_command[Fc])
    

        while Fc < Fn:
            tb = time.time()  # time of sending (ff)

            if raw_command[Fc][:1] != '2':
                Fc = Fc + 1

            # analyse response
            for s in frsp.split('\n'):

                if s.strip()[:4] == "STPX":  # echo cancelation
                    continue

                s = s.strip().replace(' ', '')
                if len(s) == 0:  # empty string
                    continue

                if all(c in string.hexdigits for c in s):  # some data
                    if s[:1] == '3':  # FlowControl

                        # extract Burst Size
                        BS = s[2:4]
                        if BS == '': BS = '03'
                        BS = int(BS, 16)

                        # extract Frame Interval
                        ST = s[4:6]
                        if ST == '': ST = 'EF'
                        if ST[:1].upper() == 'F':
                            ST = int(ST[1:2], 16) * 100
                        else:
                            ST = int(ST, 16)
                            # print 'BS:',BS,'ST:',ST
                        break  # go to sending consequent frames
                    else:
                        responses.append(s)
                        continue

            # sending consequent frames according to FlowControl
            frames_left = (Fn - Fc)
            cf = min({BS, frames_left})  # number of frames to send without response

            while cf > 0:
                burst_size_command = ''.join(raw_command[Fc: Fc + cf])
                burst_size_command_last_frame = burst_size_command[len(''.join(raw_command[Fc: Fc + cf - 1])):]
                
                if burst_size_command_last_frame == raw_command[-1]:
                    if init_command in self.l1_cache.keys():
                        burst_size_request = 'STPX D:' + burst_size_command + ",R:"  + self.l1_cache[init_command]
                    else:
                        burst_size_request = 'STPX D:' + burst_size_command
                else:
                    burst_size_request = 'STPX D:' + burst_size_command + ",R:1"
                    
                # Ensure time gap between frames according to FlowControl
                tc = time.time()  # current time
                self.screenRefreshTime += ST /1000.
                if (tc - tb) * 1000. < ST:
                    target_time = time.clock() + (ST / 1000. - (tc - tb))
                    while time.clock() < target_time:
                        pass
                tb = tc

                frsp = self.send_raw(burst_size_request)
                Fc = Fc + cf
                cf = 0
                if burst_size_command_last_frame == raw_command[-1]:
                    for s in frsp.split('\n'):
                        if s.strip()[:4] == "STPX":  # echo cancelation
                            continue
                        else:
                            responses.append(s)
                            continue

        result = ""
        noerrors = True
        cFrame = 0  # frame counter
        nBytes = 0  # number bytes in response
        nFrames = 0  # numer frames in response

        if len (responses) == 0:  # no data in response
            return ""

        if responses[0][:1] == '0':  # single frame (sf)
            nBytes = int(responses[0][1:2], 16)
            nFrames = 1
            result = responses[0][2:2 + nBytes * 2]

        elif responses[0][:1] == '1':  # first frame (ff)
            nBytes = int(responses[0][1:4], 16)
            nBytes = nBytes - 6  # we assume that it should be more then 7
            nFrames = 1 + nBytes / 7 + bool(nBytes % 7)
            cFrame = 1

            result = responses[0][4:16]

            while cFrame < nFrames:

                # analyse response
                nodataflag = False
                for s in responses:

                    if 'NO DATA' in s:
                        nodataflag = True
                        break

                    s = s.strip().replace(' ', '')
                    if len(s) == 0:  # empty string
                        continue

                    if all(c in string.hexdigits for c in s):  # some data
                        # responses.append(s)
                        if s[:1] == '2':  # consecutive frames (cf)
                            tmp_fn = int(s[1:2], 16)
                            if tmp_fn != (cFrame % 16):  # wrong response (frame lost)
                                self.error_frame += 1
                                noerrors = False
                                continue
                            cFrame += 1
                            result += s[2:16]
                        continue

                if nodataflag:
                    break

        else:  # wrong response (first frame omitted)
            self.error_frame += 1
            noerrors = False
        
        # Check for negative
        if result[:2] == '7F': noerrors = False

        # populate L1 cache
        if noerrors and init_command[:2] in AllowedList:
            self.l1_cache[init_command] = str(nFrames)

        if noerrors and len(result) / 2 >= nBytes:
            # split by bytes and return
            result = ' '.join(a + b for a, b in zip(result[::2], result[1::2]))
            return result
        else:
            # check for negative response (repeat the same as in cmd())
            # debug
            # print "Size error: ", result
            if result[:2] == '7F' and result[4:6] in negrsp.keys():
                if self.vf != 0:
                    tmstr = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    self.vf.write(
                        tmstr + ";" + dnat[self.currentaddress] + ";" + command + ";" + result + ";" + negrsp[
                            result[4:6]] + "\n")
                    self.vf.flush()
                return "NR:" + result[4:6] + ':' + negrsp[result[4:6]]
            else:
                return "WRONG RESPONSE"

    def send_can_cfc0(self, command):
        
        command = command.strip ().replace (' ', '').upper ()

        if len(command) == 0:
            return
        if len (command) % 2 != 0:
            return "ODD ERROR"
        if not all (c in string.hexdigits for c in command):
            return "HEX ERROR"
        
        # do framing
        raw_command = []
        cmd_len = len (command) / 2
        if cmd_len < 8:  # single frame
            raw_command.append (("%0.2X" % cmd_len) + command)
        else:
            # first frame
            raw_command.append ("1" + ("%0.3X" % cmd_len)[-3:] + command[:12])
            command = command[12:]
            # consecutive frames
            frame_number = 1
            while len (command):
                raw_command.append ("2" + ("%X" % frame_number)[-1:] + command[:14])
                frame_number = frame_number + 1
                command = command[14:]
        
        responses = []
        
        # send frames
        BS = 1  # Burst Size
        ST = 0  # Frame Interval
        Fc = 0  # Current frame
        Fn = len (raw_command)  # Number of frames

        if Fn > 1 or len(raw_command[0])>15: # set elm timeout to 300ms for first response
            # corrected timeout  RT * 1000ms / 4ms / 2 (on a half of RT)
            corr_tout = int( 75 - (self.response_time * 125) )
            if corr_tout > 0x20:
                cmdTxt = 'ATST' + hex(corr_tout)[-2:].zfill(2)
                self.send_raw(cmdTxt)
            else: # it seems too long roundtrip
                self.send_raw('ATST20')

        while Fc < Fn:

            # enable responses
            frsp = ''
            if not self.ATR1:
                frsp = self.send_raw ('at r1')
                self.ATR1 = True
            
            tb = time.time ()  # time of sending (ff)

            if Fn > 1 and Fc == (Fn-1):  # set elm timeout to maximum for last response on long command
                self.send_raw('ATSTFF')
                self.send_raw('ATAT1')

            if (Fc == 0 or Fc == (Fn-1)) and len(raw_command[Fc])<16:  #first or last frame in command and len<16 (bug in ELM)
                frsp = self.send_raw (raw_command[Fc] + '1')  # we'll get only 1 frame: nr, fc, ff or sf
            else:
                frsp = self.send_raw (raw_command[Fc])

            #print '\nbp1:', raw_command[Fc]

            Fc = Fc + 1

            # analyse response
            # first pass. We have to left only response data frames
            s0 = []
            for s in frsp.upper().split('\n'):

                if s.strip()[:len(raw_command[Fc - 1])] == raw_command[Fc - 1]:  # echo cancellation
                    continue

                s = s.strip().replace(' ', '')
                if len(s) == 0:  # empty string
                    continue

                if all(c in string.hexdigits for c in s):  # some data
                    s0.append(s)

            # second pass. Now we may check if 7Fxx78 is a last or not
            for s in s0:
                if s[:1] == '3':  # FlowControl
                    # extract Burst Size
                    BS = s[2:4]
                    if BS == '': BS = '03'
                    BS = int (BS, 16)

                    # extract Frame Interval
                    ST = s[4:6]
                    if ST == '': ST = 'EF'
                    if ST[:1].upper () == 'F':
                        ST = int (ST[1:2], 16) * 100
                    else:
                        ST = int (ST, 16)
                        # print 'BS:',BS,'ST:',ST
                    break  # go to sending consequent frames
                elif s[:4] == '037F' and s[6:8] == '78': # NR:78
                    if len(s0)>0 and s == s0[-1]: # it should be the last one
                        r = self.waitFrames( 6 )
                        if len(r.strip())>0:
                            responses.append ( r )
                    else:
                        continue  # ignore NR 78 if it is not the last
                else:
                    responses.append (s)
                    continue
            
            # sending consequent frames according to FlowControl
            
            cf = min ({BS - 1, (Fn - Fc) - 1})  # number of frames to send without response
            
            # disable responses
            if cf > 0:
                if self.ATR1:
                    frsp = self.send_raw ('at r0')
                    self.ATR1 = False
            
            while cf > 0:
                cf = cf - 1
                
                # Ensure time gap between frames according to FlowControl
                tc = time.time ()  # current time
                if (tc - tb) * 1000. < ST:
                    time.sleep (ST / 1000. - (tc - tb))
                tb = tc
                
                frsp = self.send_raw (raw_command[Fc])
                Fc = Fc + 1

        #debug
        #print '\nbp8>',responses,'<\n'

        # now we are going to receive data. st or ff should be in responses[0]
        if len (responses) != 1:
            # print "Something went wrong. len responces != 1"
            return "WRONG RESPONSE"
        
        result = ""
        noErrors = True
        cFrame = 0  # frame counter
        nBytes = 0  # number bytes in response
        nFrames = 0  # numer frames in response
        
        if responses[0][:1] == '0':  # single frame (sf)
            nBytes = int (responses[0][1:2], 16)
            nFrames = 1
            result = responses[0][2:2 + nBytes * 2]
        
        elif responses[0][:1] == '1':  # first frame (ff)
            nBytes = int (responses[0][1:4], 16)
            nBytes = nBytes - 6 # we assume that it should be more then 7
            nFrames = 1 + nBytes/7 + bool(nBytes%7)
            cFrame = 1

            result = responses[0][4:16]
            
            # receiving consecutive frames
            #while len (result) / 2 < nBytes:
            while cFrame < nFrames:
                # now we should send ff
                sBS = hex (min ({nFrames - cFrame, MaxBurst}))[2:]
                frsp = self.send_raw ('300' + sBS + '00' + sBS)
                
                # analyse response
                nodataflag = False
                for s in frsp.split ('\n'):
                    
                    if s.strip ()[:len (raw_command[Fc - 1])] == raw_command[Fc - 1]:  # echo cancelation
                        continue
                    
                    if 'NO DATA' in s:
                        nodataflag = True
                        break
                    
                    s = s.strip ().replace (' ', '')
                    if len (s) == 0:  # empty string
                        continue
                    
                    if all (c in string.hexdigits for c in s):  # some data
                        responses.append (s)
                        if s[:1] == '2':  # consecutive frames (cf)
                            tmp_fn = int (s[1:2], 16)
                            if tmp_fn != (cFrame % 16):  # wrong response (frame lost)
                                self.error_frame += 1
                                noErrors = False
                                continue
                            cFrame += 1
                            result += s[2:16]
                        continue
                
                if nodataflag:
                    break
        
        else:  # wrong response (first frame omitted)
            self.error_frame += 1
            noErrors = False

        if len (result) / 2 >= nBytes and noErrors and result[:2] != '7F':
            # split by bytes and return
            result = ' '.join (a + b for a, b in zip (result[::2], result[1::2]))
            return result
        else:
            # check for negative response (repeat the same as in cmd())
            #debug
            #print "Size error: ", result
            if result[:2] == '7F' and result[4:6] in negrsp.keys ():
                if self.vf != 0:
                    tmstr = datetime.now ().strftime ("%H:%M:%S.%f")[:-3]
                    self.vf.write (
                        tmstr + ";" + dnat[self.currentaddress] + ";" + command + ";" + result + ";" + negrsp[
                            result[4:6]] + "\n")
                    self.vf.flush ()
                return "NR:" + result[4:6] + ':' + negrsp[result[4:6]]
            else:
                return "WRONG RESPONSE"
    
    def send_raw(self, command):
        
        command = command.upper ()
        
        tb = time.time ()  # start time
        
        # save command to log
        if self.lf != 0:
            # tm = str(time.time())
            tmstr = datetime.now ().strftime ("%H:%M:%S.%f")[:-3]
            self.lf.write (">[" + tmstr + "]" + command + "\n")
            self.lf.flush ()
        
        # send command
        if not mod_globals.opt_demo:
            self.port.write (str (command + "\r").encode ("utf-8"))  # send command
        
        # receive and parse responce
        while True:
            tc = time.time ()
            if mod_globals.opt_demo:
                break
            self.buff = self.port.expect ('>', self.portTimeout)
            tc = time.time ()
            if (tc - tb) > self.portTimeout and "TIMEOUT" not in self.buff:
                self.buff += "TIMEOUT"
            if "TIMEOUT" in self.buff:
                self.error_timeout += 1
                break
            if command in self.buff:
                break
            elif self.lf != 0:
                tmstr = datetime.now ().strftime ("%H:%M:%S.%f")[:-3]
                self.lf.write ("<[" + tmstr + "]" + self.buff + "(shifted)" + command + "\n")
                self.lf.flush ()
        
        # count errors
        if "?" in self.buff:
            self.error_question += 1
        if "BUFFER FULL" in self.buff:
            self.error_bufferfull += 1
        if "NO DATA" in self.buff:
            self.error_nodata += 1
        if "RX ERROR" in self.buff:
            self.error_rx += 1
        if "CAN ERROR" in self.buff:
            self.error_can += 1

        roundtrip = tc - tb

        self.screenRefreshTime += roundtrip

        self.response_time = ((self.response_time * 9) + roundtrip) / 10

        # save responce to log
        if self.lf != 0:
            # tm = str(time.time())
            self.lf.write ("<[" + str (round (roundtrip, 3)) + "]" + self.buff + "\n")
            self.lf.flush ()
        
        return self.buff
    
    def close_protocol(self):
        self.cmd ("atpc")
    
    def start_session(self, start_session_cmd):
        self.startSession = start_session_cmd
        if len (self.startSession) > 0:
            self.lastinitrsp = self.cmd (self.startSession)
    
    def check_answer(self, ans):
        if '?' in ans:
            self.unsupportedCommands += 1
        else:
            self.supportedCommands += 1
    
    def check_adapter(self):
        if mod_globals.opt_demo:
          return
        if self.unsupportedCommands == 0:
          return
        
        if self.supportedCommands > 0:
            self.lastMessage = '\n\n\tFake adapter !!!\n\n'
        else:
            self.lastMessage = '\n\n\tBroken or unsupported adapter !!!\n\n'
            
            # sys.exit()
    
    def init_can(self):

        if not mod_globals.opt_demo:
          self.port.reinit()
        
        self.currentprotocol = "can"
        self.currentaddress = "7e0"  # do not tuch
        self.startSession = ""
        self.lastCMDtime = 0
        self.l1_cache = {}
        self.notSupportedCommands = {}

        if self.lf != 0:
            tmstr = datetime.now ().strftime ("%x %H:%M:%S.%f")[:-3]
            self.lf.write('#' * 60 + "\n# Init CAN\n" + '#' * 60 + "\n")
            self.lf.flush()

        # reset ELM
        elm_ver = self.cmd("at ws")
        self.check_answer(elm_ver)

        self.check_answer(self.cmd("at e1"))
        self.check_answer(self.cmd("at s0"))
        self.check_answer(self.cmd("at h0"))
        self.check_answer(self.cmd("at l0"))
        self.check_answer(self.cmd("at al"))

        if mod_globals.opt_obdlink and mod_globals.opt_caf:
            self.check_answer(self.cmd("AT CAF1"))
            self.check_answer(self.cmd("STCSEGR 1"))
            self.check_answer(self.cmd("STCSEGT 1"))
        else:
            self.check_answer(self.cmd("at caf0"))
        
        if self.ATCFC0:
            self.check_answer(self.cmd("at cfc0"))
        else:
            self.check_answer(self.cmd("at cfc1"))

        self.lastCMDtime = 0

    def set_can_500(self, addr='XXX'):
        if len(addr)==3:
            if mod_globals.opt_can2 and mod_globals.opt_stn: #for STN with FORD MS-CAN support and pinout changed by soldering 
                self.cmd("STP 53")
                self.cmd("STPBR 500000")
                tmprsp = self.send_raw("0210C0")    #send anything
                if not 'CAN ERROR' in tmprsp: return
            self.cmd("at sp 6")
        else:
            if mod_globals.opt_can2 and mod_globals.opt_stn:
                self.cmd("STP 54")
                self.cmd("STPBR 500000")
                tmprsp = self.send_raw("0210C0")
                if not 'CAN ERROR' in tmprsp: return
            self.cmd("at sp 7")

    def set_can_250(self, addr='XXX'):
        if len(addr)==3:
            if mod_globals.opt_can2 and mod_globals.opt_stn:
                self.cmd("STP 53")
                self.cmd("STPBR 250000")
                tmprsp = self.send_raw("0210C0")
                if not 'CAN ERROR' in tmprsp: return
            self.cmd("at sp 8")
        else:
            if mod_globals.opt_can2 and mod_globals.opt_stn:
                self.cmd("STP 54")
                self.cmd("STPBR 250000")
                tmprsp = self.send_raw("0210C0")
                if not 'CAN ERROR' in tmprsp: return
            self.cmd("at sp 9")

    def set_can_addr(self, addr, ecu):
        
        self.notSupportedCommands = {}
        self.tmpNotSupportedCommands = {}

        if self.currentprotocol == "can" and self.currentaddress == addr:
            return

        if len (ecu['idTx']): dnat[addr] = ecu['idTx']
        if len (ecu['idRx']): snat[addr] = ecu['idRx']
        
        if self.lf != 0:
            self.lf.write ('#' * 60 + "\n#connect to: " + ecu['ecuname'] + " Addr:" + addr + "\n" + '#' * 60 + "\n")
            self.lf.flush ()
        
        self.currentprotocol = "can"
        self.currentaddress = addr
        self.startSession = ""
        self.lastCMDtime = 0
        self.l1_cache = {}
        self.clear_cache()

        if addr in dnat.keys():
            TXa = dnat[addr]
        else:
            TXa = 'undefined'

        if addr in snat.keys():
            RXa = snat[addr]
        else:
            RXa = 'undefined'

        if len(TXa)==8: # 29bit CANId
            self.check_answer(self.cmd("at cp " + TXa[:2]))
            self.check_answer(self.cmd("at sh " + TXa[2:]))
        else:
            self.check_answer (self.cmd ("at sh " + TXa))

        self.check_answer (self.cmd ("at fc sh " + TXa))
        self.check_answer (self.cmd ("at fc sd 30 00 00"))  # status BS STmin
        self.check_answer (self.cmd ("at fc sm 1"))
        self.check_answer (self.cmd ("at st ff"))  # reset adaptive timing step 1
        self.check_answer (self.cmd ("at at 0"))  # reset adaptive timing step 2
        
        # some models of cars may have different CAN buses
        if 'brp' in ecu.keys () and '1' in ecu['brp'] and '0' in ecu['brp']:  # double brp
            if self.lf != 0:
                self.lf.write ('#' * 60 + "\n#    Double BRP, try CAN250 and then CAN500\n" + '#' * 60 + "\n")
                self.lf.flush ()
            self.set_can_250( TXa )
            tmprsp = self.send_raw ("0210C0")  # send any command
            if 'CAN ERROR' in tmprsp:  # not 250!
                ecu['brp'] = '0'  # brp = 0
                self.set_can_500( TXa )
            else:  # 250!
                ecu['brp'] = '1'  # brp = 1
        else:  # not double brp
            if 'brp' in ecu.keys () and '1' in ecu['brp']:
                self.set_can_250( TXa )
            else:
                self.set_can_500( TXa )
        
        self.check_answer (self.cmd ("at at 1"))  # reset adaptive timing step 3
        self.check_answer (self.cmd ("at cra " + RXa))

        if mod_globals.opt_obdlink and mod_globals.opt_caf:
            self.check_answer (self.cmd ("STCFCPA " + TXa + ", " + RXa))

        self.check_adapter ()
    
    def init_iso(self):

        if not mod_globals.opt_demo:
          self.port.reinit()

        self.currentprotocol = "iso"
        self.currentsubprotocol = ""
        self.currentaddress = ""
        self.startSession = ""
        self.lastCMDtime = 0
        self.lastinitrsp = ""
        self.notSupportedCommands = {}

        if self.lf != 0:
            tmstr = datetime.now ().strftime ("%x %H:%M:%S.%f")[:-3]
            self.lf.write ('#' * 60 + "\n#[" + tmstr + "] Init ISO\n" + '#' * 60 + "\n")
            self.lf.flush ()
        self.check_answer (self.cmd ("at ws"))
        self.check_answer (self.cmd ("at e1"))
        self.check_answer (self.cmd ("at s1"))
        self.check_answer (self.cmd ("at l1"))
        self.check_answer (self.cmd ("at d1"))
    
    def set_iso_addr(self, addr, ecu):
        
        self.notSupportedCommands = {}
        self.tmpNotSupportedCommands = {}

        if self.currentprotocol == "iso" and self.currentaddress == addr and self.currentsubprotocol == ecu['protocol']:
            return

        if self.lf != 0:
            self.lf.write ('#' * 60 + "\n#connect to: " + ecu['ecuname'] + " Addr:" + addr + " Protocol:" + ecu[
                'protocol'] + "\n" + '#' * 60 + "\n")
            self.lf.flush ()

        if self.currentprotocol == "iso":
            self.check_answer(self.cmd("82"))  # close previous session

        self.currentprotocol = "iso"
        self.currentsubprotocol = ecu['protocol']
        self.currentaddress = addr
        self.startSession = ""
        self.lastCMDtime = 0
        self.lastinitrsp = ""
        self.clear_cache()

        self.check_answer (self.cmd ("at sh 81 " + addr + " f1"))  # set address
        self.check_answer (self.cmd ("at sw 96"))  # wakeup message period 3 seconds
        self.check_answer (self.cmd ("at wm 81 " + addr + " f1 3E"))  # set wakeup message
        # self.check_answer(self.cmd("at wm 82 "+addr+" f1 3E01"))       #set wakeup message
        self.check_answer (self.cmd ("at ib10"))  # baud rate 10400
        self.check_answer (self.cmd ("at st ff"))  # set timeout to 1 second
        self.check_answer (self.cmd ("at at 0"))  # disable adaptive timing
        
        if 'PRNA2000' in ecu['protocol'].upper () or mod_globals.opt_si:
            self.cmd ("at sp 4")  # slow init mode 4
            if len (ecu['slowInit']) > 0:
                self.cmd ("at iia " + ecu['slowInit'])  # address for slow init
            rsp = self.lastinitrsp = self.cmd ("at si")  # for slow init mode 4
            # rsp = self.cmd("81")
            if 'ERROR' in rsp and len (ecu['fastInit']) > 0:
                ecu['protocol'] = ''
                if self.lf != 0:
                    self.lf.write ('### Try fast init\n')
                    self.lf.flush ()
                    
                    # if 'PRNA2000' not in ecu['protocol'].upper() :
        if 'OK' not in self.lastinitrsp:
            self.cmd ("at sp 5")  # fast init mode 5
            self.lastinitrsp = self.cmd ("at fi")  # perform fast init mode 5
            # self.lastinitrsp = self.cmd("81")         #init bus
        
        self.check_answer (self.cmd ("at at 1"))  # enable adaptive timing

        self.check_answer(self.cmd("81"))  # start session

        self.check_adapter ()

    #check what is the maximum number of parameters that module can handle in one request
    def checkModulePerformaceLevel(self, dataids):
        performanceLevels = [3, 2]

        for level in performanceLevels:
            isLevelAccepted = self.checkPerformaceLevel(level, dataids)
            if isLevelAccepted: 
                break

        if self.performanceModeLevel == 3 and mod_globals.opt_obdlink:
            for level in reversed(range(4,100)): #26 - 1 = 25  parameters per page
                isLevelAccepted = self.checkPerformaceLevel(level, dataids)
                if isLevelAccepted: 
                    return

    def checkPerformaceLevel(self, level, dataids):
        if len(dataids) >= level:
            paramToSend = ''

            if level <= 3: # 3 dataids max can be send in single frame
                frameLength = '{:02X}'.format(1 + level * 2)
                for lvl in range(level):
                    paramToSend += dataids.keys()[lvl]
                
                cmd = '22' + paramToSend
                
                resp = self.cmd(cmd).replace(" ", "")   #check response length first
                if not all (c in string.hexdigits for c in resp):
                    return False 
                
                if self.l1_cache.get(cmd, ""):
                    if mod_globals.opt_caf:
                        resp = self.send_raw(cmd + self.l1_cache.get(cmd)) # get all frames, not only first one
                    else:                                                  # prevents from triggering false error_frame error
                        resp = self.send_raw(frameLength + cmd + self.l1_cache.get(cmd))
                    for s in resp.split('\n'):
                        if s.strip().startswith("037F") or "?" in s:
                            return False 
            
            else: # send multiframe command for more than 3 dataids
                # Some modules can return NO DATA if multi frame command is sent after some no activity time
                # Sending anything before main command usually helps that command to be accepted
                self.send_cmd ("22" + dataids.keys()[0] + "1")  

                for lvl in range(level):
                    resp = self.request("22" + dataids.keys()[lvl])
                    if any(s in resp for s in ['?', 'NR']):
                        continue
                    paramToSend += dataids.keys()[lvl]
                cmd = '22' + paramToSend
                resp = self.send_cmd(cmd)
            if any(s in resp for s in ['?', 'NR']):
                return False
        
        self.performanceModeLevel = level
        return True

    def getRefreshRate(self):
        refreshRate = 0

        if not self.screenRefreshTime:
            return refreshRate
        
        refreshRate = 1 / self.screenRefreshTime
        self.screenRefreshTime = 0
        return refreshRate
    
    def reset_elm(self):
        self.cmd ("at z")
