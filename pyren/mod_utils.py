#!/usr/bin/env python

'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as 
published by the Free Software Foundation, either version 3 of the 
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

import sys
import os
import string
import signal
import atexit
import subprocess
import mod_globals
try:
    import webbrowser
except:
    pass

# Snippet from http://home.wlu.edu/~levys/software/kbhit.py

# Windows
if os.name == 'nt':
    import msvcrt

# Posix (Linux, OS X)
else:
    import termios
    #import atexit
    from select import select
    #from decimal import *

class KBHit:
    
    def __init__(self):
        self.set_getch_term()

    def set_getch_term(self):
        '''Creates a KBHit object that you can call to do various keyboard things.
        '''

        if os.name == 'nt':
            pass
        
        else:
    
            # Save the terminal settings
            self.fd = sys.stdin.fileno()
            self.new_term = termios.tcgetattr(self.fd)
            self.old_term = termios.tcgetattr(self.fd)
    
            # New terminal setting unbuffered
            self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)

            termios.tcsetattr(self.fd, termios.TCSANOW, self.new_term)
            #termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)
    
            # Support normal-terminal reset at exit
            atexit.register(self.set_normal_term)
    
    
    def set_normal_term(self):
        ''' Resets to normal terminal.  On Windows this is a no-op.
        '''
        
        if os.name == 'nt':
            pass
        
        else:
            termios.tcsetattr(self.fd, termios.TCSANOW, self.old_term)
            #termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)


    def getch(self):
        ''' Returns a keyboard character after kbhit() has been called.
            Should not be called in the same program as getarrow().
        '''
        
        s = ''
        
        if os.name == 'nt':
            s = msvcrt.getch().decode('utf-8','ignore')        
        else:
            s = sys.stdin.read(1)

        if len(s)==0 or ord(s)==0 or ord(s)==0xe0:
          if os.name == 'nt':
            s = msvcrt.getch().decode('utf-8','ignore')        
          else:
            s = sys.stdin.read(1)

        return s 
                        

    def getarrow(self):
        ''' Returns an arrow-key code after kbhit() has been called. Codes are
        0 : up
        1 : right
        2 : down
        3 : left
        Should not be called in the same program as getch().
        '''
        
        if os.name == 'nt':
            msvcrt.getch() # skip 0xE0
            c = msvcrt.getch()
            vals = [72, 77, 80, 75]
            
        else:
            c = sys.stdin.read(3)[2]
            vals = [65, 67, 66, 68]
        
        return vals.index(ord(c.decode('utf-8')))
        

    def kbhit(self):
        ''' Returns True if keyboard character was hit, False otherwise.
        '''
        if os.name == 'nt':
            return msvcrt.kbhit()
        
        else:
            try:
                dr,dw,de = select([sys.stdin], [], [], 0)
            except:
                pass
            return dr != []
     
def Choice(list, question ):
  '''Util for make simple choice'''
  d = {};
  c = 1
  exitNumber = 0
  for s in list:
    if s.lower()=='<up>' or s.lower()=='<exit>':
      exitNumber = c
      print "%-2s - %s" % ('Q', pyren_encode(s))
      d['Q']=s
    else:
      print "%-2s - %s" % (c, pyren_encode(s))
      d[str(c)]=s
    c = c+1
  
  while (True):
    try:
      ch = raw_input(question)
    except (KeyboardInterrupt, SystemExit):
        print
        print 
        sys.exit()
    if ch=='q': ch = 'Q'
    if ch=='cmd': mod_globals.opt_cmd = True
    if ch in d.keys():
      return [d[ch],ch]

def ChoiceLong(list, question, header = '' ):
  '''Util for make choice from long list'''
  d = {};
  c = 1
  exitNumber = 0
  page = 0
  page_size = 20

  for s in list:
    if s.lower()=='<up>' or s.lower()=='<exit>':
      exitNumber = c
      d['Q']=s
    else:
      d[str(c)]=s
    c = c+1

  while( 1 ):

    clearScreen()
    #os.system('cls' if os.name == 'nt' else 'clear')      # clear screen
    #print chr(27)+"[2J"+chr(27)+"[;H",                    # clear ANSI screen (thanks colorama for windows)

    if len( header ): print pyren_encode(header)

    c = page*page_size 
    for s in list[page*page_size:(page+1)*page_size]:
      c = c + 1
      if s.lower()=='<up>' or s.lower()=='<exit>':
        print "%-2s - %s" % ('Q', pyren_encode(s))
      else:
        print "%-2s - %s" % (c, pyren_encode(s))

    if len(list)>page_size:
      if page>0:
        print "%-2s - %s" % ('P', '<prev page>')
      if (page+1)*page_size<len(list):
        print "%-2s - %s" % ('N', '<next page>')
      
    while (True):
      try:
        ch = raw_input(question)
      except (KeyboardInterrupt, SystemExit):
        print
        print 
        sys.exit()
      
      if ch=='q': ch = 'Q'
      if ch=='p': ch = 'P'
      if ch=='n': ch = 'N'
      
      if ch=='N' and (page+1)*page_size<len(list):
        page = page + 1
        break
      if ch=='P' and page>0:
        page = page - 1
        break

      if ch=='cmd': mod_globals.opt_cmd = True
      if ch in d.keys():
        return [d[ch],ch]

def ChoiceFromDict(dict, question, showId = True ):
  '''Util for make choice from dictionary'''
  d = {};
  c = 1
  exitNumber = 0
  for k in sorted(dict.keys()):
    s = dict[k]
    if k.lower()=='<up>' or k.lower()=='<exit>':
      exitNumber = c
      print "%s - %s" % ('Q',pyren_encode(s))
      d['Q']=k
    else:
      if showId:
        print "%s - (%s) %s" % (c,pyren_encode(k),pyren_encode(s))
      else:
        print "%s - %s" % (c,pyren_encode(s))      
      d[str(c)]=k
    c = c+1
  
  while (True):
    try:
      ch = raw_input(question)
    except (KeyboardInterrupt, SystemExit):
        print
        print 
        sys.exit()
    if ch=='q': ch = 'Q'
    if ch in d.keys():
      return [d[ch],ch]
      
def pyren_encode( inp ):
  if mod_globals.os == 'android':
    return inp.encode('utf-8', errors='replace')
  else:
    return inp.encode(sys.stdout.encoding, errors='replace')

def pyren_decode( inp ):
  if mod_globals.os == 'android':
    return inp.decode('utf-8', errors='replace')
  else:
    return inp.decode(sys.stdout.encoding, errors='replace')
    
def pyren_decode_i( inp ):
  if mod_globals.os == 'android':
    return inp.decode('utf-8', errors='ignore')
  else:
    return inp.decode(sys.stdout.encoding, errors='ignore')
    
def clearScreen():
  # https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences
  # [2J   - clear entire screen
  # [x;yH - move cursor to x:y
  sys.stdout.write(chr(27)+"[2J"+chr(27)+"[;H")

def upScreen():
  sys.stdout.write(chr(27)+"[;H")
    
def hex_VIN_plus_CRC( VIN, plusCRC=True):
  '''The VIN must be composed of 17 alphanumeric characters apart from "I" and "O"'''
  
  #VIN    ='VF1LM1B0H11111111'
  VIN = VIN.upper()
  hexVIN = ''
  CRC    = 0xFFFF

  for c in VIN:                # for every byte in VIN
    b = ord(c)                 # get ASCII
    hexVIN = hexVIN + hex(b)[2:].upper()
    for i in range( 8 ):       # for every bit
      if ((CRC ^ b) & 0x1):    
        CRC = CRC >> 1
        CRC = CRC ^ 0x8408
        b = b >> 1
      else:
        CRC = CRC >> 1
        b = b >> 1

  # invert
  CRC = CRC ^ 0xFFFF

  # swap bytes
  b1 = (CRC >> 8) & 0xFF
  b2 = CRC & 0xFF
  CRC = ((b2 << 8) | b1) & 0xFFFF

  sCRC = hex( CRC )[2:].upper()
  sCRC = '0'*(4-len(sCRC))+sCRC

  # result
  if plusCRC:
    return hexVIN+sCRC
  else:
    return hexVIN

# Test
if __name__ == "__main__":
    
    kb = KBHit()

    print('Hit any key, or ESC to exit')

    while True:

        if kb.kbhit():
            c = kb.getch()
            if ord(c) == 27: # ESC
                break
            print(c)
             
    kb.set_normal_term()

# Convert ASCII to HEX

def ASCIITOHEX( ATH ):
      
      ATH = ATH.upper()
      hexATH = ''.join("{:02X}".format(ord(c)) for c in ATH)
      
  #Result
      return hexATH

# Convert ch str to int then to Hexadecimal digits

def StringToIntToHex(DEC):

      DEC = int(DEC)
      hDEC = hex(DEC)

   #Result                         
      return hDEC[2:].zfill(2).upper()
      
def loadDumpToELM( ecuname, elm ): 
  ecudump = {}
  dumpname = ''
  
  flist = []
  for root, dirs, files in os.walk("./dumps"):
    for f in files:
      if (ecuname+'.txt') in f:
        flist.append(f)
  
  if len(flist)==0: return
  flist.sort()
  dumpname = os.path.join("./dumps/", flist[-1])
  
  #debug
  print "Loading:", dumpname
  
  df = open(dumpname,'rt')
  lines = df.readlines()
  df.close()
  
  for l in lines:
    l = l.strip().replace('\n','')
    if ':' in l:
      req,rsp = l.split(':')
      ecudump[req] = rsp
  
  elm.setDump( ecudump )

def chkDirTree():
    '''Check direcories'''
    if not os.path.exists('./cache'):
        os.makedirs('./cache')
    if not os.path.exists('./csv'):
        os.makedirs('./csv')
    if not os.path.exists('./logs'):
        os.makedirs('./logs')
    if not os.path.exists('./dumps'):
        os.makedirs('./dumps')
    if not os.path.exists('./macro'):
        os.makedirs('./macro')
    if not os.path.exists('./doc'):
        os.makedirs('./doc')
    if not os.path.exists('../MTCSAVE'):
        os.makedirs('../MTCSAVE')

def getVIN( de, elm, getFirst = False ):
  ''' getting VINs from every ECU     '''
  '''    de  - list of detected ECUs  '''
  '''    elm - reference to ELM class '''
  
  m_vin = set([])
  for e in de:
  
    # init elm
    if mod_globals.opt_demo: #try to load dump
      loadDumpToELM( e['ecuname'], elm )
    else:
      if e['pin'].lower()=='can':
        elm.init_can()
        elm.set_can_addr( e['dst'], e )
      else:
        elm.init_iso()
        elm.set_iso_addr( e['dst'], e )
      elm.start_session( e['startDiagReq'] )
     
    # read VIN
    if e['stdType'].lower()=='uds':
      rsp = elm.request( req = '22F190', positive = '62', cache = False )[9:59]
    else:
      rsp = elm.request( req = '2181', positive = '61', cache = False )[6:56]

    try:
        vin = rsp.replace(' ','').decode('HEX')
    except:
        continue
    
    #debug
    #print e['dst'],' : ', vin

    if len(vin)==17:
      m_vin.add(vin)
      if getFirst:
        return vin
      
  l_vin = m_vin
  
  if os.path.exists('savedVIN.txt'):
    with open('savedVIN.txt') as vinfile:
      vinlines = vinfile.readlines()
      for l in vinlines:
        l = l.strip()
        if '#' in l: continue
        if len(l)==17:
          l_vin.add(l.upper())

  if len(l_vin)==0 and not getFirst:
    print "ERROR!!! Can't find any VIN. Check connection"
    exit()
  
  if len(l_vin)<2:
    try:
        ret = next(iter(l_vin))
    except:
        ret = ''
    return ret
  
  print "\nFound ",len(l_vin), " VINs\n"
    
  choice = Choice(l_vin, "Choose VIN : ")
  
  return choice[0]

def DBG( tag, s ):
    if mod_globals.opt_debug and mod_globals.debug_file!=None:
        mod_globals.debug_file.write( '### ' + tag + '\n')
        mod_globals.debug_file.write( '"' + s + '"\n')

def isHex(s):
  return all(c in string.hexdigits for c in s)

def kill_server():
    if mod_globals.doc_server_proc is None:
        pass
    else:
        os.kill(mod_globals.doc_server_proc.pid, signal.SIGTERM)

def show_doc( addr, id ):
    if mod_globals.vin == '':
        return

    if mod_globals.doc_server_proc == None:
        mod_globals.doc_server_proc = subprocess.Popen(["python", "-m", "SimpleHTTPServer", "59152"])
        atexit.register(kill_server)

    if mod_globals.opt_sd:
        url = 'http://localhost:59152/doc/' + id[1:] + '.htm'
    else:
        url = 'http://localhost:59152/doc/'+mod_globals.vin+'.htm'+id
    webbrowser.open(url, new=0)



