#!/usr/bin/env python

import sys, os
#import serial
    
import mod_globals

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

import mod_elm


############## change me ################

ecu_functional_address  = "26"
mod_globals.opt_port    = 'bt'

#########################################


#mod_globals.opt_demo    = True
mod_globals.opt_speed   = 38400
mod_globals.opt_log     = 'simpl.txt'


print 'Opening ELM'
elm = mod_elm.ELM( mod_globals.opt_port, mod_globals.opt_speed, True )

print 'Init    ELM'
elm.init_can()

TXa = mod_elm.dnat[ecu_functional_address]
RXa = mod_elm.snat[ecu_functional_address]
elm.currentaddress = TXa

print elm.cmd("at sh "+TXa)
print elm.cmd("at cra "+RXa)
print elm.cmd("at fc sh "+TXa)
print elm.cmd("at fc sd 30 00 00") # status BS STmin
print elm.cmd("at fc sm 1")
print elm.cmd("at sp 6")
print elm.cmd("10C0")
#print elm.cmd("3BA00A00")

