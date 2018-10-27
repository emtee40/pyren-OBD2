#!/usr/bin/env python
'''
Scenarium usage example

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:scen_ecri_codevin#scen_ecri_codevin_xxxxx.xml

'run' procedure will be executed by pyren script
 
'''

import os
import sys
import re
import time

import mod_globals
import mod_utils
import mod_ecu
from   mod_utils     import pyren_encode
from   mod_utils     import clearScreen
from   mod_utils     import hex_VIN_plus_CRC

import xml.dom.minidom

def run( elm, ecu, command, data ):
  '''
  MAIN function of scenarium
  
  Parameters:
      elm     - refernce to adapter class
      ecu     - reference to ecu class
      command - refernce to the command this scenarium belongs to
      data    - name of xml file with parameters from scenarium URL
  '''
  
  clearScreen()
  header =  '['+command.codeMR+'] '+command.label
  
  ScmSet   = {}
  ScmParam = {}

  def get_message( msg ):
    if msg in ScmParam.keys():
      value = ScmParam[msg]
    else:
      value = msg
    if value.isdigit() and value in mod_globals.language_dict.keys():
      value = pyren_encode( mod_globals.language_dict[value] )
    return value

  def get_message_by_id( id ):
    if id.isdigit() and id in mod_globals.language_dict.keys():
      value = pyren_encode( mod_globals.language_dict[id] )
    return value
  
  
  #
  #      Data file parsing
  #  
  DOMTree = xml.dom.minidom.parse(data)
  ScmRoom = DOMTree.documentElement
  
  ScmParams = ScmRoom.getElementsByTagName("ScmParam")
 
  for Param in ScmParams:
    name  = pyren_encode( Param.getAttribute("name")  )
    value = pyren_encode( Param.getAttribute("value") )
        
    ScmParam[name] = value
    
  ScmSets = ScmRoom.getElementsByTagName("ScmSet")
 
  for Set in ScmSets:
    setname  = pyren_encode(mod_globals.language_dict[Set.getAttribute("name")])
    ScmParams = Set.getElementsByTagName("ScmParam")
   
    for Param in ScmParams:
      name  = pyren_encode( Param.getAttribute("name")  )
      value = pyren_encode( Param.getAttribute("value") )
      
      ScmSet[setname]= value
      ScmParam[name] = value

  #
  #     Important information
  #
  clearScreen()
  value1, datastr1 = ecu.get_id(ScmParam['identVIN'])
  print pyren_encode(header)
  print 
  print get_message('TextTitre')  
  print 
  print get_message('MessageBox3')  
  print 
  print '*'*80
  print 
  print pyren_encode(datastr1)
  print 
  print '*'*80
  ch = raw_input('Are you ready to change the VIN? <yes/no>:')
  if ch.lower()!='yes': return

  #
  #     Enter new VIN
  #
  clearScreen()
  print pyren_encode(header)
  print 
  print get_message('TextTitre')  
  print 
  print '*'*80
  print 
  ch = raw_input(get_message('STextTitre1')+': ').upper()

  while not (len(ch)==17 and ('I' not in ch) and ('O' not in ch)):
    ch = raw_input(get_message('STextTitre2')+': ').upper()
  
  cmd = ecu.get_ref_cmd(get_message('ConfigurationName'))
  
  vin_crc = hex_VIN_plus_CRC( ch )

  print 
  ch = raw_input('Are you ready to change the VIN? <yes/no>:')
  if ch.lower()!='yes': return

  #
  #     Change VIN
  #
  responce = ecu.run_cmd(ScmParam['ConfigurationName'],vin_crc)
  value1, datastr1 = ecu.get_id(ScmParam['identVIN'])
  print
  print '*'*80
  print 
  print pyren_encode(datastr1)
  print 
  print '*'*80
  
  ch = raw_input('Press ENTER to continue')

