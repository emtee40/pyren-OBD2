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
      value = mod_globals.language_dict[id]
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
                      buttons = OrderedDict()
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
              break
          else:
            correctEcu = ecuSet
            break
        else:
          correctEcu = ecuSet
          break 
  else:
    correctEcu = ecusList[0]

  if not correctEcu and mod_globals.opt_demo:
    correctEcu = ecusList[0]
  
  if vdiagExists:
    if not correctEcu:
      print '*'*80
      ch = raw_input('Unknown diagnostic version. Press ENTER to exit')
      return

  #Prepare buttons
  buttons = OrderedDict()

  for bt in correctEcu.buttons.keys():
    if bt == 'InjectorsButton':
      if str(correctEcu.buttons[bt]) == 'true':
        buttons[1] = get_message("Injectors")
    if bt == 'EGRValveButton':
      if str(correctEcu.buttons[bt]) == 'true':
        buttons[2] = get_message("EGR_VALVE")
    if bt == 'InletFlapButton':
      if str(correctEcu.buttons[bt]) == 'true':
        buttons[3] = get_message("INLET_FLAP")
    if bt.startswith("Button"):
      if str(correctEcu.buttons[bt]) == 'true':
        buttons[int(bt.strip('Button'))] = get_message(bt[:-6] + "Text")
  buttons["exit"] = '<exit>'

  #Get commands
  commands = {}
  
  for child in root:
    if child.attrib["name"] == "Commands":
      if len(child.keys()) == 1:
        for param in child:
          commands[param.attrib["name"]] = param.attrib["value"]
  
  #Get identifications
  identsList = OrderedDict()
  identsRangeKeys = OrderedDict()

  for param in ScmParam.keys():
    if param.startswith('Idents') and param.endswith('Begin'):
      key = param[6:-5]
      begin = int(ScmParam['Idents'+key+'Begin'])
      end = int(ScmParam['Idents'+key+'End'])
      identsRangeKeys[key] = {"begin": begin, "end": end}
      try:  #10099 trap
        identsList['D'+str(begin)] = ScmParam['Ident'+str(begin)]
      except:
        break
      else:
        for idnum in range(begin ,end + 1):
          identsList['D'+str(idnum)] = ScmParam['Ident'+str(idnum)]

  def getValuesToChange(resetItem):
    params = {}
    for child in root:
      if child.attrib["name"] == resetItem:
        if len(child.keys()) == 1:
          for param in child:
            params[param.attrib["name"].replace("D0", "D")] = param.attrib["value"]
    return params
  
  def getValuesFromEcu(rangeKey):
    paramToSend = ""
    idRangeKey = identsRangeKeys[identsRangeKeys.keys()[rangeKey]]

    for idKey in range(idRangeKey['begin'], idRangeKey['end'] + 1):
      if identsList["D" + str(idKey)].startswith("ID"):
        identsList["D" + str(idKey)] = ecu.get_id(identsList["D" + str(idKey)], 1)
      paramToSend += identsList["D" + str(idKey)]
    return paramToSend

  confirm = get_message_by_id('19800')
  successMessage = get_message('Message32')
  failMessage = get_message('MessageNACK')
  mainText = get_message('Title')
  inProgressMessage = get_message('CommandInProgressMessage')

  def resetInjetorsData(button, injectorsList):
    injectorsInfoMessage = get_message('Message21')
    response = ""
    clearScreen()

    print mainText
    print '*'*80
    print buttons[button]
    print '*'*80
    print injectorsInfoMessage
    print '*'*80
    print

    choice = Choice(injectorsList.keys(), "Choose :")
    if choice[0]=='<exit>': return
    
    clearScreen()
    
    print
    response = ecu.run_cmd(injectorsList[choice[0]])
    print

    if "NR" in response:
      print failMessage
    else:
      print successMessage

    print
    ch = raw_input('Press ENTER to exit')

  def afterEcuChange(title, button, command, rangeKey):
    params = getValuesToChange(title)
    infoMessage = get_message("Message262")
    mileageText = get_message_by_id('2110')

    clearScreen()
    print mainText
    print '*'*80
    print buttons[button]
    print '*'*80
    print infoMessage
    print '*'*80
    print get_message("MessageBox2")
    print 
    ch = raw_input(confirm + ' <YES/NO>: ')
    if ch.upper()!='YES':
        return
    mileage = raw_input(mileageText + ': ')
    while not (mileage.isdigit() and 2 <= len(mileage) <= 6 and int(mileage) >= 10):
      print get_message("MessageBox1")
      print
      mileage = raw_input(mileageText + ': ')

    clearScreen()

    print mileageText + ': ' + mileage
    print
    ch = raw_input(confirm + ' <YES/NO>: ')
    while (ch.upper()!='YES') and (ch.upper()!='NO'):
      ch = raw_input(confirm + ' <YES/NO>: ')
    if ch.upper()!='YES':
        return

    clearScreen()

    print
    print inProgressMessage

    mileage = int(mileage)

    for k,v in params.iteritems():
      if v in identsList.keys():
        identsList[k] = ecu.get_id(identsList[v], 1)
      elif v == "Mileage":
        identValue = ecu.get_id(identsList[k], 1)
        identsList[k] = "{0:0{1}X}".format(mileage,len(identValue))
      else:
        identsList[k] = v
    
    paramToSend = getValuesFromEcu(rangeKey)
    
    clearScreen()
      
    print
    response = ecu.run_cmd(command,paramToSend)
    print

    if "NR" in response:
      print failMessage
    else:
      print successMessage

    print
    ch = raw_input('Press ENTER to exit')

  def setGlowPlugsType(title, button, command, rangeKey):
    params = getValuesToChange(title)
    currentType = ecu.get_id(identsList[params["IdentToBeDisplayed"].replace("Ident", "D")], 1)
    slowTypeValue = get_message('ValueSlowParam')
    fastTypeValue = get_message('ValueFastParam')
    currentMessage = get_message_by_id('52676')
    slowMessage = get_message('Slow')
    fastMessage = get_message('Fast')
    notDefinedMessage = get_message('NotDefined')
    message2 = get_message('Message282')

    typesButtons = OrderedDict()

    typesButtons[slowMessage] = slowTypeValue
    typesButtons[fastMessage] = fastTypeValue
    typesButtons['<exit>'] = ""

    clearScreen()
    print mainText
    print '*'*80
    print buttons[button]
    print '*'*80
    print message2
    print '*'*80
    print
    if currentType == slowTypeValue:
      print currentMessage + ': ' + slowMessage
    elif currentType == fastTypeValue:
      print currentMessage + ': ' + fastMessage
    else:
      print currentMessage + ': ' + notDefinedMessage
    print

    choice = Choice(typesButtons.keys(), "Choose :")
    if choice[0]=='<exit>': return

    clearScreen()
    print
    print inProgressMessage

    identsList[params["IdentToBeDisplayed"].replace("Ident", "D")] = typesButtons[choice[0]]

    paramToSend = getValuesFromEcu(rangeKey)
    
    clearScreen()
      
    print
    response = ecu.run_cmd(command,paramToSend)
    print

    if "NR" in response:
      print failMessage
    else:
      print successMessage

    print
    ch = raw_input('Press ENTER to exit')

  def resetValues(title, button, command, rangeKey):
    paramToSend = ""
    commandTakesParams = True
    params = getValuesToChange(title)
    
    commandServices = ecu.Commands[command.replace("VP", "V")].serviceID  
    for sid in commandServices:
      if not ecu.Services[sid].params:  #For INLET_FLAP VP042 in 10959 or VP018 EGR_VALVE in 10527
        commandTakesParams = False
      else:
        commandTakesParams = True
        break
    
    if commandTakesParams:
      for k,v in params.iteritems():
        if v in identsList.keys():
          identsList[k] = ecu.get_id(identsList[v], 1)
        else:
          identsList[k] = v
      
      paramToSend = getValuesFromEcu(rangeKey)
    
    clearScreen()

    print mainText
    print '*'*80
    print buttons[button]
    print '*'*80
    if button == 4:
      print get_message_by_id('55662')
      print '*'*80
    if button == 5:
      print get_message_by_id('55663')
      print '*'*80
    print
    ch = raw_input(confirm + ' <YES/NO>: ')
    while (ch.upper()!='YES') and (ch.upper()!='NO'):
      ch = raw_input(confirm + ' <YES/NO>: ')
    if ch.upper()!='YES':
        return

    clearScreen()
      
    print
    if commandTakesParams:
      response = ecu.run_cmd(command,paramToSend)
    else:
      response = ecu.run_cmd(command)
    print

    if "NR" in response:
      print failMessage
    else:
      print successMessage

    print
    ch = raw_input('Press ENTER to exit')


  functions = OrderedDict()
  for cmdKey in commands.keys():
    if cmdKey == 'Cmd1':
      injectorsDict = OrderedDict()
      injectorsDict[get_message('Cylinder1')] = commands['Cmd1']
      injectorsDict[get_message('Cylinder2')] = commands['Cmd2']
      injectorsDict[get_message('Cylinder3')] = commands['Cmd3']
      injectorsDict[get_message('Cylinder4')] = commands['Cmd4']
      injectorsDict['<exit>'] = ""
      functions[1] = [1, injectorsDict]
    if cmdKey == 'Cmd5':
      functions[2] = ["EGR_VALVE", 2, commands['Cmd5'], 0]
    if cmdKey == 'Cmd6':
      functions[3] = ["INLET_FLAP", 3, commands['Cmd6'], 1]
    if cmdKey == 'Cmd7':
      functions[4] = ["PARTICLE_FILTER", 4, commands['Cmd7'], 2]
      functions[5] = ["Button5ChangeData", 5, commands['Cmd7'], 2]
      functions[6] = ["Button6ChangeData", 6, commands['Cmd7'], 2]
    if cmdKey == 'Cmd9':
      functions[8] = ["Button8DisplayData", 8, commands["Cmd9"], len(identsRangeKeys) - 1]

  infoMessage = get_message('Message1')
  
  print mainText
  print
  print infoMessage
  print

  notSupported = [7]

  choice = Choice(buttons.values(), "Choose :")

  for key, value in buttons.iteritems():
    if choice[0]=='<exit>': return
    if value == choice[0]:
      if key in notSupported:
        ch = raw_input("\nNot Supported yet. Press ENTER to exit")
        return
      if key == 1:
        resetInjetorsData(functions[key][0],functions[key][1])
      elif key ==6:
        afterEcuChange(functions[key][0],functions[key][1],functions[key][2],functions[key][3])
      elif key == 8:
        setGlowPlugsType(functions[key][0],functions[key][1],functions[key][2],functions[key][3])
      else:
        resetValues(functions[key][0],functions[key][1],functions[key][2],functions[key][3])
      return