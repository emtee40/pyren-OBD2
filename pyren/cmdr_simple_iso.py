#!/usr/bin/env python

import sys, os
import serial
    
import mod_globals

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

import mod_elm


############## change me ################

ecu_functional_address  = "7a"
#mod_globals.opt_port    = 'com4'
mod_globals.opt_port    = '/dev/cu.usbserial-AH01J4BS'

#########################################


#mod_globals.opt_demo    = True
mod_globals.opt_speed   = 38400
mod_globals.opt_log     = 'simpl.txt'


print 'Opening ELM'
elm = mod_elm.ELM( mod_globals.opt_port, mod_globals.opt_speed, True )

print 'Init    ELM'
print elm.cmd("at z")     
elm.init_iso()

#print elm.cmd("at fi")     
print elm.cmd("at sh 80 "+ecu_functional_address+" f1")           
print elm.cmd("at sw 96")            
print elm.cmd("at wm 81 "+ecu_functional_address+" f1 3E")        
print elm.cmd("at ib10")                        
print elm.cmd("at st ff")                       
print elm.cmd("at at 0")                        

#print elm.cmd("at sp 4")                      
#print elm.cmd("at si")
print elm.cmd("at sp 5")                      
print elm.cmd("at fi")     

print elm.cmd("at at 1") 
print elm.cmd("at al") 
print elm.cmd("at h1") 
  

print elm.cmd("10C0")
print elm.cmd("2180")
print elm.cmd("2181")
print elm.cmd("17FF00")
#print elm.cmd("14FF")
#print elm.cmd("14FF00")
print elm.cmd("01 02 03 04 05 06 07 08 09")


