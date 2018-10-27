#!/usr/bin/env python
'''

Version: 180402
This scenarium may enable/disable AndroidAuto and CarPlay

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:SCEN_ECRI_GENERIQUE2#SCEN_ECRI_GENERIQUE2_<eid>.xml

'run' procedure will be executed by pyren script
 
'''

import os
import sys
import re
import time

import mod_globals
import mod_utils
import mod_ecu
from   mod_utils     import pyren_encode
from   mod_utils     import clearScreen

import xml.dom.minidom

def run( elm, ecu, command, data ):
  '''
  MAIN function of scenarium
  
  Parameters:
      elm     - refernce to adapter class
      ecu     - reference to ecu class
      command - refernce to the command this scenarium belongs to
      data    - name of xml file with parameters from scenarium URL
  '''
  
  clearScreen()
  header =  '['+command.codeMR+'] '+command.label
  
  #
  #     Important information
  #
  clearScreen()
  print pyren_encode(header)
  print
  print 'This scenarium may enable/disable AndroidAuto and CarPlay'
  print
  print '*'*50
  
  #
  #     check if this ECU is supported
  #
  eid = data[-9:-4]
  if eid not in ['11300']:
    print '\n\nThis ECU is unsupported !!!!\n\n'
    ch = raw_input('Press ENTER to exit')
    return
  
  #
  #     read current value
  #
  print 'Reading current value'
  rsp = elm.request("222130",positive='622130', cache=False)
  rsp = rsp.replace(' ','')[:20]
  print "Done:", rsp
  if not rsp.startswith('622130'):
    print 'Got WRONG RESPONSE !!!'
    ch = raw_input('Press ENTER to exit')
    return
  hexVal = int(rsp[8:9],16)
  print '*'*50
  if hexVal & 0x2:
    print 'AndroidAuto   : ON'
  else:
    print 'AndroidAuto   : OFF'
  if hexVal & 0x4:
    print 'CarPlay       : ON'
  else:
    print 'CarPlay       : OFF'
  print '*'*50
  
  #
  #     changing value
  #
  ch = raw_input ('What do you want? <on/off/quit>:')
  if ch.lower () != 'on' and ch.lower () != 'off': return

  if ch.lower () == 'off':
    print 'Swithing OFF !!!'
    hexVal = hexVal & 0x9
  elif ch.lower () == 'on':
    print 'Swithing ON !!!'
    hexVal = hexVal | 0x6
  newcmd = '2E2130'+rsp[6:8]+hex(hexVal)[-1:].upper()+rsp[9:]
  
  #
  #     writing value
  #
  print 'New :',newcmd
  print 'We are ready to change'
  ch = raw_input ('Do you agree? <yes/no/quit>:')
  if ch.lower () != 'yes': return
  rsp = elm.request(newcmd, positive='6E2130', cache=False)
  if not rsp.upper().replace(' ','').startswith('6E2130'):
    print 'RSP :',rsp
    print 'Got ERROR!!!'
    ch = raw_input('Press ENTER to exit')
    return

  #
  #     wait a bit
  #
  time.sleep(2)
  
  #
  #     read new value
  #
  print 'Reading new value'
  rsp = elm.request ("222130", positive='622130', cache=False)
  rsp = rsp.replace (' ', '')[:20]
  print "Done:", rsp
  if not rsp.startswith ('622130'):
    print 'Got WRONG RESPONSE !!!'
    ch = raw_input ('Press ENTER to exit')
    return
  hexVal = int (rsp[8:9], 16)
  print '*' * 50
  if hexVal & 0x2:
    print 'AndroidAuto   : ON'
  else:
    print 'AndroidAuto   : OFF'
  if hexVal & 0x4:
    print 'CarPlay       : ON'
  else:
    print 'CarPlay       : OFF'
  print '*' * 50

  print '\n\n\t DONE'
  print '\n\n You have to reset the device manually '
  print ' by long press on power button\n\n'
  ch = raw_input('Press ENTER to continue')

