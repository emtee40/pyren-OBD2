#!/usr/bin/env python

import sys, os
import mod_globals
import mod_db_manager

mod_globals.os = os.name

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

import pickle

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
    
import mod_utils
import mod_ddt_utils

from mod_elm       import ELM
from mod_scan_ecus import ScanEcus
from mod_ecu       import ECU
from mod_optfile   import *
from mod_utils     import *


def optParser():
  '''Parsing of command line parameters. User should define at least com port name'''
  
  import argparse

  parser = argparse.ArgumentParser(
    #usage = "%prog -p <port> [options]",
    version="pyRen Version 0.9.q",
    description = "pyRen - python program for diagnostic Renault cars"
  )
  
  parser.add_argument('-p',
      help="ELM327 com port name",
      dest="port",
      default="")

  parser.add_argument("-s",
      help="com port speed configured on ELM {38400[default],57600,115200,230400,500000} DEPRECATED",
      dest="speed",
      default="38400")

  parser.add_argument("-r",
      help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
      dest="rate",
      default="38400",)

  parser.add_argument("-L",
      help="language option {RU[default],GB,FR,IT,...}",
      dest="lang",
      default="RU")

  parser.add_argument("--sd",
      help="separate doc files",
      dest="sd",
      default=False)

  parser.add_argument("-m",
      help="number of car model",
      dest="car",
      default=0,
      type=int)

  parser.add_argument("-vv", "--verbose",
      help="show parameter explanations",
      dest="verbose",
      default=False,
      action="store_true")

  parser.add_argument("-e",
      help="index of ECU, or comma separeted list for DEMO MODE",
      dest="ecuid",
      default="")

  parser.add_argument("--si",
      help="try SlowInit first",
      dest="si",
      default=False,
      action="store_true")

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

  parser.add_argument("--csv",
      help="save data in csv format",
      dest="csv",
      default=False,
      action="store_true")

  parser.add_argument("--csv_only",
      help="data doesnt show on screen for speed up",
      dest="csv_only",
      default=False,
      action="store_true")

  parser.add_argument("--csv_human",
      help="data saves to csv in readable format",
      dest="csv_human",
      default=False,
      action="store_true")

  parser.add_argument('--usr_key',
      help="add user events to log",
      dest="usr_key",
      default="")

  parser.add_argument("--log",
      help="log file name",
      dest="logfile",
      default="")

  parser.add_argument("--scan",
      help="scan ECUs even if savedEcus.p file exists",
      dest="scan",
      default=False,
      action="store_true")

  parser.add_argument("--demo",
      help="for debuging purpose. Work without car and ELM",
      dest="demo",
      default=False,
      action="store_true")

  parser.add_argument("--dump",
      help="dump responces from all 21xx and 22xxxx requests",
      dest="dump",
      default=False,
      action="store_true")

  parser.add_argument("--dev",
      help="swith to Development Session for commands from DevList, you should define alternative command for opening the session, like a 1086",
      dest="dev",
      default='')

  parser.add_argument("--exp",
      help="swith to Expert mode (allow to use buttons in DDT)",
      dest="exp",
      default=False,
      action="store_true")

  parser.add_argument("--can2",
      help="CAN network connected to pin 13 and pin 12",
      dest="can2",
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
    mod_globals.opt_ecuid     = options.ecuid
    mod_globals.opt_speed     = int(options.speed)
    mod_globals.opt_rate      = int(options.rate)
    mod_globals.opt_lang      = options.lang
    mod_globals.opt_car       = options.car
    mod_globals.opt_log       = options.logfile
    mod_globals.opt_demo      = options.demo
    mod_globals.opt_scan      = options.scan
    mod_globals.opt_csv       = options.csv
    mod_globals.opt_csv_only  = options.csv_only
    if mod_globals.opt_csv_only  : mod_globals.opt_csv = True
    mod_globals.opt_csv_human = options.csv_human
    if mod_globals.opt_csv_human : mod_globals.opt_csv = True
    mod_globals.opt_usrkey    = options.usr_key
    mod_globals.opt_verbose   = options.verbose
    mod_globals.opt_si        = options.si
    mod_globals.opt_cfc0      = options.cfc
    mod_globals.opt_n1c       = options.n1c
    mod_globals.opt_exp       = options.exp
    mod_globals.opt_dump      = options.dump
    mod_globals.opt_can2      = options.can2
    mod_globals.opt_sd        = options.sd
    if options.dev=='' or len(options.dev)!=4 or options.dev[0:2]!='10':
      mod_globals.opt_dev       = False
      mod_globals.opt_devses    = '1086'   
    else:
      print "Development MODE"
      mod_globals.opt_dev       = True
      mod_globals.opt_devses    = options.dev   
    
def main():
  '''Main function'''

  optParser()

  mod_utils.chkDirTree()
  mod_db_manager.find_DBs()

  print 'Opening ELM'
  elm = ELM( mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log )

  #change serial port baud rate 
  if mod_globals.opt_speed<mod_globals.opt_rate and not mod_globals.opt_demo:
    elm.port.soft_boudrate( mod_globals.opt_rate )
     
  print 'Loading ECUs list'
  se  = ScanEcus(elm)                    #Prepare list of all ecus

  SEFname = "savedEcus.p"
  if mod_globals.opt_can2:
    SEFname = "savedEcus2.p" 

  if mod_globals.opt_demo and len(mod_globals.opt_ecuid)>0:
    # demo mode with predefined ecu list
    se.read_Uces_file( all = True )    
    se.detectedEcus = []
    for i in mod_globals.opt_ecuid.split(','):
      if  i in se.allecus.keys():
        se.allecus[i]['ecuname']=i
        se.allecus[i]['idf']=se.allecus[i]['ModelId'][2:4]
        if se.allecus[i]['idf'][0]=='0': 
          se.allecus[i]['idf'] = se.allecus[i]['idf'][1]
        se.allecus[i]['pin'] = 'can' 
        se.detectedEcus.append( se.allecus[i] )    
  else:
    if not os.path.isfile(SEFname) or mod_globals.opt_scan: 
      # choosing model 
      se.chooseModel( mod_globals.opt_car )  #choose model of car for doing full scan
    
    # Do this check every time
    se.scanAllEcus()                       #First scan of all ecus
 
  mod_globals.vin = getVIN(se.detectedEcus, elm, getFirst=True)

  print "Loading language "
  sys.stdout.flush()
  # loading language data
  lang = optfile("Location/DiagOnCAN_" + mod_globals.opt_lang + ".bqm", True)
  mod_globals.language_dict = lang.dict
  print "Done"

  mod_ddt_utils.searchddtroot()

  #check if DDT present
  if os.path.exists(os.path.join(mod_globals.ddtroot, '/ecus')) and mod_globals.os != 'android':
    mod_globals.opt_ddt = True  

  while( 1 ):
    clearScreen()
    choosen_ecu = se.chooseECU( mod_globals.opt_ecuid )   # choose ECU among detected
    mod_globals.opt_ecuid = ''
    if choosen_ecu==-1:
      continue
    
    ecucashfile = "./cache/"+choosen_ecu['ModelId']+'_'+mod_globals.opt_lang+".p"
    
    if os.path.isfile(ecucashfile):                         #if cache exists
      ecu = pickle.load( open( ecucashfile, "rb" ) )        #load it
    else:                                                   #else
      ecu = ECU(choosen_ecu, lang.dict )                    #loading original data for chosen ECU
      pickle.dump( ecu, open( ecucashfile, "wb" ) )         #and save cache
    
    ecu.initELM( elm )                                      #init ELM for chosen ECU 
    
    if mod_globals.opt_demo:
      print "Loading dump"
      ecu.loadDump()
    elif mod_globals.opt_dump:
      print "Saving dump"
      ecu.saveDump()
      
    ecu.show_screens()                                      #show ECU screens

if __name__ == '__main__':  
  main()
  
