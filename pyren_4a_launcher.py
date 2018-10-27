#!/usr/bin/python
#-*-coding:utf8;-*-
#qpy:2
#qpy:console


import os
import sys

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
pa = [os.path.abspath(name) for name in os.listdir(".") if os.path.isdir(name) and name.lower().startswith('pyren')][0]

if len(sys.argv)==1:
  sys.path.insert( 0, pa )
  sys.path.insert( 0, pa+"\\ply" )
  import pyren
  
  #fake port for not to left empty. Do not comment it
  sys.argv.append('-pbt')
 
  #### demo mode without connecting to car    
  #sys.argv.append('--demo')#; sys.argv.append('-e11476,11588')
  
  #### save responses of all 21xx and 22xxxx commands for demo mode    
  #sys.argv.append('--dump')
  
  #### ignore existence of savedEcus.p and do new scanning
  #sys.argv.append('--scan')
  
  #### enable logging
  #sys.argv.append('--log'); sys.argv.append('log.txt')

  #### switch to english. Remove all FG/SG files from cache directory
  #sys.argv.append('-LGB')
  
  #### try SlowInit before FastInit
  #sys.argv.append('--si')
   
  #### turn off automatic FC and do it by script
  #sys.argv.append('--cfc')
   
  #### turn off L1 cache
  #sys.argv.append('--n1c')

  #### save responses of all 21xx and 22xxxx commands for demo mode    
  #sys.argv.append('--dev'); sys.argv.append('1086')
  
  #### turn on writing to csv. Uncomment only one of them
  #sys.argv.append('--csv')
  #sys.argv.append('--csv_only')
  #sys.argv.append('--csv_human')

  os.chdir(pa)
  pyren.main()
else:
  os.system("cd "+pa)
  os.system("python pyren.py "+(' '.join(sys.argv[1:])))
