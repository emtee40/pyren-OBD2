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
from   mod_utils     import pyren_encode
from   mod_utils     import clearScreen
from   mod_utils     import ASCIITOHEX
from   mod_utils     import StringToIntToHex
from   mod_utils     import Choice
from   collections   import OrderedDict
import xml.dom.minidom
import xml.etree.cElementTree as et

class ecus:
  
  vdiag = ""
  buttons = {}
  ncalib = ""

  def __init__(self, vd, nc, bt):
    self.vdiag = vd
    self.ncalib = nc
    self.buttons = bt

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
  ecusList = []
  correctEcu = ''
  vdiagExists = False
  ncalibExists = False

  def get_message( msg ):
    if msg in ScmParam.keys():
      value = ScmParam[msg]
    else:
      value = msg
    if value.isdigit() and value in mod_globals.language_dict.keys():
      value = mod_globals.language_dict[value]
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

  root = et.parse(data).getroot()
  
  ScmParams = ScmRoom.getElementsByTagName("ScmParam")
 
  for Param in ScmParams:
    name  = pyren_encode( Param.getAttribute("name") )
    value = pyren_encode( Param.getAttribute("value") )
        
    ScmParam[name] = value
    
  ScmSets = ScmRoom.getElementsByTagName("ScmSet")
 
  for Set in ScmSets:
    if len(Set.attributes) != 1:           
      setname  = pyren_encode(mod_globals.language_dict[Set.getAttribute("name")])
      ScmParams = Set.getElementsByTagName("ScmParam")
    
      for Param in ScmParams:
        name  = pyren_encode( Param.getAttribute("name")  )
        value = pyren_encode( Param.getAttribute("value") )
        
        ScmSet[setname]= value
        ScmParam[name] = value
  
  if "VDiag" in ScmParam.keys():
    vdiagExists = True
    if "Ncalib" in ScmParam.keys():
      ncalibExists = True
  
  # Get nested buttons with VDiag and Ncalib
  for vDiag in root:
    if vDiag.attrib["name"] == "VDiag":
      if len(vDiag.keys()) == 1:
        for vDiagName in vDiag:
          if vDiagName:
            for vDiagButtons in vDiagName:
              buttons = OrderedDict()
              if vDiagButtons.attrib["name"] == "Ncalib":
                for ncalibName in vDiagButtons:
                  for ncalibButtons in ncalibName:
                    if ncalibButtons.attrib["name"] == "Buttons":
                      for ncalibButton in ncalibButtons:
                        buttons[ncalibButton.attrib["name"]] = ncalibButton.attrib["value"]
                    ecusList.append(ecus(vDiagName.attrib["name"],ncalibName.attrib["name"], buttons))
              else:
                if vDiagButtons.attrib["name"] == "Buttons":
                  for vDiagButton in vDiagButtons:
                    buttons[vDiagButton.attrib["name"]] = vDiagButton.attrib["value"]
                ecusList.append(ecus(vDiagName.attrib["name"], '', buttons))

# Get plain buttons with VDiag
  if vdiagExists:
    if not ncalibExists:
      vdiag = ''
      buttons = OrderedDict()
      for name in ScmParam.keys():
        if name.startswith("InjectorsButton"):
          if buttons:
            ecusList.append(ecus(vdiag, '', buttons))
          buttons = OrderedDict()
          vdiag = name[-2:]
          buttons[name[:-2]] = ScmParam[name]
        if vdiag:
          if name.endswith("Button" + vdiag):
            buttons[name[:-2]] = ScmParam[name]
      ecusList.append(ecus(vdiag, '', buttons))
  else:                                         #Get buttons without VDiag
    buttons = OrderedDict()
    found = False
    for name in ScmParam.keys():
        if name == "InjectorsButton":
          buttons[name] = ScmParam[name]
          found = True
        if found:
          if name.endswith("Button"):
            buttons[name] = ScmParam[name]
          else:
            found = False
            break
    ecusList.append(ecus('', '', buttons))

# Get correct buttons set
  if vdiagExists:
    value1, datastr1 = ecu.get_id(ScmParam['VDiag'])
    for ecuSet in ecusList:
      if ecuSet.vdiag == value1.upper():
        if ncalibExists:
          if ecuSet.ncalib:
            value2, datastr2 = ecu.get_id(ScmParam['Ncalib'])
            if ecuSet.ncalib == value2.upper():
              correctEcu = ecuSet
              break
            elif ecuSet.ncalib == "Other":
              correctEcu = ecuSet
          else:
            correctEcu = ecuSet
        else:
          correctEcu = ecuSet
  else:
    correctEcu = ecusList[0]
  
  if not correctEcu and mod_globals.opt_demo:
    correctEcu = ecusList[0]

  # for i in ecusList:
  #   print i.vdiag
  #   print i.ncalib
  #   for l in i.buttons.keys():
  #     print l
  #     print str(i.buttons[l])

  #Prepare buttons
  buttons = OrderedDict()

  for l in correctEcu.buttons.keys():
    if l == 'InjectorsButton':
      if str(correctEcu.buttons[l]) == 'true':
        buttons[1] = get_message("Injectors")
    if l == 'EGRValveButton':
      if str(correctEcu.buttons[l]) == 'true':
        buttons[2] = get_message("EGR_VALVE")
    if l == 'InletFlapButton':
      if str(correctEcu.buttons[l]) == 'true':
        buttons[3] = get_message("INLET_FLAP")
    if l.startswith("Button"):
      if str(correctEcu.buttons[l]) == 'true':
        buttons[int(l.strip('Button'))] = get_message(l[:-6] + "Text")
  

  #Get commands
  commands = {}
  
  for child in root:
    if child.attrib["name"] == "Commands":
      if len(child.keys()) == 1:
        for param in child:
          commands[param.attrib["name"]] = param.attrib["value"]
  
  #Get identifications
  identsList = OrderedDict()
  identsKeys = OrderedDict()

  for param in ScmParam.keys():
    if param.startswith('Idents') and param.endswith('Begin'):
      key = param[6:-5]
      begin = int(ScmParam['Idents'+key+'Begin'])
      end = int(ScmParam['Idents'+key+'End'])
      identsKeys[key] = {"begin": begin, "end": end}
      try:
        identsList['D'+str(begin)] = ScmParam['Ident'+str(begin)]
      except:
        break
      else:
        for idnum in range(begin ,end + 1):
          identsList['D'+str(idnum)] = ScmParam['Ident'+str(idnum)]

  # def getIdents(start, end):
  #   identsDict = OrderedDict()
  #   for idnum in range(start,end + 1):
  #     identsDict['D'+str(idnum)] = ScmParam['Ident'+str(idnum)]
  #   return identsDict

  # for param in ScmParam.keys():
  #   if param.startswith('Idents') and param.endswith('Begin'):
  #     key = param[6:-5]
  #     start = int(ScmParam['Idents'+key+'Begin'])
  #     end = int(ScmParam['Idents'+key+'End'])
  #     identsList[key] = getIdents(start, end)

  def getValuesToChange(resetItem):
    params = {}
    for child in root:
      if child.attrib["name"] == resetItem:
        if len(child.keys()) == 1:
          for param in child:
            params[param.attrib["name"]] = param.attrib["value"]
    return params
  
  # def replaceValues(params):
  #   for k,v in params.iteritems():
  #     if v in identsList.keys():
  #       identsList[k] = ecu.get_id(identsList[v], 1)
  #     else:
  #       identsList[k] = v

  confirm = get_message_by_id('19800')
  successMessage = get_message('Message32')
  failMessage = get_message('MessageNACK')
  mainText = get_message('Title')

  # def resetEGRValve():
  #   paramToSend = ""
  #   params = getValuesToChange("EGR_VALVE")

  #   clearScreen()

  #   print mainText
  #   print
  #   print buttons[2]
  #   print
  #   ch = raw_input(confirm + ' <YES/NO>: ')
  #   while (ch.upper()!='YES') and (ch.upper()!='NO'):
  #     ch = raw_input(confirm + ' <YES/NO>: ')
  #   if ch.upper()!='YES':
  #       return

  #   clearScreen()

  #   if not params:
  #     print
  #     response = ecu.run_cmd(commands['Cmd5'])
  #     print
  #     if "NR" in response:
  #       print failMessage
  #     else:
  #       print successMessage
  #     print
  #     ch = raw_input('Press ENTER to exit')
  #     return
    
    
  #   for idKey in range(identsKeys[identsKeys.keys()[0]]['begin'], identsKeys[identsKeys.keys()[0]]['end'] + 1):
  #     identsList["D" + str(idKey)] = ecu.get_id(identsList["D" + str(idKey)], 1)

  #   for k,v in params.iteritems():
  #     if v in identsList.keys():
  #       identsList[k] = ecu.get_id(identsList[v], 1)
  #     else:
  #       identsList[k] = v
    
  #   for idKey in range(identsKeys[identsKeys.keys()[0]]['begin'], identsKeys[identsKeys.keys()[0]]['end'] + 1):
  #     paramToSend += identsList["D" + str(idKey)]
      
  #   print
  #   response = ecu.run_cmd(commands['Cmd5'],paramToSend)
  #   print
  #   if "NR" in response:
  #     print failMessage
  #   else:
  #     print successMessage

  #   print
  #   ch = raw_input('Press ENTER to exit')

  def resetValues(title, button, command, rangeKey, message = ''):
    paramToSend = ""
    params = getValuesToChange(title)

    clearScreen()

    print mainText
    print
    print buttons[button]
    print
    if button == 4:
      print get_message_by_id('55662')
      print
    if button == 5:
      print get_message_by_id('55663')
      print
    ch = raw_input(confirm + ' <YES/NO>: ')
    while (ch.upper()!='YES') and (ch.upper()!='NO'):
      ch = raw_input(confirm + ' <YES/NO>: ')
    if ch.upper()!='YES':
        return

    clearScreen()

    if not params:
      print
      response = ecu.run_cmd(command)
      print
      if "NR" in response:
        print failMessage
      else:
        print successMessage
      print
      ch = raw_input('Press ENTER to exit')
      return
      
    idRangeKey = identsKeys[identsKeys.keys()[rangeKey]]

    for k,v in params.iteritems():
      if v in identsList.keys():
        identsList[k] = ecu.get_id(identsList[v], 1)
      else:
        identsList[k] = v

    for idKey in range(idRangeKey['begin'], idRangeKey['end'] + 1):
      print str(idKey), identsList["D" + str(idKey)]
      if identsList["D" + str(idKey)].startswith("ID"):
        identsList["D" + str(idKey)] = ecu.get_id(identsList["D" + str(idKey)], 1)
      paramToSend += identsList["D" + str(idKey)]
      print str(idKey), identsList["D" + str(idKey)]
      
      
    print
    response = ecu.run_cmd(command,paramToSend)
    print

    if "NR" in response:
      print failMessage
    else:
      print successMessage

    print
    ch = raw_input('Press ENTER to exit')


  functions = OrderedDict()
  functions[2] = ["EGR_VALVE", 2, commands['Cmd5'], 0]
  functions[3] = ["INLET_FLAP", 3, commands['Cmd6'], 1]
  functions[4] = ["PARTICLE_FILTER", 4, commands['Cmd7'], 2]
  functions[5] = ["Button5ChangeData", 5, commands['Cmd7'], 2]

  infoMessage = get_message('Message1')
  confirmButton = get_message_by_id('8405')

  print mainText
  print
  print infoMessage
  print

  choice = Choice(buttons.values(), "Choose :")
  for key, value in buttons.iteritems():
    if value == choice[0]:
      resetValues(functions[key][0],functions[key][1],functions[key][2],functions[key][3])
      return