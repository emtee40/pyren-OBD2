#!/usr/bin/env python

import struct
import sys
import os
import mod_globals
import mod_db_manager

try:
    import cPickle as pickle
except:
    import pickle

from xml.dom.minidom import parseString

class optfile:

  dict = {}

  obf = True
  
  def __init__(self,filename,progress=False,cache=True):
    
    self.dict = {}

    # check in cache folder
    cachename = mod_globals.cache_dir+os.path.basename(filename)[:-4]+'.p'
    if os.path.isfile(cachename):
      self.dict = pickle.load( open( cachename, "rb" ) )
      return

    if mod_globals.clip_arc!='' and mod_db_manager.file_in_clip(filename[:-4]+'.p'):
      mod_db_manager.extract_from_clip_to_cache(filename[:-4]+'.p')
      self.dict = pickle.load( open( cachename, "rb" ) )
      return

    lf = mod_db_manager.get_file_from_clip( filename )

    if lf:
      self.get_dict( lf, progress )
      if cache:
        pickle.dump( self.dict, open( cachename, "wb" ) )

  def get_string(self, lf, len):

    i = lf.tell()
    bytes = lf.read(2 * len)

    st = ''
    j = 0
    len = len * 2
    while j < len:
      x = struct.unpack('<H', bytes[j:j + 2])[0]
      if self.obf: x = x ^ (i & 0xFFFF) ^ 0x5555
      j += 2
      i += 2
      st += unichr(x)

    return st

  def get_2_bytes(self,lf):

    i = lf.tell()
    bytes = lf.read(2)
    
    x = 0
    x = struct.unpack('<H', bytes)[0]
    
    if self.obf==False: return x

    return x^(i&0xFFFF)^0x5555

  def get_4_bytes(self,lf):
    return self.get_2_bytes(lf)+(self.get_2_bytes(lf)<<16)

  def get_dict(self,lf,progress):
    
    self.fb = ord(lf.read(1))
    
    if self.fb!=0x55 and self.fb!=0xBD: self.obf = False
    
    lf.seek(0x14)
    protlen = self.get_4_bytes(lf)
    lf.seek(0x18+protlen*2)
    keyoff = self.get_4_bytes(lf)
    
    lf.seek(keyoff-8)
    tb = self.get_4_bytes(lf)
    i = keyoff
    
    n = 0
    
    while i<tb:
    
      if progress and (i&0xff==0):
        pr = (i+2-keyoff)*100/(tb-keyoff)
        print '\r['+'X'*(pr/2)+' '*(50-pr/2)+'] '+str(int(pr))+'%',
        sys.stdout.flush()
          
      lf.seek(i)
      addr = self.get_4_bytes(lf)
      strl = self.get_4_bytes(lf)
      keyl = self.get_4_bytes(lf)
      n = n + 1

      key = self.get_string(lf,keyl)

      lf.seek(addr)
      line = self.get_string(lf,strl)
      line = line.strip()
      line = line.strip('\n')
      line = line.replace(u'\xab','\"')
      line = line.replace(u'\xbb','\"')

      self.dict[key] = line 
      i=i+12+keyl*2
    
    if progress:
      print '\r['+'X'*50+'] 100%',

if __name__ == "__main__":

  os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
  
  if len(sys.argv)==1:
    print "Usage: mod_optfile.py <filename> [key]"
    print "       mod_optfile.py ALLSG"
    print "       mod_optfile.py HEX <infile> <outfile>"
    print "Example:"
    print "   mod_optfile.py ../Location/DiagOnCan_RU.bqm"
    print "   mod_optfile.py ../EcuRenault/Sessions/SG0110016.XML P001"
    sys.exit(0)

  if sys.argv[1]=='ALLSG':
    for subdir, dirs, files in os.walk('../EcuRenault/Sessions'):
      for file in files:
        if file.startswith('SG'):
          sgFileName = '../EcuRenault/Sessions/S'+file[1:]
          ugFileName = '../EcuRenault/Sessions/U'+file[1:]
          if os.path.isfile(ugFileName): continue
          print sgFileName
          try:
            of = optfile(sgFileName,False,False)
          except:
            print 'bad file'
            continue
          rf = '<?xml version="1.0" ?><DiagOnCan>'
          for k in sorted(of.dict.keys()):
            if of.dict[k][:1]=='<' and of.dict[k][-1:]=='>':
              rf = rf + of.dict[k]
          rf = rf + '</DiagOnCan>'
          rf = parseString(rf).toprettyxml(indent='  ')
          print ugFileName
          f = open(ugFileName,'wt')
          f.write( rf )
          f.close()
    exit(0)

  if sys.argv[1]=='HEX':
      lf = open(sys.argv[2], "rb")
      of = open(sys.argv[3], "wb")

      while(1):
        i = lf.tell()
        bytes = lf.read(2)
        if len(bytes)<2:
          exit()

        x = 0
        x = struct.unpack('<H', bytes)[0]
        x = x ^ (i & 0xFFFF) ^ 0x5555
        of.write(struct.pack('H', x))

  of = optfile(sys.argv[1])

  if len(sys.argv)==2:
    for k in sorted(of.dict.keys()):
      print '#'*60
      print 'Key:',k
      print '-'*60
      if of.dict[k][:1]=='<' and of.dict[k][-1:]=='>':
        print parseString(of.dict[k]).toprettyxml(indent='  ')     
      else:
        print of.dict[k]
   
  if len(sys.argv)==3:
    k = sys.argv[2]
    if k in of.dict.keys():
      if of.dict[k][:1]=='<' and of.dict[k][-1:]=='>':
        print parseString(of.dict[k]).toprettyxml(indent='  ')     
      else:
       print of.dict[k]
    else:
      for i in sorted(of.dict.keys()):
        if k in i:
          print '#'*60
          print 'Key:',i
          print '-'*60
          if of.dict[i][:1]=='<' and of.dict[i][-1:]=='>':
            print parseString(of.dict[i]).toprettyxml(indent='  ')    
          else:
            print of.dict[i]
      
  
   
