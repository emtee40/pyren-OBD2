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
  import bus_monitor
  
  #fake port for not to left empty. Do not comment it
  sys.argv.append('-pbt')
 
  #### filtered mode   
  #sys.argv.append('-f');sys.argv.append('flt.txt')
  
  #### demo mode without connecting to car (mon.log is file needed)   
  #sys.argv.append('--demo');sys.argv.append('--log');sys.argv.append('mon.log')

  #### log for demo   
  #sys.argv.append('--log');sys.argv.append('mon.log')
  
  os.chdir(pa)
  bus_monitor.main()
else:
  os.system("cd "+pa)
  os.system("python bus_monitor.py "+(' '.join(sys.argv[1:])))
