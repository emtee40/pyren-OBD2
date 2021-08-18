#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import time
import pickle
import codecs
import string
import threading
import mod_utils
import mod_ddt_utils

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

import pickle

import mod_globals
import mod_db_manager
import mod_elm

from mod_elm       import ELM

from mod_ddt_ecu      import DDTECU
from mod_utils        import clearScreen
from mod_utils        import ChoiceLong
from mod_utils        import KBHit
from mod_utils        import pyren_encode

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

class DDT_MON():

  decu    = None    #ddt ecu
  
  frames = {}   #frame statistic
  datas  = {}   #last data value
  f2r    = {}   #frame to decu.request mapper
  showList = [] #data we will
  
  lt = 0  #last time we showed the screen
  
  screenMode = 0
  framefilter = ''
  
  def __init__(self, elm, xmlfile, outfile, infile ):
    self.elm = elm
    
    clearScreen()
    print "Starting DDT process"

    mod_ddt_utils.searchddtroot()
    
    #make or load ddt ecu 
    decucashfile = "./cache/ddt_"+xmlfile+".p"
    
    if os.path.isfile(decucashfile):                        #if cache exists
      self.decu = pickle.load( open( decucashfile, "rb" ) )    #load it
    else:                                                   #else
      self.decu = DDTECU( None )                               #init class
      self.decu.setELM(self.elm)                               #define ELM for it
      self.decu.loadXml( 'ecus/'+xmlfile )                     #loading original data for chosen ECU
      self.decu.setELM( None )                                 #clear elm before serialization
      if len(self.decu.ecufname)>0:
        pickle.dump( self.decu, open( decucashfile, "wb" ) )   #and save cache
    
    if len(outfile)>0:
      self.saveOutAndExit()
    
    self.showList = []
    self.screenMode = 0
    if len(infile)>0:
      self.loadInFile( infile )
      self.screenMode = 1
      #make elm filter
      elmFilter = []
      for d in self.showList:
        if d in self.decu.req4data.keys():
          fid = self.decu.requests[self.decu.req4data[d]].SentBytes[1:]
          elmFilter.append(fid)
      self.setFilter( elmFilter )
      
    self.decu.setELM(self.elm)                               #re-define ELM
    
    self.frames = {}
    self.datas  = {}
    self.f2r    = {}
    
    for r in self.decu.requests.keys():
      self.f2r[self.decu.requests[r].SentBytes[1:]] = self.decu.requests[r]
    
    #addr = "7A"
    
    if '250' in mod_globals.opt_protocol or self.decu.BaudRate == "250000":
      # CAN 250
      elm.init_can()
      elm.cmd("at sp 8")
    else:
      # CAN 500
      elm.init_can()
      elm.cmd("at sp 6")
    
    self.sendAllow = threading.Event()
    self.sendAllow.clear()
    self.elm.startMonitor( self.parser, self.sendAllow )
    
  def setFilter( self, f ):
    
    if isinstance(f,list):
      bmask   = ['0','1','1','1','1','1','1','1','1','1','1','1']
      filter = list(bin(int(f[0],16))[2:].zfill(12))
      #print f[0],filter
      for fi in f[1:]:
        fl = list(bin(int(fi,16))[2:].zfill(12))
        #print fi, fl
        for i in range(0,12):
          if filter[i]!=fl[i]:
            bmask[i] = '0'
      mask = hex(int(''.join(bmask),2))[2:].zfill(3)
      self.elm.setMonitorFilter( filter, mask )
    elif isinstance(f,str) and all(c in string.hexdigits for c in f) and len(f)<4:
      filter = f+'0'*(3-len(f))
      if   len(f)==1: mask = '700'
      elif len(f)==2: mask = '7F0'
      else:           mask = '7FF'
      self.elm.setMonitorFilter( filter, mask )

  def parser(self, buf ):
    
    global show_loc
    
    if show_loc == None or show_loc.isSet(): 
      self.sendAllow.clear()  
      return
        
    ct = time.time()
    
    for f in buf.split('\n'):
      f = f.strip()
      if len(f)==0: continue
      fid  = f[:3]
      data = f[6:]
      if fid not in self.frames.keys():
        self.frames[fid] = {'FirstSeen':ct, 'LastSeen':ct, 'Count':1, 'Name':'', 'data':'', 'changes':0}
        if fid in self.f2r.keys():
          name = self.f2r[fid].Name
        else:
          name = 'Unknown'
        self.frames[fid]['Name'] = name
        
      self.frames[fid]['LastSeen'] = ct
      self.frames[fid]['Count'] = self.frames[fid]['Count'] + 1
      if len(self.frames[fid]['data']) and self.frames[fid]['data']!=data:
        self.frames[fid]['changes'] = self.frames[fid]['changes'] + 1
      self.frames[fid]['data'] = data

    self.sendAllow.clear()
              
  def saveOutAndExit( self ):
    print "Saving output file:"+outfile+'\n'
    of = codecs.open(outfile,'w',encoding='utf8')
    for d in self.decu.datas.keys():
      d_type = u''
      if len(self.decu.datas[d].List)>0:
        d_type = u';LIST'
      elif self.decu.datas[d].Scaled:
        d_type = u';SCALED;'+self.decu.datas[d].Unit
      of.write(d+d_type+u'\n')
    of.close()
    exit()
  
  def loadInFile( self, infile ):
    print "Loading show list:"+infile+'\n'
    lf = codecs.open(infile,'rt',encoding='utf8')
    lff = lf.read()
    self.showList = []
    for l in lff.split('\n'):
      l = l.strip()
      if len(l)==0: continue
      self.showList.append( l.split(';')[0] )
  
  def showData( self, ct ):
    
    if self.screenMode==0:  #frame monitor mode
      if len(self.framefilter)==3 and self.framefilter in self.frames.keys():
        fid = self.framefilter
        if self.frames[fid]['Name'] != 'Unknown':
          for d in self.f2r[fid].ReceivedDI.values():
            val = self.decu.getValue(d.Name, False, self.f2r[fid], self.frames[fid]['data'])
            self.datas[d.Name] = val
          
      clearScreen()
      #if self.screenMode == '' and len(self.frames.keys()):
      if '<' not in self.framefilter and len(self.framefilter)<4:
        for l in sorted(self.frames.keys()):
          if not l.startswith(self.framefilter): continue

          #debug
          #if self.frames[l]['changes']==0 or self.frames[l]['changes']>10: continue
          
          if self.frames[l]['Name'] != 'Unknown':
            ost = pyren_encode('%s : %-30s  #%d:%d' % (l, self.frames[l]['Name'],
                                                       self.frames[l]['Count'], self.frames[l]['changes']))
          else:
            ost = pyren_encode('%s : %-30s  #%d:%d' % (l, self.frames[l]['data'],
                                                       self.frames[l]['Count'], self.frames[l]['changes']))
          print ost
      #if len(self.framefilter)==3 and self.framefilter in self.frames.keys():
      if len(self.framefilter)==3 and self.framefilter in self.f2r.keys():
        print '*'*50
        for l in self.f2r[self.framefilter].ReceivedDI.values():
          ost = pyren_encode('%-50s %s' % (l.Name, self.datas[l.Name]))
          print ost
      print 'Frame filter (Q for exit, R for reset counter):', self.framefilter,
      sys.stdout.flush()
      return
    
    if self.screenMode==1:  # show list mode
      for d in self.showList:
        if d in self.decu.req4data.keys():
          fid = self.decu.requests[self.decu.req4data[d]].SentBytes[1:]
          if fid in self.f2r.keys() and fid in self.frames.keys():
            val = self.decu.getValue(d, False, self.f2r[fid], self.frames[fid]['data'])
          else:
            val = mod_globals.none_val
          self.datas[d] = val
      
      clearScreen()
      
      for d in self.showList:
        if d in self.datas.keys():
          ost = pyren_encode('%-50s %s' % (d, self.datas[d]))
          print ost

candef = ''
outfile = ''
infile = ''
show_loc = None

def optParser():
  '''Parsing of command line parameters. User should define at least com port name'''
  
  import argparse

  global candef
  global outfile
  global infile
  
  parser = argparse.ArgumentParser(
    #usage = "%prog -p <port> [options]",
    version="bus_monitor Version 0.1",
    description = "bus_monitor - python program for diagnostic Renault cars"
  )
  
  parser.add_argument('-p',
      help="ELM327 com port name",
      dest="port",
      default="")

  parser.add_argument("-r",
      help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
      dest="rate",
      default="38400",)

  parser.add_argument("-i",
      help="interface protocol [250|500]",
      dest="protocol",
      default='UnDef')

  parser.add_argument("-a",
      help="filter for canId",
      dest="ecuAddr",
      default="")

  parser.add_argument("-x",
      help="xml file with frames defenition",
      dest="xmlfile",
      default="")

  parser.add_argument("-o",
      help="output file for saving parameters list",
      dest="outfile",
      default="")

  parser.add_argument("-f",
      help="file with selected parameters list",
      dest="infile",
      default="")

  parser.add_argument("--log",
      help="log file name",
      dest="logfile",
      default="")

  parser.add_argument("-L",
      help="language option {RU[default],GB,FR,IT,...}",
      dest="lang",
      default="RU")

  parser.add_argument("--demo",
      help="for debuging purpose. Work without car and ELM",
      dest="demo",
      default=False,
      action="store_true")

  options = parser.parse_args()
  
  if options.outfile=='' and not options.port and mod_globals.os != 'android':
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
    mod_globals.opt_rate      = int(options.rate)
    mod_globals.opt_log       = options.logfile
    mod_globals.opt_ecuAddr   = options.ecuAddr.upper()
    mod_globals.opt_demo      = options.demo
    if '250' in options.protocol:
      mod_globals.opt_protocol  = '250'
    elif '500' in options.protocol:
      mod_globals.opt_protocol  = '500'
    else:
      mod_globals.opt_protocol  = 'UnDef'
    candef = options.xmlfile
    outfile = options.outfile
    infile = options.infile
    mod_globals.opt_exp       = True

def chooseXml():

  import projects
  
  p_list = projects.projects.split('\n')
  menu = []
  for pr in p_list:
    pr = pr.strip()
    if len(pr)<2: continue
    p_params = pr.split(';')
    
    menu.append( "%-6s : %s" % ( p_params[0], p_params[1] ) )

  menu.append("<Exit>")
  choice = ChoiceLong(menu, "Choose :", "")
  if choice[0]=="<Exit>": return
  
  p = p_list[int(choice[1])].split(';')
  
  if len(p)==3:
    return p[2]
  
  menu = []
  for x in p[2:]:
    menu.append(x)
    
  choice = ChoiceLong(menu, "Choose :", choice[0])
  
  return choice[0]
  
  

def main():

  global candef
  global outfile
  global infile
  global show_loc
  
  optParser()

  mod_utils.chkDirTree()
  mod_db_manager.find_DBs()

  if len(candef)==0:
    candef = chooseXml()
  
  elm = None  
  if len(outfile)==0:
    print 'Opening ELM'
    elm = ELM( mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log )

  #change serial port baud rate 
  if mod_globals.opt_speed<mod_globals.opt_rate and not mod_globals.opt_demo:
    elm.port.soft_boudrate( mod_globals.opt_rate )
  
  print candef
  mon = DDT_MON( elm, candef, outfile, infile )

  kb = KBHit()

  lt = ct = time.time()
    
  show_loc = threading.Event()

  if mod_globals.opt_ecuAddr != '':
    mon.framefilter = mod_globals.opt_ecuAddr
    mon.setFilter(mon.framefilter)

  while(1):
    c = ''
    if kb.kbhit():
      c = kb.getch()
      if c=='q' or c=='Q' or c=='\x71' or c=='\x51' :
        print 
        mon.elm.stopMonitor()
        mon.elm.reset_elm()
        break;
      if c == 'r' or c == 'R' or c == '\x72' or c == '\x52':
        for l in mon.frames.keys():
          mon.frames[l]['changes']=0
        continue
      if c>='a' and c<='f':
        c = chr(ord(c) - 32)
      if (c>='0' and c<='9') or (c>='A' and c<='F'):
        mon.framefilter = mon.framefilter + c
        mon.setFilter( mon.framefilter )
      elif c=='\x7f' or c=='\x08':  #backspase
        mon.framefilter = mon.framefilter[:-1]
        mon.setFilter( mon.framefilter )
      else:
        pass
        #mon.framefilter = mon.framefilter + '<' + str(ord(c)) + '>'
    
    time.sleep( 0.03 )
    ct = time.time()
    if (ct-lt)>0.1:
      lt = ct
      show_loc.set()
      mon.showData( ct )
      show_loc.clear()

if __name__ == '__main__':
  main()  
