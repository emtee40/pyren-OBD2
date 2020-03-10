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

  def get_message( msg, encode = 1 ):
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

  def get_message_by_id( id, encode = 1 ):
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
    if len(Set.attributes) != 1:           
      setname  = pyren_encode(mod_globals.language_dict[Set.getAttribute("name")])
      ScmParams = Set.getElementsByTagName("ScmParam")
    
      for Param in ScmParams:
        name  = pyren_encode( Param.getAttribute("name")  )
        value = pyren_encode( Param.getAttribute("value") )
        
        ScmSet[setname]= value
        ScmParam[name] = value
 
  if "IdentVdiag" in ScmParam.keys():
    vdiagExists = True
  
  # Get nested buttons with VDiag
  for vDiag in root:
    if vDiag.attrib["name"] == "ListVdiag":
      if len(vDiag.keys()) == 1:
        for vDiagName in vDiag:
          buttons = OrderedDict()
          if vDiagName:
            for vDiagButton in vDiagName:
              buttons[vDiagButton.attrib["name"]] = vDiagButton.attrib["value"]
              ecusList.append(ecus(vDiagName.attrib["name"], '', buttons))

# Get correct buttons set
  if vdiagExists:
    value1, datastr1 = ecu.get_id(ScmParam['IdentVdiag'])
    for ecuSet in ecusList:
      if ecuSet.vdiag == value1.upper():
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
        buttons[1] = get_message("Injectors",0)
    if bt == 'EGRValveButton':
      if str(correctEcu.buttons[bt]) == 'true':
        buttons[2] = get_message("EGR_VALVE",0)
    if bt == 'InletFlapButton':
      if str(correctEcu.buttons[bt]) == 'true':
        buttons[3] = get_message("INLET_FLAP",0)
    if bt == 'ParticleFilterButton':
      if str(correctEcu.buttons[bt]) == 'true':
        buttons[4] = get_message("PARTICLES_FILTER",0)
    if bt.startswith("Button"):
      if str(correctEcu.buttons[bt]) == 'true':
        buttons[int(bt.strip('Button'))] = get_message(bt[:-6] + "Text", 0)
  buttons["loadDump"] = get_message_by_id('19802', 0)
  buttons["exit"] = '<exit>'

  #Get commands
  commands = {}
  
  for child in root:
    if child.attrib["name"] == "Commands":
      if len(child.keys()) == 1:
        for param in child:
          serviceIDs = ecu.get_ref_cmd(param.attrib["value"]).serviceID
          startReq = ""
          for sid in serviceIDs:
            if ecu.Services[sid].params:
              startReq = ecu.Services[sid].startReq
              break
          commands[param.attrib["name"]] = {"command": param.attrib["value"], "startReq": startReq}
  
  #Get identifications
  identsList = OrderedDict()
  identsRangeKeys = OrderedDict()

  for param in ScmParam.keys():
    if param.startswith('Idents') and param.endswith('Begin'):
      key = param[6:-5]
      begin = int(ScmParam['Idents'+key+'Begin'])
      end = int(ScmParam['Idents'+key+'End'])
      try:  #10099 trap
        ecu.get_ref_id(ScmParam['Ident' + str(begin)]).mnemolist[0]
      except:
        continue
      else:
        for idnum in range(begin ,end + 1):
          identsList['D'+str(idnum)] = ScmParam['Ident'+str(idnum)]
        frame = ecu.Mnemonics[ecu.get_ref_id(identsList['D'+str(begin)]).mnemolist[0]].request
        identsRangeKeys[key] = {"begin": begin, "end": end, "frame": frame}

  def getValuesToChange(resetItem):
    params = {}
    for child in root:
      if child.attrib["name"] == resetItem:
        if len(child.keys()) == 1:
          for param in child:
            params[param.attrib["name"].replace("D0", "D")] = param.attrib["value"]
    return params

  def takesParams(request):
    for cmd in commands.values():
      if cmd['startReq'] == request:
        commandToRun = cmd['command']
        return commandToRun
  
  def getValuesFromEcu(params):
    paramToSend = ""
    commandToRun = ""
    requestToFindInCommandsRequests = ""
    backupDict = {}

    try:
      idKeyToFindInRange = int((params.keys()[0]).replace("D",""))
    except:
      return commandToRun, paramToSend
    else:
      for rangeK in identsRangeKeys.keys():
        if identsRangeKeys[rangeK]['begin'] <= idKeyToFindInRange <= identsRangeKeys[rangeK]['end']:
          requestToFindInCommandsRequests = "3B" + identsRangeKeys[rangeK]['frame'][-2:]
          isTakingParams = takesParams(requestToFindInCommandsRequests)
          if isTakingParams:
            for k,v in params.iteritems():
              backupDict[k] = ecu.get_id(identsList[k], 1)
              if v in identsList.keys():
                identsList[k] = ecu.get_id(identsList[v], 1)
              else:
                identsList[k] = v
            for idKey in range(identsRangeKeys[rangeK]['begin'], identsRangeKeys[rangeK]['end'] + 1):
              if identsList["D" + str(idKey)].startswith("ID"):
                identsList["D" + str(idKey)] = ecu.get_id(identsList["D" + str(idKey)], 1)
                backupDict["D" + str(idKey)] = identsList["D" + str(idKey)]
              paramToSend += identsList["D" + str(idKey)]
            commandToRun = isTakingParams
            break
      
      makeDump(commandToRun, backupDict)
      return commandToRun, paramToSend

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

  def afterEcuChange(title, button):
    params = getValuesToChange(title)
    infoMessage = get_message("Message262")
    mileageText = get_message_by_id('2110')
    mileageUnit = get_message_by_id('16521')

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
    mileage = raw_input(mileageText + ' (' + mileageUnit + ')' + ': ')
    while not (mileage.isdigit() and 2 <= len(mileage) <= 6 and int(mileage) >= 10):
      print get_message("MessageBox1")
      print
      mileage = raw_input(mileageText + ' (' + mileageUnit + ')' + ': ')

    clearScreen()

    print mileageText + ': ' + mileage + ' ' + mileageUnit
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

    for paramkey in params.keys():
      if params[paramkey] == "Mileage":
        mnemonics = ecu.get_ref_id(identsList[paramkey]).mnemolist[0]
        identValue = ecu.get_id(identsList[paramkey], 1)
        if identValue == 'ERROR':
          identValue = '00000000'
        hexval = "{0:0{1}X}".format(mileage,len(identValue))
        if ecu.Mnemonics[mnemonics].littleEndian == '1':
          a = hexval
          b = ''
          if not len(a) % 2:
            for i in range(0,len(a),2):
              b = a[i:i+2]+b
            hexval = b
        params[paramkey] = hexval
    
    command, paramToSend = getValuesFromEcu(params)

    if "ERROR" in paramToSend:
      raw_input("Data downloading went wrong. Aborting.")
      return
    
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

  def setGlowPlugsType(title, button):
    params = getValuesToChange(title)
    value, datastr = ecu.get_st(ScmParam['State1'])

    message = get_message('Message29')
    currentTypeMessage = get_message_by_id('52676')

    typesButtons = OrderedDict()

    typesButtons[get_message_by_id('54031',0)] = ScmParam['54031']
    typesButtons[get_message_by_id('54030',0)] = ScmParam['54030']
    typesButtons[get_message_by_id('54032',0)] = ScmParam['54032']
    typesButtons['<exit>'] = ""

    clearScreen()
    print mainText
    print '*'*80
    print buttons[button]
    print '*'*80
    print message
    print '*'*80
    print
    print currentTypeMessage + ':'
    print
    print datastr
    print

    choice = Choice(typesButtons.keys(), "Choose :")
    if choice[0]=='<exit>': return

    clearScreen()
    print
    print inProgressMessage

    glowPlugType =  "{0:0{1}X}".format((int(ScmParam['Mask1']) + int(typesButtons[choice[0]])),2)

    params[params.keys()[0]] = glowPlugType

    command, paramToSend = getValuesFromEcu(params)

    if "ERROR" in paramToSend:
      raw_input("Data downloading went wrong. Aborting.")
      return
    
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

  def resetValues(title, button, defaultCommand):
    paramToSend = ""
    commandTakesParams = True
    params = getValuesToChange(title)
    
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
    print inProgressMessage

    command, paramToSend = getValuesFromEcu(params)

    if "ERROR" in paramToSend:
      raw_input("Data downloading went wrong. Aborting.")
      return

    clearScreen()
     
    print
    if command:
      response = ecu.run_cmd(command,paramToSend)
    else:
      response = ecu.run_cmd(defaultCommand)
    print

    if "NR" in response:
      print failMessage
    else:
      print successMessage

    print
    ch = raw_input('Press ENTER to exit')

  def makeDump(cmd, idents):
    fileRoot = et.Element("ScmRoot")
    fileRoot.text = "\n    "

    cmdElement = et.Element("ScmParam", name="Command", value=cmd)
    cmdElement.tail = "\n    "
    fileRoot.insert(1,cmdElement)
    
    for k in idents:
      el = et.Element("ScmParam", name='D'+ '{:0>2}'.format(k[1:]), value=idents[k])
      el.tail = "\n    "
      fileRoot.insert(1,el)
  
    tree = et.ElementTree(fileRoot)
    tree.write(mod_globals.dumps_dir + ScmParam['FileName'])

  def loadDump():
    clearScreen()

    paramToSend = ""
    dumpScmParam = {}
    try:
      dumpData = open(mod_globals.dumps_dir + ScmParam['FileName'], 'r')
    except:
      print get_message_by_id('2194')
      raw_input()
      return
    
    dumpDOMTree = xml.dom.minidom.parse(dumpData)
    dumpScmRoot = dumpDOMTree.documentElement
    dumpScmParams = dumpScmRoot.getElementsByTagName("ScmParam")

    for Param in dumpScmParams:
      name  = pyren_encode( Param.getAttribute("name") )
      value = pyren_encode( Param.getAttribute("value") )

      dumpScmParam[name] = value
    
    for k in sorted(dumpScmParam):
      if k != "Command":
        paramToSend += dumpScmParam[k]

    if "ERROR" in paramToSend:
      raw_input("Data downloading went wrong. Aborting.")
      return

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
      
    print
    response = ecu.run_cmd(dumpScmParam['Command'],paramToSend)
    print

    if "NR" in response:
      print failMessage
    else:
      print successMessage

    print
    ch = raw_input('Press ENTER to exit')


  functions = OrderedDict()
  for cmdKey in commands.keys():
    if cmdKey == 'Cmd1' and "Cmd5" in commands.keys():
      injectorsDict = OrderedDict()
      injectorsDict[get_message('Cylinder1', 0)] = commands['Cmd1']['command']
      injectorsDict[get_message('Cylinder2', 0)] = commands['Cmd2']['command']
      injectorsDict[get_message('Cylinder3', 0)] = commands['Cmd3']['command']
      injectorsDict[get_message('Cylinder4', 0)] = commands['Cmd4']['command']
      injectorsDict['<exit>'] = ""
      functions[1] = [1, injectorsDict]
    if cmdKey == 'Cmd5':
      functions[2] = ["EGR_VALVE", 2, commands['Cmd5']['command']]
    if cmdKey == 'Cmd6':
      functions[3] = ["INLET_FLAP", 3, commands['Cmd6']['command']]
    if cmdKey == 'Cmd7':
      functions[4] = ["PARTICLE_FILTER", 4, commands['Cmd7']['command']]
      functions[5] = ["Button5ChangeData", 5, commands['Cmd7']['command']]
      functions[6] = ["Button6ChangeData", 6, commands['Cmd7']['command']]
    if len(commands) == 1 and cmdKey == 'Cmd1':
      functions[7] = ["Button7ChangeData", 7]

  infoMessage = get_message('Message1')
  
  print mainText
  print
  print infoMessage
  print

  choice = Choice(buttons.values(), "Choose :")

  for key, value in buttons.iteritems():
    if choice[0]=='<exit>': return
    if value == choice[0]:
      if key == 'loadDump':
        loadDump()
      elif key == 1:
        resetInjetorsData(functions[key][0],functions[key][1])
      elif key == 6:
        afterEcuChange(functions[key][0],functions[key][1])
      elif key == 7:
        setGlowPlugsType(functions[key][0],functions[key][1])
      else:
        resetValues(functions[key][0],functions[key][1],functions[key][2])
      return