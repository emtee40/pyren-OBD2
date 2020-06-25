#!/usr/bin/env python

from mod_utils              import Choice
from mod_utils              import ChoiceFromDict
from mod_utils              import hex_VIN_plus_CRC
from mod_utils              import pyren_encode
from mod_utils              import clearScreen
from mod_utils              import ASCIITOHEX
from mod_utils              import StringToIntToHex
from mod_ecu_service        import *
from mod_ecu_screen         import *
from mod_ecu_state          import get_state
from mod_ecu_parameter      import get_parameter
from mod_ecu_identification import get_identification
from mod_ecu_scenario       import playScenario

from xml.dom.minidom    import parse
from xml.dom.minidom    import parseString
import xml.dom.minidom

import os
import sys
import string

def runCommand( command, ecu, elm, param = '', cmdt = 'HEX' ):
  
  isService = 0
  isParam   = 0
  isInputList = 0  

  # check conditions
  
  if len(command.scenario):
    print "It is scenarium. I do not support them!!!\n"
    return

  if len(command.inputlist.keys()):  isInputList = 1
  for si in command.serviceID:
    isService = 1
    service = ecu.Services[si]
    if len(service.params):  isParam += len(service.params)
      
  if len(command.datarefs):
    print
    print "#"*26," Current values ","#"*26
    print ""
    strlst = []
    elm.clear_cache()
    for dr in command.datarefs:
      datastr = dr.name;
      help    = dr.type
      if dr.type=='State':
        datastr, help, csvd = get_state( ecu.States[dr.name], ecu.Mnemonics, ecu.Services, ecu.elm, ecu.calc )
      if dr.type=='Parameter':
        datastr, help, csvd = get_parameter( ecu.Parameters[dr.name], ecu.Mnemonics, ecu.Services, ecu.elm, ecu.calc )
      if dr.type=='Identification':
        datastr, help = get_identification( ecu.Identifications[dr.name], ecu.Mnemonics, ecu.Services, ecu.elm, ecu.calc )       
      print pyren_encode( datastr )
    print ""
    print "#"*70
    print ""
  
  chosenParameter = ''
  if isInputList and param not in command.inputlist.keys() :
    print "Not valid parameter. It isn't in inputList"
    return
  
  summary = ''
  for si in command.serviceID:
    service = ecu.Services[si]
    if len(service.params)==1 and chosenParameter=='':
      if len(service.params[0]['size']):
        parsize = int(service.params[0]['size'])
      else:
        parsize = 0
      ch = param
      ch = ch.strip().upper() 
      if cmdt=='HEX' and all(c in string.hexdigits for c in ch) and len(ch)%2==0:
          if parsize>0 and len(ch)!=parsize*2: continue
          chosenParameter = ch
      if cmdt=='VIN' and len(ch)==17 and ('I' not in ch) and ('O' not in ch):
          chosenParameter = hex_VIN_plus_CRC( ch )
      if cmdt=='DEC' and all (c in string.digits for c in ch):
          chosenParameter = StringToIntToHex( ch )
          #if parsize > 0 and len(chosenParameter) > parsize * 2:
          #  print 'Too long value'
          #  continue
          if parsize>0 and len(chosenParameter)<parsize*2:
              chosenParameter = '0'*(parsize*2 - len(chosenParameter)) + chosenParameter
      if cmdt=='ASCII':
          chosenParameter = ASCIITOHEX( ch )
          #if parsize > 0 and len(chosenParameter) > parsize * 2:
          #  print 'Too long value'
          #  continue
          if parsize>0 and len(chosenParameter)<parsize*2:
              chosenParameter = '0'*(parsize*2 - len(chosenParameter)) + chosenParameter
    if len(service.params)==1:
      ostr = "cmd:"+service.startReq+chosenParameter
      print pyren_encode("%-35s "%(ostr)),
      resp = executeService( service, elm, command.caracter, chosenParameter, False )
    elif len(service.params)==0:
      ostr = "cmd:"+service.startReq,
      print pyren_encode("%-35s "%(ostr)),
      resp = executeService( service, elm, command.caracter, "", False )
    print "rsp:", resp
    summary = summary + resp + '\n'
    
  return summary
  
def getDataId( req, ecu, elm ):
  
  #check if ecu is std-b or uds
  if not req.upper().startswith('2E'):
    return '', ''
    
  dataid = req[2:]
  
  #check if req not in DataIds 
  if dataid not in ecu.DataIds.keys():
    return '', ''
    
  # try to get current value of data
  getdatareq = '22'+dataid
  rsp = elm.request( getdatareq, '', False, 0 )
  rsp = rsp.replace(' ','')
  
  #check response
  if not rsp.upper().startswith('62'+dataid):
    return '', ''
    
  data = rsp.replace('62'+dataid,'')
  
  datalen = int(ecu.DataIds[dataid].dataBitLength) / 4
  
  #check response length
  if len(data)<datalen:
    return '', ''
    
  return dataid, data[:datalen]
 
def packData( ecu, mnemo, dataid, data, value ):
  di = ecu.DataIds[dataid]
  if mnemo not in di.mnemolocations.keys():
    return value
  pr = di.mnemolocations[mnemo]
  mn = ecu.Mnemonics[mnemo]
  
  littleEndian = True if int(mn.littleEndian) else False
  sb    = int(pr.startByte) - 1 
  bits  = int(mn.bitsLength)
  sbit  = int(pr.startBit)
  bytes = (bits+sbit-1)/8 + 1
  if littleEndian:
    lshift = sbit
  else:
    lshift = ((bytes+1)*8 - (bits+sbit))%8
    
  # shift value on bit offset 
  val = int(value,16)
  val = (val&(2**bits-1))<<lshift
  value = hex(val)[2:]
  #remove 'L'
  if value[-1:].upper()=='L':
    value = value[:-1]
  #add left zero if need 
  if len(value)%2:
    value = '0'+value
    
  # check hex
  if value.upper().startswith('0X'): value = value[2:]
  value = value.zfill(bytes*2).upper()
  if not all(c in string.hexdigits for c in value) and len(value)==bytes*2:
    return 'ERROR: Wrong value'

  #prepare base and mask
  base = data[sb*2:(sb+bytes)*2]
  binbase  = int(base,16)
  binvalue = int(value,16)
  mask     = (2**bits-1)<<lshift
  
  #print value, base, binbase, binvalue, mask

  #shift and mask
  binvalue = binbase ^ (mask & binbase) | binvalue

  #print binvalue 
   
  #remove '0x'
  value = hex(binvalue)[2:].upper()
  #remove 'L'
  if value[-1:].upper()=='L':
    value = value[:-1]
  value = value[-bytes*2:].zfill(bytes*2)

  data = data[0:sb*2] + value + data[(sb+bytes)*2:]

  return data

def executeCommand( command, ecu, elm, path ):
  
  clearScreen()
  
  isService = 0
  isParam   = 0
  isInputList = 0
  data      = ''
  dataid    = ''  

  print pyren_encode(path)
  
  print
  print "#"*29," Command parameters ","#"*29
  print
  print "Prerequisite :",pyren_encode(command.prerequisite)
  print 
  print "name         :",command.name
  print "codeMR       :",command.codeMR 
  print "label        :",pyren_encode(command.label)  
  print "type         :",command.type   
  print "scenario     :",command.scenario
  print "inputlist    +"
  for ilk in sorted(command.inputlist.keys()):
    isInputList = 1
    print pyren_encode("              : (%-5s) %s" % (ilk, command.inputlist[ilk]))    
  print "serviceID    +"
  for si in command.serviceID:
    isService = 1
    service = ecu.Services[si]
    if len(service.params)==0:
      print pyren_encode("              : (%-5s) %s" % (si, service.startReq))
    else:
      dataid, data = getDataId( service.startReq, ecu, elm )
      isParam += len(service.params)
      print pyren_encode("              : (%-5s) %s <Params>" % (si, service.startReq))
      
  # check conditions
  
  if len(command.scenario):
    #print "\nThere is scenarium. I do not support them!!!\n"
    #ch = raw_input('Press ENTER to exit ')
    #if 'show' in ch:
    playScenario( command, ecu, elm )
    return

  cmdt = ''
  if (isParam-isInputList)!=0:
    print "\nThere are parameters. \n"
    cmdt = raw_input('Press ENTER to exit or type [HEX, DEC, ASCII, VIN]: ')
    cmdt = cmdt.upper()
    if cmdt!='HEX' and cmdt!='DEC' and cmdt!='ASCII' and cmdt!='VIN': 
      return
    
  if isService==0:
    print "\nNothing to send!!!\n"
    ch = raw_input('Press ENTER to exit ')
    return
        
  # show datarefs if exist
  
  mnemo = ''
  if len(command.datarefs):
    print
    print "#"*26," Current values ","#"*26
    print ""
    strlst = []
    elm.clear_cache()
    for dr in command.datarefs:
      datastr = dr.name;
      help    = dr.type
      if dr.type=='State':
        datastr, help, csvd = get_state( ecu.States[dr.name], ecu.Mnemonics, ecu.Services, ecu.elm, ecu.calc )
        mnemo = ecu.States[dr.name].mnemolist[0]
      if dr.type=='Parameter':
        datastr, help, csvd = get_parameter( ecu.Parameters[dr.name], ecu.Mnemonics, ecu.Services, ecu.elm, ecu.calc )
        mnemo = ecu.Parameters[dr.name].mnemolist[0]
      if dr.type=='Identification':
        datastr, help = get_identification( ecu.Identifications[dr.name], ecu.Mnemonics, ecu.Services, ecu.elm, ecu.calc )       
        mnemo = ecu.Identifications[dr.name].mnemolist[0]
      print pyren_encode( datastr )
    print ""
    print "#"*70
    print ""
  
  ch = raw_input('Are you ready to execute the command? <yes/no>:')
  if ch.lower()!='yes': return
  
  chosenParameter = ""
  if isInputList:
    print
    print "#"*25," Make your choice ","#"*25
    print ""
    menu = {}
    menu = dict(command.inputlist)
    menu["<EXIT>"] = "Exit from command execution"
    choice = ChoiceFromDict(menu, "Choose :")
    if choice[0]=="<EXIT>": return
    chosenParameter = choice[0]
    
    print
    ps = "##### Your choice is ("+chosenParameter+") "+command.inputlist[chosenParameter]
    print pyren_encode( ps ), '#'*(70-len(ps))
    print

  if len(dataid) and dataid in ecu.DataIds.keys() and len(mnemo) and mnemo in ecu.Mnemonics.keys() and len(chosenParameter)>0:
    chosenParameter = packData( ecu, mnemo, dataid, data, chosenParameter )

    for si in command.serviceID:
      service = ecu.Services[si]
      if len(service.params)==1:
        ostr = "cmd:"+service.startReq+chosenParameter
        print pyren_encode("%-35s \n"%(ostr)),
      elif len(service.params)==0:
        ostr = "cmd:"+service.startReq,
        print pyren_encode("%-35s \n"%(ostr)),

    ch = raw_input('\nDo you agree? <yes/no>:')
    if ch.lower()!='yes': return
    
  
  print
  print "#"*29," Execution ","#"*29
  print
  for si in command.serviceID:
    service = ecu.Services[si]
    if len(service.params)==1 and chosenParameter=='':
      if len(service.params[0]['size']):
        parsize = int(service.params[0]['size'])
      else:
        parsize = 0
      print 'Parametr type:',service.params[0]['type'], ' size:',service.params[0]['size']
      while True:
        ch = raw_input(cmdt+':')
        ch = ch.strip().upper() 
        if cmdt=='HEX' and all(c in string.hexdigits for c in ch) and len(ch)%2==0:
          if parsize>0 and len(ch)!=parsize*2: continue
          chosenParameter = ch 
          break
        if cmdt=='VIN' and len(ch)==17 and ('I' not in ch) and ('O' not in ch):
          chosenParameter = hex_VIN_plus_CRC( ch )
          break 
        if cmdt=='DEC' and all (c in string.digits for c in ch):
          chosenParameter = StringToIntToHex( ch )
          if parsize > 0 and len(chosenParameter) > parsize * 2:
            print 'Too long value'
            continue
          if parsize > 0 and len(chosenParameter)<parsize*2:
              chosenParameter = '0'*(parsize*2 - len(chosenParameter)) + chosenParameter
          break
        if cmdt=='ASCII':
          chosenParameter = ASCIITOHEX( ch )
          if parsize > 0 and len(chosenParameter) > parsize * 2:
            print 'Too long value'
            continue
          if parsize > 0 and len(chosenParameter)<parsize*2:
              chosenParameter = '0'*(parsize*2 - len(chosenParameter)) + chosenParameter
          break
    if len(service.params)==1:
      ostr = "cmd:"+service.startReq+chosenParameter
      print pyren_encode("%-35s "%(ostr)),
      resp = executeService( service, elm, command.caracter, chosenParameter, False )
    elif len(service.params)==0:
      ostr = "cmd:"+service.startReq,
      print pyren_encode("%-35s "%(ostr)),
      resp = executeService( service, elm, command.caracter, "", False )
    print "rsp:", resp

  print
  print "#"*31," Done ","#"*31
  print
  
  try:
    ch = raw_input('Press ENTER to exit ')
  except (KeyboardInterrupt, SystemExit):
    print
    print 
    sys.exit()
   

class ecu_command:

  name    = ""
  agcdRef = ""
  codeMR  = ""
  type    = ""
  mask    = ""
  label   = ""
  prerequisite = ""
  datarefs    = []
  caracter    = {}
  inputlist   = {}
  serviceID   = []
  scenario    = ""
  
  def __init__(self, co, opt, tran ):
  
    self.name = co.getAttribute("name")
    self.agcdRef = co.getAttribute("agcdRef")
    self.codeMR  = co.getAttribute("codeMR")
    if not self.codeMR:
      self.codeMR = self.name
    self.type  = co.getAttribute("type")

    Mask = co.getElementsByTagName("Mask")
    if Mask:
      self.mask = Mask.item(0).getAttribute("value")
      
    Label = co.getElementsByTagName("Label")
    codetext = Label.item(0).getAttribute("codetext")
    defaultText = Label.item(0).getAttribute("defaultText")
    self.label = ""
    if codetext:
      if codetext in tran.keys():
        self.label = tran[codetext]
      elif defaultText:
        self.label = defaultText

    Prereq = co.getElementsByTagName("PrerequisiteMessage")
    if Prereq:
      codetext = Prereq.item(0).getAttribute("codetext")
      defaultText = Prereq.item(0).getAttribute("defaultText")
      self.prerequisite = ""
      if codetext:
        if codetext in tran.keys():
          self.prerequisite = tran[codetext]
        elif defaultText:
          self.prerequisite = defaultText
      
    scenario_tmp = co.getElementsByTagName("Scenario")
    if scenario_tmp:
      scenario_fc = scenario_tmp.item(0).firstChild
      if scenario_fc:
        self.scenario = scenario_fc.nodeValue
      else: 
        self.scenario = "" 

    self.datarefs = []
    CurrentInfo = co.getElementsByTagName("DataList")
    if CurrentInfo:
      for ci in CurrentInfo:
        DataRef = ci.getElementsByTagName("DataRef")
        if DataRef:
          for dr in DataRef:
            dataref = ecu_screen_dataref( dr ) 
            self.datarefs.append( dataref )
            
    self.inputlist = {}
    InputList = co.getElementsByTagName("InputList")
    if InputList:
      for corIL in InputList:
        CorrespondanceIL = corIL.getElementsByTagName("Correspondance")
        if CorrespondanceIL:
          for cil in CorrespondanceIL:
            ivalue = cil.getAttribute("value")            
            codetext  = cil.getAttribute("codetext")
            defaultText = cil.getAttribute("defaultText")
            itext = ""
            if codetext:
              if codetext in tran.keys():
                itext = tran[codetext]
              elif defaultText:
                itext = defaultText
              self.inputlist[ivalue]=itext

    self.caracter = {}
    Interpretation = co.getElementsByTagName("StatusInterpretation")
    if Interpretation:
      for corIT in Interpretation:
        CorrespondanceSI = corIT.getElementsByTagName("Correspondance")
        if CorrespondanceSI:
          for co in CorrespondanceSI:
            ivalue = co.getAttribute("value")            
            codetext  = co.getAttribute("codetext")
            defaultText = co.getAttribute("defaultText")
            itext = ""
            if codetext:
              if codetext in tran.keys():
                itext = tran[codetext]
              elif defaultText:
                itext = defaultText
              self.caracter[ivalue]=itext

    if "Command\\"+self.name not in opt.keys(): return
    xmlstr = opt["Command\\"+self.name]
    odom = xml.dom.minidom.parseString( xmlstr.encode( "utf-8" ) )
    odoc = odom.documentElement
    
    self.computation = ""
    self.serviceID = []
    ServiceID = odoc.getElementsByTagName("ServiceID")
    if ServiceID:
      for sid in ServiceID:
        self.serviceID.append(sid.getAttribute("name"))

    '''
    print '='*60
    print pyren_encode( self.name+" "+self.label )
    print "inputlist"
    for l in self.inputlist.keys():
      print pyren_encode( "\t"+self.inputlist[l] )
    print "caracter"
    for l in self.caracter.keys():
      print pyren_encode( "\t"+self.caracter[l] )
    '''  

class ecu_commands:
 
  def __init__(self, command_list, mdoc, opt, tran ):
    commands = mdoc.getElementsByTagName("Command")
    if commands:
      for co in commands:
        command = ecu_command( co, opt, tran )
        command_list[command.name] = command
        
