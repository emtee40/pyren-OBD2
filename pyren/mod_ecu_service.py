#!/usr/bin/env python

from mod_utils          import Choice
from mod_utils          import pyren_encode
from xml.dom.minidom    import parse
from xml.dom.minidom    import parseString

import mod_globals

import xml.dom.minidom
import time
import sys

class ecu_mnemolocation:
  name  = ""
  startByte = ""
  startBit  = ""
  rOffset   = ""
  
  def __str__(self):
    out = 'name=%-50s startByte=%2s startBit=%s rOffset=%s\n' % (
       self.name, self.startByte, self.startBit, self.rOffset)
    return pyren_encode(out) 
     
  def __init__(self, ml ):
    self.name = ml.getAttribute("name")
    self.startByte = ml.getAttribute("startByte")
    self.startBit  = ml.getAttribute("startBit")
    self.rOffset   = ml.getAttribute("rOffset")

class ecu_service_response:
  val   = ""
  status = 0
  mnemolocations = {}
  
  def __init__(self, sr ):
    self.val = sr.getAttribute("val")
    self.status = sr.getAttribute("status")
    
    self.mnemolocations = {}

    MnemoLocations = sr.getElementsByTagName("MnemoLocation")
    if MnemoLocations:
      for ml in MnemoLocations:
        mnemoloc = ecu_mnemolocation( ml )
        self.mnemolocations[mnemoloc.name] = mnemoloc

def rspStrip( rsp, req ):
  rsp = rsp.replace( req, '' )
  rsp = rsp.replace( '>', '' )
  rsp = rsp.replace( ' ', '' )
  rsp = rsp.replace( '\t', '' )
  return rsp

def executeService( service, elm, status = [], param = "", cache = False ):
  #print "Start of execution service: ", service.id
  
  #tb = time.time()   #start time 
  #tc = tb

  sentDataIdentifires = [] #dataids sent in one 22 request, nedded for a response parse
  performanceMode = mod_globals.opt_perform and elm.performanceModeLevel > 1 

  commandToSend = service.startReq

  if performanceMode and elm.currentScreenDataIds:
    commandToSend, sentDataIdentifires = prepareComplexRequest(service.startReq, elm.currentScreenDataIds)
    
  if len(service.params)>0:  # but I support only one and do not support SnapShot
    if service.params[0]['type']=='DTC':
      param = mod_globals.ext_cur_DTC
    pos = (int(service.params[0]['pos'])-1)*2
    commandToSend = commandToSend[:pos]+param+commandToSend[pos:]
  
  try:
    localDelay = int(service.delay)
  except ValueError:
    localDelay = 0
    
  if len(service.startNextDelay)>1:
    localDelay = service.startNextDelay
  
  rsp = elm.request( commandToSend, '', cache, localDelay )
  rsp = rspStrip( rsp, commandToSend )
  first_rsp = rsp

  if performanceMode and sentDataIdentifires:
    first_rsp = parseComplexResponse(elm, service.simpleRsp, rsp, sentDataIdentifires)

  #print "Status:", status
  #print "Delay:",localDelay,
  #print "startReq	", service.startReq
  #print "repeatReq	", service.repeatReq
  #print "simpleRsp	", service.simpleRsp
  #print "startNextDelay	", service.startNextDelay
  #print "repeatNextDelay	", service.repeatNextDelay
  #print "responces	", service.responces
  #print "responcesRepeat	", service.responcesRepeat
  #print "startRepeatInProgres	", service.startRepeatInProgres
  #print "repeatRepeatInProgres 	", service.repeatRepeatInProgres 
  #print "params ", service.params

  #te = time.time()   #end time 
  
  #check for simple responce
  if len(service.simpleRsp) and rsp.startswith( service.simpleRsp ):
    return first_rsp
  
  #if rsp in service.responces.keys():
  for rspk in service.responces.keys():
    if rsp.startswith( rspk ):
      if rsp in service.responces.keys() and \
         service.responces[rsp].status in status.keys():
        #print '\r',' '*80,"\rStatus:",pyren_encode(status[service.responces[rsp].status]),
        print "\nStatus:",pyren_encode(status[service.responces[rsp].status]),
      sys.stdout.flush()
      break
    
  #if rsp not in service.startRepeatInProgres.keys():
  flag = True;
  for rspk in service.startRepeatInProgres.keys():
    if rsp.startswith( rspk ):
      flag = False;
      break
  if flag:
    #print
    return first_rsp
    
  #Repeat
  commandToSend = service.repeatReq
  localDelay = service.delay
  if len(service.repeatNextDelay)>1:
    localDelay = service.repeatNextDelay
  count = 0
  while count<100: # just for not to step into infinite loop
    count += 1
    rsp = elm.request( commandToSend, '', cache, localDelay )
    rsp = rspStrip( rsp, commandToSend )
  
    #if rsp in service.responces.keys():
    for rspk in service.responces.keys():
      if rsp.startswith( rspk ):
        if rsp in service.responces.keys() and \
           service.responces[rsp].status in status.keys():
          #print '\r',' '*80,"\rStatus:",pyren_encode(status[service.responces[rsp].status]), count,
          print "\nStatus:",pyren_encode(status[service.responces[rsp].status]),
        sys.stdout.flush()
        break
    
    #if rsp not in service.repeatRepeatInProgres.keys():
    flag = True;
    for rspk in service.repeatRepeatInProgres.keys():
      if rsp.startswith( rspk ):
        flag = False;
        break
    if flag:
      #print
      return first_rsp
  
  print "\nSomething went wrong. Counter reached maximum value.\n"
  return ""  

def prepareComplexRequest(request, screenDataIds):
  commandToSend = request
  sentDataIdentifires = []
  screenDataIdsNumber = len(screenDataIds[0])

  if screenDataIdsNumber > 1:
    firstDataId = screenDataIds[0][0].id
    if firstDataId == request[2:]:
      commandToSend = request[:2]
      for did in screenDataIds[0]:
        commandToSend += did.id
      
      sentDataIdentifires = screenDataIds.pop(0) 
   
  return commandToSend, sentDataIdentifires

def parseComplexResponse(elm, positiveRsp, response, sentDataIds):
  first_rsp = ''
  posInResp = 2
  byteLength = 2
  sentDataIdsLength = len(sentDataIds)
  
  for i in range(sentDataIdsLength):
    dataId = response[posInResp:posInResp + 2 * byteLength]
    posInResp += 2 * byteLength
    didDataLength = int(sentDataIds[i].dataBitLength)/8
    didData = response[posInResp: posInResp + didDataLength * byteLength]
    posInResp += didDataLength * byteLength
    if i == 0:
      first_rsp = positiveRsp + dataId + didData
    
    resp = positiveRsp + dataId + didData
    resp = ' '.join(a+b for a,b in zip(resp[::2], resp[1::2]))

    elm.rsp_cache['22' + dataId] = resp

  return first_rsp

class ecu_service:

  id        = ""
  delay     = ""
  mode      = ""
  startReq  = ""
  repeatReq = ""
  simpleRsp = ""
  startNextDelay   = 0
  repeatNextDelay  = 0
  responces             = {}
  responcesRepeat       = {}
  startRepeatInProgres  = {}
  repeatRepeatInProgres = {}  
  params                = []
    
  def __init__(self, sv ):
    self.id = sv.getAttribute("serviceID")
    self.delay = sv.getAttribute("delay")
    self.mode  = sv.getAttribute("mode")
    
    self.responces             = {}
    self.responcesRepeat       = {}
    self.startRepeatInProgres  = {}
    self.repeatRepeatInProgres = {}  
    self.params                = []
    
    Start = sv.getElementsByTagName("Start")
    if Start:
      for st in Start:
        Request = st.getElementsByTagName("Request").item(0)
        if Request:
          #print Request.toprettyxml()
          self.startReq = Request.getAttribute("val")
          self.startNextDelay = Request.getAttribute("nextDelay")
          
          #self.params    = []
          Params = Request.getElementsByTagName("Params").item(0)
          if Params:
            Param = Params.getElementsByTagName("Param")
            if Param:
              for pr in Param:
                parm_dic = {}
                parm_dic["rank"] = pr.getAttribute("rank")
                parm_dic["type"] = pr.getAttribute("type")
                parm_dic["pos"] = pr.getAttribute("pos")
                if pr.hasAttribute("size"):
                  parm_dic["size"] = pr.getAttribute("size")
                else:
                  parm_dic["size"] = ''
                self.params.append( parm_dic )
        
        self.simpleRsp = ""
        Simple = st.getElementsByTagName("Simple").item(0)
        if Simple:
          resp = ecu_service_response( Simple )
          self.responces[resp.val] = resp
          self.simpleRsp = resp.val  
           
        RepeatInProgress = st.getElementsByTagName("RepeatInProgress").item(0)
        if RepeatInProgress:
          resp = ecu_service_response( RepeatInProgress )
          self.responces[resp.val] = resp 
          self.startRepeatInProgres[resp.val] = resp 
  
        Resp = st.getElementsByTagName("Resp")
        if Resp:
          for rsp in Resp:
            resp = ecu_service_response( rsp )
            self.responces[resp.val] = resp 
 
    Repeat = sv.getElementsByTagName("Repeat")
    if Repeat:
      for rep in Repeat:
        Request = rep.getElementsByTagName("Request").item(0)
        if Request:
          self.repeatReq = Request.getAttribute("val")
          self.repeatNextDelay = Request.getAttribute("nextDelay")
        
        Simple = rep.getElementsByTagName("Simple").item(0)
        if Simple:
          resp = ecu_service_response( Simple )
          self.responces[resp.val] = resp 
           
        RepeatInProgress = rep.getElementsByTagName("RepeatInProgress").item(0)
        if RepeatInProgress:
          resp = ecu_service_response( RepeatInProgress )
          self.responcesRepeat[resp.val] = resp 
          self.repeatRepeatInProgres[resp.val] = resp 
  
        Resp = rep.getElementsByTagName("Resp")
        if Resp:
          for rsp in Resp:
            resp = ecu_service_response( rsp )
            self.responcesRepeat[resp.val] = resp 
    
class ecu_services:
 
  def __init__(self, service_list, mdoc, opt, tran ):
    
    for k in opt.keys():
      if "Service" in k:
        xmlstr = opt[k]
        odom = xml.dom.minidom.parseString( xmlstr.encode( "utf-8" ) )
        odoc = odom.documentElement

        service = ecu_service( odoc )
        service_list[service.id] = service
       