#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import pickle

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

import mod_globals
import mod_ecu
import mod_scan_ecus
import mod_elm

from mod_ddt_ecu      import DDTECU
from mod_ddt_screen   import DDTScreen
from mod_utils        import clearScreen

import xml.etree.ElementTree as et

from   xml.dom.minidom import parse
import xml.dom.minidom

mod_globals.os = os.name
 
if mod_globals.os == 'nt':
  import pip
  
  try:
    import serial
  except ImportError:
    pip.main(['install','pyserial'])

  try:
    import colorama
  except ImportError:
    pip.main(['install','colorama'])
    try:
      import colorama
    except ImportError:
      print "\n\n\n\t\t\tGive me access to the Internet for download modules\n\n\n"
      sys.exit()
  colorama.init()
else:
  # let's try android
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
  try:
    import serial
    from serial.tools  import list_ports
    #import ply
  except ImportError:
    print "\n\n\n\tPleas install additional modules"
    print "\t\t>sudo easy_install pyserial"
    #print "\t\t>sudo easy_install ply"
    sys.exit()

from mod_elm       import ELM
from mod_optfile   import *
from mod_utils     import *

class DDT():

  #elm     = None    #elm class
  decu    = None    #ddt ecu
  cecu    = None    #chosen ecu
  #ecuscr  = None    #ecu screen

  def __init__(self, elm, cecu, langmap = {}):
    self.elm     = elm
    self.cecu    = cecu
    
    clearScreen()
    print "Starting DDT process"
    
    #make or load ddt ecu 
    decucashfile = "./cache/ddt_"+cecu['ModelId']+".p"

    if os.path.isfile(decucashfile) and mod_globals.opt_ddtxml=='': #if cache exists and no xml defined
      self.decu = pickle.load( open( decucashfile, "rb" ) )            #load it
    else:                                                           #else
      self.decu = DDTECU(self.cecu)                                    #init class
      self.decu.setELM(self.elm)                                       #define ELM for it
      self.decu.scanECU()                                              #scan and loading original data for chosen ECU
      self.decu.setELM( None )                                         #clear elm before serialization
      if len(self.decu.ecufname)>0:
        pickle.dump( self.decu, open( decucashfile, "wb" ) )        #and save cache
      
    self.decu.setELM(self.elm)                               #re-define ELM
    self.decu.setLangMap(langmap)

    if len(self.decu.ecufname)==0:
      return

    if '/' in self.decu.ecufname:
      xfn = self.decu.ecufname[:-4].split('/')[-1]
    else:
      xfn = self.decu.ecufname[:-4].split ('\\')[-1]

    dumpIs = False
    for root, dirs, files in os.walk("./dumps"):
      for f in files:
        if (xfn+'.') in f:
          dumpIs = True
          break
          
    if not mod_globals.opt_demo and not dumpIs and not mod_globals.opt_dump:
      answer = raw_input ('Save dump ? [y/n] : ')
      if 'N' in answer.upper():
        dumpIs = True

    if mod_globals.opt_demo:
      print "Loading dump"
      self.decu.loadDump()
    elif mod_globals.opt_dump or not dumpIs:
      print "Saving dump"
      self.decu.saveDump()

    #Load XML
    if not os.path.isfile(self.decu.ecufname):
      print "No such file: ", self.decu.ecufname
      return None

    ns = {'ns0': 'http://www-diag.renault.com/2002/ECU',
          'ns1': 'http://www-diag.renault.com/2002/screens'}

    tree = et.parse (self.decu.ecufname)
    xdoc = tree.getroot ()

    # Show screen
    print "Show screen"
    scr = DDTScreen(self.decu.ecufname, xdoc, self.decu)
    
    del(scr)
    del(self.decu)
    
def __del__(self):
  #debug
  #print sys.getrefcount(self.elm)
  del self.elm
  del self.cecu

def optParser():
  '''Parsing of command line parameters. User should define at least com port name'''
  
  import argparse

  parser = argparse.ArgumentParser(
    #usage = "%prog -p <port> [options]",
    version="mod_ddt Version 0.9.n",
    description = "mod_ddt - python program for diagnostic Renault cars"
  )
  
  parser.add_argument('-p',
      help="ELM327 com port name",
      dest="port",
      default="")

  parser.add_argument("-r",
      help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
      dest="rate",
      default="38400",)

  parser.add_argument("-a",
      help="functional address of ecu",
      dest="ecuAddr",
      default="")

  parser.add_argument("-i",
      help="interface protocol [can250|250|can500|500|kwpS|S|kwpF|F]",
      dest="protocol",
      default='500')

  parser.add_argument("-L",
      help="language option {RU[default],GB,FR,IT,...}",
      dest="lang",
      default="RU")

  parser.add_argument("--cfc",
      help="turn off automatic FC and do it by script",
      dest="cfc",
      default=False,
      action="store_true")

  parser.add_argument("--n1c",
      help="turn off L1 cache",
      dest="n1c",
      default=False,
      action="store_true")

  parser.add_argument("--log",
      help="log file name",
      dest="logfile",
      default="")

  parser.add_argument("--xml",
      help="xml file name",
      dest="ddtxml",
      default="")

  parser.add_argument("--demo",
      help="for debuging purpose. Work without car and ELM",
      dest="demo",
      default=False,
      action="store_true")

  parser.add_argument("--dump",
      help="dump responces from all 21xx and 22xxxx requests",
      dest="dump",
      default=True,
      action="store_true")

  parser.add_argument("--exp",
      help="swith to Expert mode (allow to use buttons in DDT)",
      dest="exp",
      default=False,
      action="store_true")


  options = parser.parse_args()
  
  if not options.port and mod_globals.os != 'android':
    parser.print_help()
    iterator = sorted(list(list_ports.comports()))
    print ""
    print "Available COM ports:"
    for port, desc, hwid in iterator:
      print "%-30s \n\tdesc: %s \n\thwid: %s" % (port,desc.decode("windows-1251"),hwid)
    print ""
    exit(2)
  else:
    mod_globals.opt_port      = options.port
    mod_globals.opt_ecuAddr   = options.ecuAddr.upper()
    mod_globals.opt_rate      = int(options.rate)
    mod_globals.opt_lang      = options.lang
    mod_globals.opt_log       = options.logfile
    mod_globals.opt_demo      = options.demo
    mod_globals.opt_dump      = options.dump
    mod_globals.opt_exp       = options.exp
    mod_globals.opt_cfc0      = options.cfc
    mod_globals.opt_n1c       = options.n1c
    mod_globals.opt_ddtxml    = options.ddtxml
    if   'S' in options.protocol.upper():
      mod_globals.opt_protocol  = 'S'
    elif 'F' in options.protocol.upper():
      mod_globals.opt_protocol  = 'F'
    elif '250' in options.protocol:
      mod_globals.opt_protocol  = '250'
    elif '500' in options.protocol:
      mod_globals.opt_protocol  = '500'
    else:
      mod_globals.opt_protocol  = '500'
      
def get_addr_from_xml( xmlfile ):
  
  if '/ecus/' not in xmlfile:
    xmlfile = '../ecus/'+xmlfile
      
  #Load XML
  xdom = xml.dom.minidom.parse(xmlfile)
  xdoc = xdom.documentElement
  if not xdoc:
    print "No such file:", xmlfile
    return
  
  faddr = ''
  cans = xdoc.getElementsByTagName("CAN")
  if cans:
    for can in cans:
      sendid = can.getElementsByTagName("SendId")
      if sendid:
        for sid in sendid:
          canid = sid.getElementsByTagName("CANId")
          if canid:
            for cid in canid:
              send_can_addr = cid.getAttribute("Value")
              if len(send_can_addr)>0:
                sca = hex(int(send_can_addr))[2:].upper().zfill(3)
                for k in mod_elm.dnat.keys():
                  if sca==mod_elm.dnat[k]:
                    faddr = k

  #if faddr=='':
  #    faddr = raw_input('Please define functional address : ')
  
  return faddr

def main():
  '''Main function'''

  optParser()
  
  print 'Opening ELM'
  elm = ELM( mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log )

  #change serial port baud rate 
  if mod_globals.opt_speed<mod_globals.opt_rate and not mod_globals.opt_demo:
    elm.port.soft_boudrate( mod_globals.opt_rate )
     
  print "Loading language "
  sys.stdout.flush()
  
                                         #loading language data
  lang = optfile("../Location/DiagOnCan_"+mod_globals.opt_lang+".bqm",True)
  mod_globals.language_dict = lang.dict
  print "Done"
  
  #check if address or xml defined
  
  if mod_globals.opt_ecuAddr=='' and mod_globals.opt_ddtxml!='':
    mod_globals.opt_ecuAddr = get_addr_from_xml( mod_globals.opt_ddtxml )

  #if mod_globals.opt_ddtxml=='' and (mod_globals.opt_ecuAddr=='' or mod_globals.opt_ecuAddr not in mod_ecu.F2A.values()):
  if mod_globals.opt_ecuAddr == '' or mod_globals.opt_ecuAddr not in mod_ecu.F2A.values ():
    #ask to choose famile
    fmls = []
    for f in sorted(mod_ecu.F2A.keys()):
      f = str(int(f))
      if mod_scan_ecus.families[f] in mod_globals.language_dict.keys():
        x = f
        if len(x)==1: x = '0'+ x
        if x in mod_ecu.F2A.keys() and mod_ecu.F2A[x] in mod_elm.dnat.keys():
          fmls.append( f+":"+mod_globals.language_dict[mod_scan_ecus.families[f]] )
    ch = ChoiceLong(fmls, "Choose ECU type :")
    family = ch[0].split(':')[0]
    if len(family)==1: family = '0'+ family
    if family in mod_ecu.F2A.keys():
      mod_globals.opt_ecuAddr = mod_ecu.F2A[family]
    else:
      print "ERROR : Unknown family!!!!"
      sys.exit()

  addr = mod_globals.opt_ecuAddr
  #if addr=='' and mod_globals.opt_ddtxml!='':
  #  addr = get_addr_from_xml( mod_globals.opt_ddtxml )

  if 'S' in mod_globals.opt_protocol:
    # SlowInit KWP
    ecudata = { 'pin':'iso', 'slowInit':addr, 'fastInit':addr, 'ecuname': 'ddt_unknown', 'idTx':'', 'idRx':'', 'ModelId':addr, 'protocol':'KWP_Slow' }
    mod_globals.opt_si = True
    elm.init_iso()
    elm.set_iso_addr( addr, ecudata )
  elif 'F' in mod_globals.opt_protocol:
    # FastInitKWP
    ecudata = { 'pin':'iso', 'slowInit':addr, 'fastInit':addr, 'ecuname': 'ddt_unknown', 'idTx':'', 'idRx':'', 'ModelId':addr, 'protocol':'KWP_Fast' }
    mod_globals.opt_si = False
    elm.init_iso()
    elm.set_iso_addr( addr, ecudata )
  elif '250' in mod_globals.opt_protocol:
    # CAN 250
    ecudata = { 'pin':'can', 'slowInit':'', 'fastInit':'', 'brp':'1', 'ecuname': 'ddt_unknown', 'idTx':'', 'idRx':'', 'ModelId':addr, 'protocol':'CAN_250' }
    elm.init_can()
    elm.set_can_addr( addr, ecudata )
  elif '500' in mod_globals.opt_protocol:
    # CAN 500
    ecudata = { 'pin':'can', 'slowInit':'', 'fastInit':'', 'brp':'0', 'ecuname': 'ddt_unknown', 'idTx':'', 'idRx':'', 'ModelId':addr, 'protocol':'CAN_500' }
    elm.init_can()
    elm.set_can_addr( addr, ecudata )
  else:
    print "ERROR : Unknown protocol!!!!"
    sys.exit()
  
  ecudata['dst']=addr
    
  elm.start_session( '10C0' )
  
  ddt = DDT(elm, ecudata)

  print "Done"  

if __name__ == '__main__':
  main()  
