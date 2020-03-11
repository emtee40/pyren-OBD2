#!/usr/bin/env python
'''
Scenarium usage example

Name of this script should be exactly the same as in scenaruim URL but with '.py' extension

URL  -  scm:scen_lect_sondeO21#scen_lect_xxxxxx_xxxxx.xml

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
from   copy          import deepcopy

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
  
  ScmParam          = {}
  ScmList_Etats     = []
  ScmList_Messages  = []
  ScmUSet           = {}

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
  
  # read parameters
  ScmParams = ScmRoom.getElementsByTagName("ScmParam")
 
  for Param in ScmParams:
    name  = pyren_encode( Param.getAttribute("name")  )
    value = pyren_encode( Param.getAttribute("value") )
    
    ScmParam[name] = value

  # read ScmLists
  ScmLists = ScmRoom.getElementsByTagName("ScmList")
 
  for ScmList in ScmLists:
    listname  = ScmList.getAttribute("name")
    ScmUSets = ScmList.getElementsByTagName("ScmUSet")
   
    ScmUSet = {}
    for Set in ScmUSets:
      ScmParams = Set.getElementsByTagName("ScmParam")
      for Param in ScmParams:
        name  = pyren_encode( Param.getAttribute("name")  )
        value = pyren_encode( Param.getAttribute("value") )      
        ScmUSet[name] = value
        
      if listname.lower()=='etats':
        ScmList_Etats.append( deepcopy(ScmUSet) )
      else:
        ScmList_Messages.append( deepcopy(ScmUSet) )
    
  #
  #     Important information
  #
  clearScreen()
  print pyren_encode(header)
  print 
  print get_message('TexteScenario')  
  print 
  print get_message('TexteInformations')  
  print 
  print '*'*80
  print 
  print get_message('TexteContenuInformationsE1')  
  print 
  print get_message('TexteContenuInformationsE4')  
  print 
  print get_message('TexteProcedureFin')  
  print 
  print '*'*80
  ch = raw_input('Press ENTER to continue')
 
  #
  #     Check conditions
  #
  i = 1
  clearScreen()
  print pyren_encode(header)
  print 
  print '*'*80
  for etat in ScmList_Etats:
    print "Checking condition : ",i; i = i + 1
    print '*'*80
    state_ref = ecu.get_ref_st(etat['Index'])
    value1, datastr1 = ecu.get_st(etat['Index'])
    print datastr1
    if pyren_encode(state_ref.caracter[str(value1)])!=pyren_encode( mod_globals.language_dict[etat['RefOK']] ):
      value2, datastr2 = ecu.get_st(etat['Donne1'])
      print pyren_encode( mod_globals.language_dict[etat['TexteSortie']] )
      print datastr2
      print '*'*80
      ch = raw_input('Press ENTER to exit')
      #return

  #
  #     Ask permission to start
  #
  #clearScreen()
  print
  print '*'*80
  print
  print pyren_encode(header)
  print 
  ch = raw_input('Are you ready to start the test? <yes/no>:')
  if ch.lower()!='yes': return

  
  #
  #     Start test
  #
  responce = ecu.run_cmd(ScmParam['CommandeTestSonde'])
  
  #
  #     Main cycle
  #
  begin_time = time.time()
  Phase_state  = ecu.get_ref_st(ScmParam['EtatComTer'])
  Result_state = ecu.get_ref_st(ScmParam['EtatResultatTest'])
  kb = KBHit()
  pfe = 0
  while( 1 ):
    # get all values before showing them for avoid screen flickering
    value0, datastr0 = ecu.get_st(ScmParam['EtatComTer'])
    value1, datastr1 = ecu.get_st(ScmParam['EtatResultatTest'])
    phase   = pyren_encode(Phase_state.caracter[str(value0)])
    rescode = pyren_encode(Result_state.caracter[str(value1)])
    result   = rescode
    for m in ScmList_Messages:
      if rescode in pyren_encode(mod_globals.language_dict[m['Valeur']]):
        result  = pyren_encode( mod_globals.language_dict[m['Texte']])
    
    current_time = time.time()
    elapsed = int(current_time-begin_time)
    minutes, seconds = divmod(elapsed, 60)
    hours, minutes = divmod(minutes, 60)

    #
    #    Show process
    #
    clearScreen()
    print pyren_encode(header)
    print '\tTime   - ',"{hours:02d}:{minutes:02d}:{seconds:02d}".format(**vars())
    print '\tPhase  - ', phase
    print '*'*90
    print datastr0
    print datastr1
    print '*'*90
    if int(value0)==3: 
      pfe = 1
      break
    print 'Press Q to emergency exit'
    if kb.kbhit():
      c = kb.getch()
      if len(c)!=1: continue
      if c=='q' or c=='Q':
        kb.set_normal_term()
        break
    time.sleep( 0.2 )

  kb.set_normal_term()
  if pfe: 
    print '\tPhase  - ', phase
    print '\tResult - ', result
    print '*'*90

  ch = raw_input('Press ENTER to exit')
      
