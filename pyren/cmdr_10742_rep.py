#!/usr/bin/env python

import sys, os
import mod_globals

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

import mod_elm

############## change me ################

ecu_functional_address  = "7A"
mod_globals.os          = 'android'
mod_globals.opt_port    = 'bt'   # 'COM4'

#########################################

#mod_globals.opt_demo    = True
mod_globals.opt_cfc0    = True
mod_globals.opt_speed   = 38400
mod_globals.opt_log     = '10742-rep.txt'

print 'Opening ELM'
elm = mod_elm.ELM( mod_globals.opt_port, mod_globals.opt_speed, True )

print 'Init    ELM'
elm.init_can()

TXa = mod_elm.dnat[ecu_functional_address]
RXa = mod_elm.snat[ecu_functional_address]

print elm.cmd("at sh "+TXa)
print elm.cmd("at cra "+RXa)
print elm.cmd("at fc sh "+TXa)
print elm.cmd("at fc sd 30 00 00")
print elm.cmd("at fc sm 1")
print elm.cmd("at st ff")
print elm.cmd("at at 0") 
print elm.cmd("at sp 6")
print elm.cmd("at at 1") 
print elm.cmd("10C0")

# check ECU
r = elm.cmd("2180")
#debug
#r = '''61 80 34 36 33 32 52 45 34 42 45 30 30 33 37 52 00 83 9D 00 1A 90 01 01 00 88 AA'''
if len(r)<53 or r[7*3:7*3+2]!='45' or r[17*3:17*3+2]!='83':
  print "\n\nNot compatible ECU\n\n"
  exit() 

print elm.cmd("2EFD5000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
print elm.cmd("2EFD510000000100000001000000010000000100000001000000010000000100000001")
print elm.cmd("2EFD527FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA7FFA")
print elm.cmd("2EFD5300")
print elm.cmd("2EFD5400000000000000000000000000000000")
print elm.cmd("2EFD550000000000000000000000000000000000000000000000000000000000000000")
print elm.cmd("2EFD5680008000800080008000800080008000")
print elm.cmd("2EFD5700")
print elm.cmd("2E216401")

print "Done"




