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
              # print datastr1
              # print datastr2
              correctEcu = ecuSet
              break
            elif ecuSet.ncalib == "Other":
              # print datastr1
              # print ecuSet.ncalib
              correctEcu = ecuSet
          else:
            # print datastr1
            correctEcu = ecuSet
        else:
          # print datastr1
          correctEcu = ecuSet
  else:
    correctEcu = ecusList[0]
  
  # for i in ecusList:
  #   print i.vdiag
  #   print i.ncalib
  #   for l in i.buttons.keys():
  #     print l
  #     print str(i.buttons[l])

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
        buttons[l.strip('Button')] = get_message(l[:-6] + "Text")
  
  identsList = OrderedDict()

  def getIdents(start, end):
    identsDict = OrderedDict()
    for idnum in range(start,end + 1):
      identsDict['D'+str(idnum)] = ScmParam['Ident'+str(idnum)]
    return identsDict

  for param in ScmParam.keys():
    if param.startswith('Idents') and param.endswith('Begin'):
      key = param[6:-5]
      start = int(ScmParam['Idents'+key+'Begin'])
      end = int(ScmParam['Idents'+key+'End'])
      identsList[key] = getIdents(start, end)

  commands = {}
  
  for child in root:
      if child.attrib["name"] == "Commands":
        if len(child.keys()) == 1:
          for param in child:
            commands[param.attrib["name"]] = param.attrib["value"]

  def resetEGRValve():
    paramToSend = ""
    params = {}
    for child in root:
      if child.attrib["name"] == "EGR_VALVE":
        if len(child.keys()) == 1:
          for param in child:
            params[param.attrib["name"]] = param.attrib["value"]

    confirm = get_message('MessageBox5')
    successMessage = get_message('Message32')
    clearScreen()

    # for k,v in params.iteritems():
    #   print k,v

    for idKey in identsList['X'].keys():
      identsList['X'][idKey] = ecu.get_id(identsList['X'][idKey], 1)

    print buttons[2]
    print
    ch = raw_input(confirm + ' <YES/NO>: ')
    while (ch.upper()!='YES') and (ch.upper()!='NO'):
      ch = raw_input(confirm + ' <YES/NO>: ')
    if ch.upper()!='YES':
        return
    
    for k,v in params.iteritems():
      identsList['X'][k] = v
      
    for v in identsList['X'].values():
      paramToSend += v

    ecu.run_cmd(commands['Cmd5'],paramToSend)
    

  functions = OrderedDict()
  functions[2] = resetEGRValve

  infoMessage = get_message('Message1')
  mainText = get_message('Title')
  confirmButton = get_message_by_id('8405')

  print mainText
  print
  print infoMessage
  print

  choice = Choice(buttons.values(), "Choose :")
  for key, value in buttons.iteritems():
    if value == choice[0]:
        functions[key]()


  # print correctEcu.vdiag
  # print correctEcu.ncalib
  # for l in correctEcu.buttons.keys():
  #     print l
  #     print str(correctEcu.buttons[l])



  # value1, datastr1 = ecu.get_id(ScmParam['VDiag'])
  # value2, datastr2 = ecu.get_id(ScmParam['Ncalib'])
  # print pyren_encode(datastr1)
  # print pyren_encode(datastr2)

  ch = raw_input('')    
  #
  #     Important information
  #
  # clearScreen()
#   value1, datastr1 = ecu.get_id(ScmParam['Injecteur1'])
#   value2, datastr2 = ecu.get_id(ScmParam['Injecteur2'])
#   value3, datastr3 = ecu.get_id(ScmParam['Injecteur3'])
#   value4, datastr4 = ecu.get_id(ScmParam['Injecteur4'])
#   print pyren_encode(header)
#   print get_message('TexteTitre')  
#   print '*'*80
#   print pyren_encode(datastr1)
#   print pyren_encode(datastr2)
#   print pyren_encode(datastr3)
#   print pyren_encode(datastr4)
#   print '*'*80

#   ch = raw_input('Are you ready to change the Injector Codes? <y/n>:')
#   while (ch.lower() !='y') and (ch.lower() !='n'):
#       ch = raw_input('Are you ready to change the Injector Codes? <y/n>:')
#   if ch.lower()!='y': return

#   #
#   #     INFO
#   #
  
#   clearScreen()
#   value1, datastr1 = ecu.get_id(ScmParam['Injecteur1'])
#   value2, datastr2 = ecu.get_id(ScmParam['Injecteur2'])
#   value3, datastr3 = ecu.get_id(ScmParam['Injecteur3'])
#   value4, datastr4 = ecu.get_id(ScmParam['Injecteur4'])
#   print pyren_encode(header)
#   print '*'*80
#   print pyren_encode(datastr1)
#   print pyren_encode(datastr2)
#   print pyren_encode(datastr3)
#   print pyren_encode(datastr4)
#   print '*'*80
#   print pyren_encode('Permitted Characters'),get_message('PermittedCharacters')  
#   print '*'*80
  
#   #
#   #    Receive data length and format from scenario
#   #

#   nbCC = ScmParam['nbCaractereCode']
#   nbCC = int(nbCC)
#   if nbCC !=6 and nbCC !=7 and nbCC !=16:
#     ch = raw_input('Error nbCaractereCode in scenario xml')
#     return
#   isHEX = ScmParam['FormatHexadecimal']
#   isHEX = int(isHEX)
#   if isHEX != 0 and isHEX != 1:
#     ch = raw_input('Error FormatHexadecimal in scenario xml')
#     return
#   prmCHAR = ScmParam['PermittedCharacters']
#   if len(prmCHAR) << 16 and len(prmCHAR) >> 33:
#     ch = raw_input('Error PermittedCharacters in scenario xml')
#     return
 
#   #
#   #    Get IMA from input
#   #

  
#   ch1 = raw_input(get_message('dat_Cylindre1')+': ').upper()
#   while not (all (c in prmCHAR for c in ch1.upper()) and (len(ch1)==nbCC)):
#       ch1 = raw_input(get_message('dat_Cylindre1')+': ').upper()
#   ch2 = raw_input(get_message('dat_Cylindre2')+': ').upper()
#   while not (all (c in prmCHAR for c in ch2.upper()) and (len(ch2)==nbCC)):
#       ch2 = raw_input(get_message('dat_Cylindre2')+': ').upper()
#   ch3 = raw_input(get_message('dat_Cylindre3')+': ').upper()
#   while not (all (c in prmCHAR for c in ch3.upper()) and (len(ch3)==nbCC)):
#       ch3 = raw_input(get_message('dat_Cylindre3')+': ').upper()
#   ch4 = raw_input(get_message('dat_Cylindre4')+': ').upper()
#   while not (all (c in prmCHAR for c in ch4.upper()) and (len(ch4)==nbCC)):
#       ch4 = raw_input(get_message('dat_Cylindre4')+': ').upper()
      
#  #
#  #  Check all data format of input
#  #
 
#   chk = ( ch1 + ch2 + ch3 + ch4 )

#   if isHEX == 1 and not (all (c in prmCHAR for c in chk.upper()) and (len(chk) == nbCC * 4)):
#       print '*'*80
#       ch = raw_input('Hexdata check failed. Press ENTER to exit')
#       return
#   elif isHEX == 0 and not (all (c in prmCHAR for c in chk.upper()) and (len(chk) == nbCC * 4)) :
#       print '*'*80
#       ch = raw_input('ASCII check failed. Press ENTER to exit')
#       return
#   else:
#       print '*'*80
#       ch = raw_input('All checks passed successfull. Press ENTER to continue')
  

#   #
#   # If all checks are successful script prepares the data according to their type
#   #

#   if isHEX == 1:
#       inj_code = ( ch1 + ch2 + ch3 + ch4 ).upper()  
#   elif isHEX == 0:
#       inj_code = ASCIITOHEX ( ch1 + ch2 + ch3 + ch4 ).upper()
#   else:
#       print '*'*80
#       ch = raw_input('!!!!!!!!There is a bug somwhere in the scenario, operation aborted!!!!!!!!!')
#       return

#   #
#   # print old and new data 
#   #
   
#   clearScreen()
#   print '*'*80
#   print pyren_encode('Old injector codes')
#   print pyren_encode(datastr1)
#   print pyren_encode(datastr2)
#   print pyren_encode(datastr3)
#   print pyren_encode(datastr4)
#   print '*'*80
#   print pyren_encode('New injector codes')
#   print get_message('dat_Cylindre1'),pyren_encode(':'),pyren_encode(ch1)
#   print get_message('dat_Cylindre2'),pyren_encode(':'),pyren_encode(ch2)
#   print get_message('dat_Cylindre3'),pyren_encode(':'),pyren_encode(ch3)
#   print get_message('dat_Cylindre4'),pyren_encode(':'),pyren_encode(ch4)
#   print '*'*80
#   print pyren_encode('Permitted Characters'),get_message('PermittedCharacters')
#   print '*'*80

 
#   ch = raw_input('Start injectors writing? YES/QUIT>')
#   while (ch.upper()!='YES') and (ch.upper()!='QUIT'):
#       ch = raw_input('Start injectors codes writing? YES/QUIT>')
#   if ch.upper()!='YES':
#       return

#   #
#   #     Write Injector Codes
#   #

#   clearScreen()
#   cmd = ecu.get_ref_cmd(get_message('EcritureCodeInjecteur'))
#   print '*'*80
#   responce = ecu.run_cmd(ScmParam['EcritureCodeInjecteur'],inj_code)
#   value5, datastr5 = ecu.get_id(ScmParam['Injecteur1'])
#   value6, datastr6 = ecu.get_id(ScmParam['Injecteur2'])
#   value7, datastr7 = ecu.get_id(ScmParam['Injecteur3'])
#   value8, datastr8 = ecu.get_id(ScmParam['Injecteur4'])
#   print '*'*80
#   print pyren_encode('Old injector codes')
#   print pyren_encode(datastr1)
#   print pyren_encode(datastr2)
#   print pyren_encode(datastr3)
#   print pyren_encode(datastr4)
#   print '*'*80
#   print pyren_encode('New injector codes')
#   print pyren_encode(datastr5)
#   print pyren_encode(datastr6)
#   print pyren_encode(datastr7)
#   print pyren_encode(datastr8)
#   print '*'*80

#   ch = raw_input('Press ENTER to exit')
#   return
