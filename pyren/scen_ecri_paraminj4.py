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
from   mod_ply       import *
from   mod_utils     import pyren_encode
from   mod_utils     import clearScreen
from   mod_utils     import Choice
from   mod_utils     import isHex
from   collections   import OrderedDict
import xml.dom.minidom
import xml.etree.cElementTree as et

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
  ScmParam = OrderedDict()

  def get_message( msg, encode = True ):
    if msg in ScmParam.keys():
      value = ScmParam[msg]
    else:
      value = msg
    if value.isdigit() and value in mod_globals.language_dict.keys():
      if encode:
        value = pyren_encode(mod_globals.language_dict[value])
      else:
        value = mod_globals.language_dict[value]
    return value

  def get_message_by_id( id, encode = True ):
    if id.isdigit() and id in mod_globals.language_dict.keys():
      if encode:
        value = pyren_encode(mod_globals.language_dict[id])
      else:
        value = mod_globals.language_dict[id]
    return value
  
  #
  #      Data file parsing
  #  
  DOMTree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(data))
  ScmRoom = DOMTree.documentElement

  root = et.parse(mod_db_manager.get_file_from_clip(data)).getroot()
  
  ScmParams = ScmRoom.getElementsByTagName("ScmParam")
 
  for Param in ScmParams:
    name  = pyren_encode( Param.getAttribute("name") )
    value = pyren_encode( Param.getAttribute("value") )
        
    ScmParam[name] = value
    
  ScmSets = ScmRoom.getElementsByTagName("ScmSet")
 
  for Set in ScmSets:          
    setname  = pyren_encode(Set.getAttribute("name"))
    ScmParams = Set.getElementsByTagName("ScmParam")
  
    scmParamsDict = OrderedDict()
    for Param in ScmParams:
      name  = pyren_encode( Param.getAttribute("name")  )
      value = pyren_encode( Param.getAttribute("value") )
      
      scmParamsDict[name] = value
    
    ScmSet[setname]= scmParamsDict

  confirm = get_message_by_id('19800')
  successMessage = get_message("EndScreenMessage3")
  failMessage = get_message("EndScreenMessage4")

  #Prepare buttons
  buttons = OrderedDict()

  buttons[1] = get_message("Subtitle", False)
  buttons["loadDump"] = get_message_by_id('19802', False)
  buttons["exit"] = '<exit>'

  def getIdsDump():
    idsDump = OrderedDict()
    for name, value in ScmSet['CommandIdentifications'].iteritems():
      idValue = ecu.get_id(ScmSet['Identifications'][value], True)
      if isHex(idValue):
        idsDump[ScmSet['Commands'][name]] = idValue
    return idsDump
  
  def makeDump():
    fileRoot = et.Element("ScmRoot")
    fileRoot.text = "\n    "

    idsDump = getIdsDump()
    
    if not idsDump: return

    for cmd, value in idsDump.iteritems():
      el = et.Element("ScmParam", name=cmd, value=value)
      el.tail = "\n    "
      fileRoot.insert(1,el)

    tree = et.ElementTree(fileRoot)
    tree.write(mod_globals.dumps_dir + ScmParam['FileName'])
  
  def loadDump():
    dumpScmParam = {}

    clearScreen()

    try:
      dumpData = open(mod_globals.dumps_dir + ScmParam['FileName'], 'r')
    except:
      print get_message_by_id('2194')
      print
      raw_input('Press ENTER to exit')
      return
    
    dumpDOMTree = xml.dom.minidom.parse(dumpData)
    dumpScmRoot = dumpDOMTree.documentElement
    dumpScmParams = dumpScmRoot.getElementsByTagName("ScmParam")

    for Param in dumpScmParams:
      name  = pyren_encode( Param.getAttribute("name") )
      value = pyren_encode( Param.getAttribute("value") )

      dumpScmParam[name] = value

    print '*'*80
    print get_message_by_id('19802')
    print '*'*80
    print

    ch = raw_input(confirm + ' <YES/NO>: ')
    while (ch.upper()!='YES') and (ch.upper()!='NO'):
      ch = raw_input(confirm + ' <YES/NO>: ')
    if ch.upper()!='YES':
        return

    clearScreen()
      
    responses = ''
    for name, value in dumpScmParam.iteritems():
      responses += ecu.run_cmd(name, value)

    print '*'*80
    print
    if "NR" in responses:
      print failMessage
    else:
      print successMessage

    print
    raw_input('Press ENTER to exit')

  def resetValues():
    info = get_message('Informations')
    infoContent = get_message('InformationsContent')
    inProgressMessage = get_message('CommandInProgress')

    clearScreen()

    print title
    print '*'*80
    print subtitle
    print '*'*80
    print info
    print
    print infoContent
    print '*'*80
    print
    ch = raw_input(confirm + ' <YES/NO>: ')
    while (ch.upper()!='YES') and (ch.upper()!='NO'):
      ch = raw_input(confirm + ' <YES/NO>: ')
    if ch.upper()!='YES':
        return
    
    clearScreen()

    print inProgressMessage
    if not mod_globals.opt_demo:
      makeDump()

    responses = ''

    clearScreen()

    for name, value in ScmSet['CommandParameters'].iteritems():
      if isHex(value):
        responses += ecu.run_cmd(ScmSet['Commands'][name],value)
      else:
        result = re.search(r"[^a-zA-Z\d\s:]", value)
        if result:
          parameters = re.findall(r"Ident\d+", value)
          paramByteLength = len(parameters[0])/2
          comp = value

          for param in parameters:
            paramValue = ecu.get_id(ScmSet['Identifications'][param], True)
            if not isHex(paramValue):
              comp = ''
              break
            comp = comp.replace(param, '0x' + ecu.get_id(ScmSet['Identifications'][param], True))
          
          if not comp:
            continue

          calc = Calc()
          idValue = calc.calculate(comp)

          hexVal = hex(idValue)[2:]
          if len(hexVal)%2:
            hexVal = '0' + hexVal
          if (len(hexVal)/2) % paramByteLength:
            hexVal = '00' * (paramByteLength - len(hexVal)/2) + hexVal

          responses += ecu.run_cmd(ScmSet['Commands'][name],hexVal)
        
        else:
          idValue = ecu.get_id(ScmSet['Identifications'][value], True)
          if isHex(idValue):
            responses += ecu.run_cmd(ScmSet['Commands'][name],idValue)

    print '*'*80
    print
    if "NR" in responses:
      print failMessage
    else:
      print successMessage

    print
    raw_input('Press ENTER to exit')
  
  title = get_message('Title')
  subtitle = get_message('Subtitle')
  
  print title
  print '*'*80
  print subtitle
  print '*'*80
  print
  
  choice = Choice(buttons.values(), "Choose :")

  for key, value in buttons.iteritems():
    if choice[0] =='<exit>': return
    if value == choice[0]:
      if key == 'loadDump':
        loadDump()
      else:
        resetValues()
      return