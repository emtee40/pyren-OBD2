#!/usr/bin/python
#-*-coding:utf8;-*-
#qpy:2
#qpy:console

#enter file name without .py
cmdr_file = 'mod_ecu'


import os
import sys

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
pa = [os.path.abspath(name) for name in os.listdir(".") if os.path.isdir(name) and name.lower().startswith('pyren')][0]

if len(sys.argv)==1:
  sys.path.insert( 0, pa )
  sys.path.insert( 0, pa+"\\ply" )
  
  cmdr = __import__( cmdr_file )     

  os.chdir(pa)
  cmdr.main()

else:
  os.system("cd "+pa)
  os.system("python "+cmdr_file+".py "+(' '.join(sys.argv[1:])))
