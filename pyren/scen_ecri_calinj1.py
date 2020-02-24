#!/usr/bin/env python
'''
Scenarium usage example

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:scen_ecri_calinj1#scen_ecri_calinj1_xxxxx.xml

'run' procedure will be executed by pyren script
 
'''

import os
import sys
import re
import time
import string
import mod_globals
import mod_utils
import mod_ecu
import mod_db_manager
from   mod_utils     import pyren_encode
from   mod_utils     import clearScreen
from   mod_utils     import ASCIITOHEX
from   mod_utils     import StringToIntToHex
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
  DOMTree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(data))
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
  value1, datastr1 = ecu.get_id(ScmParam['Injecteur1'])
  value2, datastr2 = ecu.get_id(ScmParam['Injecteur2'])
  value3, datastr3 = ecu.get_id(ScmParam['Injecteur3'])
  value4, datastr4 = ecu.get_id(ScmParam['Injecteur4'])
  print pyren_encode(header)
  print get_message('TexteTitre')  
  print '*'*80
  print pyren_encode(datastr1)
  print pyren_encode(datastr2)
  print pyren_encode(datastr3)
  print pyren_encode(datastr4)
  print '*'*80

  ch = raw_input('Are you ready to change the Injector Codes? <y/n>:')
  while (ch.lower() !='y') and (ch.lower() !='n'):
      ch = raw_input('Are you ready to change the Injector Codes? <y/n>:')
  if ch.lower()!='y': return

  #
  #     INFO
  #
  
  clearScreen()
  value1, datastr1 = ecu.get_id(ScmParam['Injecteur1'])
  value2, datastr2 = ecu.get_id(ScmParam['Injecteur2'])
  value3, datastr3 = ecu.get_id(ScmParam['Injecteur3'])
  value4, datastr4 = ecu.get_id(ScmParam['Injecteur4'])
  print pyren_encode(header)
  print '*'*80
  print pyren_encode(datastr1)
  print pyren_encode(datastr2)
  print pyren_encode(datastr3)
  print pyren_encode(datastr4)
  print '*'*80
  print pyren_encode('Permitted Characters'),get_message('PermittedCharacters')  
  print '*'*80
  
  #
  #    Receive data length and format from scenario
  #

  nbCC = ScmParam['nbCaractereCode']
  nbCC = int(nbCC)
  if nbCC !=6 and nbCC !=7 and nbCC !=16:
    ch = raw_input('Error nbCaractereCode in scenario xml')
    return
  isHEX = ScmParam['FormatHexadecimal']
  isHEX = int(isHEX)
  if isHEX != 0 and isHEX != 1:
    ch = raw_input('Error FormatHexadecimal in scenario xml')
    return
  prmCHAR = ScmParam['PermittedCharacters']
  if len(prmCHAR) << 16 and len(prmCHAR) >> 33:
    ch = raw_input('Error PermittedCharacters in scenario xml')
    return
 
  #
  #    Get IMA from input
  #

  
  ch1 = raw_input(get_message('dat_Cylindre1')+': ').upper()
  while not (all (c in prmCHAR for c in ch1.upper()) and (len(ch1)==nbCC)):
      ch1 = raw_input(get_message('dat_Cylindre1')+': ').upper()
  ch2 = raw_input(get_message('dat_Cylindre2')+': ').upper()
  while not (all (c in prmCHAR for c in ch2.upper()) and (len(ch2)==nbCC)):
      ch2 = raw_input(get_message('dat_Cylindre2')+': ').upper()
  ch3 = raw_input(get_message('dat_Cylindre3')+': ').upper()
  while not (all (c in prmCHAR for c in ch3.upper()) and (len(ch3)==nbCC)):
      ch3 = raw_input(get_message('dat_Cylindre3')+': ').upper()
  ch4 = raw_input(get_message('dat_Cylindre4')+': ').upper()
  while not (all (c in prmCHAR for c in ch4.upper()) and (len(ch4)==nbCC)):
      ch4 = raw_input(get_message('dat_Cylindre4')+': ').upper()
      
 #
 #  Check all data format of input
 #
 
  chk = ( ch1 + ch2 + ch3 + ch4 )

  if isHEX == 1 and not (all (c in prmCHAR for c in chk.upper()) and (len(chk) == nbCC * 4)):
      print '*'*80
      ch = raw_input('Hexdata check failed. Press ENTER to exit')
      return
  elif isHEX == 0 and not (all (c in prmCHAR for c in chk.upper()) and (len(chk) == nbCC * 4)) :
      print '*'*80
      ch = raw_input('ASCII check failed. Press ENTER to exit')
      return
  else:
      print '*'*80
      ch = raw_input('All checks passed successfull. Press ENTER to continue')
  

  #
  # If all checks are successful script prepares the data according to their type
  #

  if isHEX == 1:
      inj_code = ( ch1 + ch2 + ch3 + ch4 ).upper()  
  elif isHEX == 0:
      inj_code = ASCIITOHEX ( ch1 + ch2 + ch3 + ch4 ).upper()
  else:
      print '*'*80
      ch = raw_input('!!!!!!!!There is a bug somwhere in the scenario, operation aborted!!!!!!!!!')
      return

  #
  # print old and new data 
  #
   
  clearScreen()
  print '*'*80
  print pyren_encode('Old injector codes')
  print pyren_encode(datastr1)
  print pyren_encode(datastr2)
  print pyren_encode(datastr3)
  print pyren_encode(datastr4)
  print '*'*80
  print pyren_encode('New injector codes')
  print get_message('dat_Cylindre1'),pyren_encode(':'),pyren_encode(ch1)
  print get_message('dat_Cylindre2'),pyren_encode(':'),pyren_encode(ch2)
  print get_message('dat_Cylindre3'),pyren_encode(':'),pyren_encode(ch3)
  print get_message('dat_Cylindre4'),pyren_encode(':'),pyren_encode(ch4)
  print '*'*80
  print pyren_encode('Permitted Characters'),get_message('PermittedCharacters')
  print '*'*80

 
  ch = raw_input('Start injectors writing? YES/QUIT>')
  while (ch.upper()!='YES') and (ch.upper()!='QUIT'):
      ch = raw_input('Start injectors codes writing? YES/QUIT>')
  if ch.upper()!='YES':
      return

  #
  #     Write Injector Codes
  #

  clearScreen()
  cmd = ecu.get_ref_cmd(get_message('EcritureCodeInjecteur'))
  print '*'*80
  responce = ecu.run_cmd(ScmParam['EcritureCodeInjecteur'],inj_code)
  value5, datastr5 = ecu.get_id(ScmParam['Injecteur1'])
  value6, datastr6 = ecu.get_id(ScmParam['Injecteur2'])
  value7, datastr7 = ecu.get_id(ScmParam['Injecteur3'])
  value8, datastr8 = ecu.get_id(ScmParam['Injecteur4'])
  print '*'*80
  print pyren_encode('Old injector codes')
  print pyren_encode(datastr1)
  print pyren_encode(datastr2)
  print pyren_encode(datastr3)
  print pyren_encode(datastr4)
  print '*'*80
  print pyren_encode('New injector codes')
  print pyren_encode(datastr5)
  print pyren_encode(datastr6)
  print pyren_encode(datastr7)
  print pyren_encode(datastr8)
  print '*'*80

  ch = raw_input('Press ENTER to exit')
  return
