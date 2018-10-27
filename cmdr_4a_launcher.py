#!/usr/bin/python
#-*-coding:utf8;-*-
#qpy:2
#qpy:console

#enter file name without .py
cmdr_file = 'cmdr_odometr'
#cmdr_file = 'cmdr_example'


import os
import sys

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
pa = [os.path.abspath(name) for name in os.listdir(".") if os.path.isdir(name) and name.lower().startswith('pyren')][0]

if len(sys.argv)==1:
  sys.path.insert( 0, pa )
  sys.path.insert( 0, pa+"\\ply" )
  
  #tcfe = 'import ' + cmdr_file + ' as cmdr'
  #exec( tcfe )
  
  cmdr = __import__( cmdr_file )
  
  #### fake port for not to left empty
  sys.argv.append('-pbt') 
  
  #### demo mode without connecting to car
  #sys.argv.append('--demo') 
  
  #### save responses of all 21xx and 22xxxx commands for demo mode    
  #sys.argv.append('--dump')
  
  #### you should define it or you've been asked later 
  #sys.argv.append('-e'); sys.argv.append('10706') 
  
  #### ignore existence of savedEcus.p and do new scanning
  #sys.argv.append('--scan')
  
  #### commander would log any way but you can define new name  
  #sys.argv.append('--log'); sys.argv.append('log.txt') 
  
  #### switch to english. Remove all FG/SG files from cache directory
  #sys.argv.append('-LGB')
   
  #### try SlowInit before FastInit
  #sys.argv.append('--si')
   
  #### turn off automatic FC and do it by script
  #sys.argv.append('--cfc')
   
  #### turn off L1 cache
  #sys.argv.append('--n1c')
   
  os.chdir(pa)
  cmdr.main()
else:
  os.system("cd "+pa)
  os.system("python "+cmdr_file+".py "+(' '.join(sys.argv[1:])))
