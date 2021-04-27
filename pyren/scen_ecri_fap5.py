#!/usr/bin/env python
'''
Scenarium usage example

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:scen_ecri_fap5#scen_ecri_fap5_xxxxx.xml

'run' procedure will be executed by pyren script
 
'''

import os
import sys
import re
import time

import mod_globals
import mod_utils
import mod_ecu
import mod_db_manager
from   mod_utils     import pyren_encode
from   mod_utils     import clearScreen
from   mod_utils     import KBHit

import xml.dom.minidom

#def get_message( value ):
#  if value.isdigit() and value in mod_globals.language_dict.keys():
#    value = pyren_encode( mod_globals.language_dict[value] )
#  print value
  
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
  #     Renew info about min/max values
  #
  GenPow = ecu.get_ref_pr(ScmParam['Param7'])  #Generator power
  GenPow.min = ScmParam['AltValueMin']
  GenPow.max = ScmParam['AltValueMax']
  
  PartMass = ecu.get_ref_pr(ScmParam['Param6']) #Particle mass
  PartMass.min = ScmParam['s_masse_suie_actif']
  PartMass.max = ScmParam['s_masse_suie_max']
  
  #
  #     Important information
  #
  clearScreen()
  print pyren_encode(header)
  print 
  print get_message('SCMTitle')  
  print 
  print get_message('Informations')  
  print 
  print '*'*80
  print 
  print get_message_by_id('1144')  
  print 
  print get_message_by_id('1145')  
  print 
  print get_message_by_id('1146')  
  print 
  ch = raw_input('Press ENTER to continue')
  clearScreen()
  print pyren_encode(header)
  print 
  print get_message('SCMTitle')  
  print 
  print '*'*80
  print 
  print get_message_by_id('1147')  
  print 
  print get_message_by_id('1148')  
  print 
  ch = raw_input('Press ENTER to continue')
      
  #
  #     Check conditions
  #
  State1_ref = ecu.get_ref_st(ScmParam['State1'])  #Engine state
  value7, datastr7 = ecu.get_st(ScmParam['State1'])
  kb = KBHit()
  while pyren_encode(value7) != pyren_encode( mod_globals.language_dict[ScmParam['TOURNANT']]):
    value7, datastr7 = ecu.get_st(ScmParam['State1'])
    value5, datastr5 = ecu.get_pr(ScmParam['Param6'])
    value6, datastr6 = ecu.get_pr(ScmParam['Param7'])
    clearScreen()
    print pyren_encode(header)
    print 
    print get_message('SCMTitle')  
    print 
    print '\tCHECK CONDITIONS'
    print 
    print '*'*90
    print pyren_encode(datastr7)
    print pyren_encode(datastr5)
    print pyren_encode(datastr6)
    print '*'*90
    print get_message_by_id('1149')  
    print 
    print 'Strat the engine and press ENTER to continue'
    print 'Q to exit or A to continue anyway'
    if kb.kbhit():
      c = kb.getch()
      if len(c)!=1: continue
      if c=='q' or c=='Q':
        kb.set_normal_term()
        return
      elif c=='a' or c=='A':
        kb.set_normal_term()
        break
    time.sleep( 0.2 )
    
  #
  #     Ask permission to start
  #
  clearScreen()
  print pyren_encode(header)
  print 
  ch = raw_input('Are you ready to start regeneration? <yes/no>:')
  if ch.lower()!='yes': return

  #
  #     Start regeneration
  #
  responce = ecu.run_cmd(ScmParam['Cmde1'])
  
  #
  #     Main cycle
  #
  begin_time = time.time()
  Phase_state  = ecu.get_ref_st(ScmParam['State2'])
  Result_state = ecu.get_ref_st(ScmParam['State3'])
  kb = KBHit()
  pfe = 0
  while( 1 ):
    # get all values before showing them for avoid screen flickering
    value0, datastr0 = ecu.get_pr(ScmParam['Param1'])
    value1, datastr1 = ecu.get_pr(ScmParam['Param2'])
    value2, datastr2 = ecu.get_pr(ScmParam['Param3'])
    value3, datastr3 = ecu.get_pr(ScmParam['Param4'])
    value4, datastr4 = ecu.get_pr(ScmParam['Param5'])
    value5, datastr5 = ecu.get_pr(ScmParam['Param6'])
    value6, datastr6 = ecu.get_pr(ScmParam['Param7'])  
    value7, datastr7 = ecu.get_st(ScmParam['State1'])
    value8, datastr8 = ecu.get_st(ScmParam['State2'])  # Phase
    value9, datastr9 = ecu.get_st(ScmParam['State3'])  # Result status
    valuea, datastra = ecu.get_st(ScmParam['State4'])

    #test
    #value8 = 6
    #value9 = 3
    
    current_time = time.time()
    elapsed = int(current_time-begin_time)
    minutes, seconds = divmod(elapsed, 60)
    hours, minutes = divmod(minutes, 60)

    #
    #    Check phase
    #
    etat    = pyren_encode(value8)
    if   etat == get_message('ETAT1'): phase = get_message('Phase1'); pfe = 0  
    elif etat == get_message('ETAT2'): phase = get_message('Phase2'); pfe = 0  
    elif etat == get_message('ETAT3'): phase = get_message('Phase3'); pfe = 0  
    elif etat == get_message('ETAT4'): phase = get_message('Phase4'); pfe = 0  
    elif etat == get_message('ETAT5'): phase = get_message('Phase5'); pfe = 1  
    elif etat == get_message('ETAT6'): phase = get_message('Phase6'); pfe = 2
    else:  phase = etat  

    #
    #    Check result
    #
    rescode = pyren_encode(value9)
    result  = pyren_encode( mod_globals.language_dict[ScmSet[rescode]])

    clearScreen()
    print pyren_encode(header)
    print '\tTime   - ',"{hours:02d}:{minutes:02d}:{seconds:02d}".format(**vars())
    print '\tPhase  - ', phase
    #print '\tResult - ', result
    print '*'*90
    print pyren_encode(datastr0)
    print pyren_encode(datastr1) 
    print pyren_encode(datastr2) 
    print pyren_encode(datastr3) 
    print pyren_encode(datastr4) 
    print pyren_encode(datastr5) 
    print pyren_encode(datastr6) 
    print pyren_encode(datastr7) 
    print pyren_encode(datastr8) 
    print pyren_encode(datastr9) 
    print pyren_encode(datastra) 
    print '*'*90
    if pfe: break
    print 'Press Q to emergency exit'
    if kb.kbhit():
      c = kb.getch()
      if len(c)!=1: continue
      if c=='q' or c=='Q':
        kb.set_normal_term()
        responce = ecu.run_cmd(ScmParam['Cmde2'])
        break
    time.sleep( 0.2 )

  if pfe: 
    print '\tPhase  - ', phase
    print '\tResult - ', result
    print '*'*90

  ch = raw_input('Press ENTER to exit')
      
