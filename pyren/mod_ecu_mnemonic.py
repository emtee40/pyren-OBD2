#!/usr/bin/env python

from mod_ecu_service    import *

from mod_utils          import Choice
from xml.dom.minidom    import parse
from xml.dom.minidom    import parseString

import xml.dom.minidom
import string

def get_mnemonicDTC( m, resp ):
  '''This function uses synthetic response generated from real one '''
  
  bytes = 1
  bits  = int(m.bitsLength)
  if bits>7:
    bytes = bits/8
  
  hexval = "00"
  sb = int(m.startByte)-1
  if (sb*3+bytes*3-1)>(len(resp)):
    return hexval
  
  hexval = resp[sb*3:(sb+bytes)*3-1]
  hexval = hexval.replace(" ","")
  
  if bits<8:
    val = int(hexval,16)
    val = (val<<int(m.startBit)>>(8-bits))&(2**bits-1)
    hexval = str(val)

  return hexval


def get_mnemonic( m, se, elm, raw = 0 ):

  if not m.serviceID and mod_globals.ext_cur_DTC:
    for sid in se.keys():
      if se[sid].startReq == "120004"+ mod_globals.ext_cur_DTC[:4]:
        m.startByte = se[sid].responces[se[sid].responces.keys()[0]].mnemolocations[m.name].startByte
        m.startBit = se[sid].responces[se[sid].responces.keys()[0]].mnemolocations[m.name].startBit
        m.request = se[sid].startReq
        m.positive = se[sid].simpleRsp
        m.delay = '100' #don't know how much it should be

  #get responce
  if len(m.sids)>0:
    for sid in m.sids:
      service = se[sid]
      resp = executeService( service, elm, [], "", True )   
  else:
    resp = elm.request( m.request, m.positive, True, m.delay )
  
  #format responce  
  resp = resp.strip().replace(' ','')
  if not all(c in string.hexdigits for c in resp): resp = ''
  resp = ' '.join(a+b for a,b in zip(resp[::2], resp[1::2]))
  if len(m.startByte)==0: m.startByte = u'01'

  #prepare local variables  
  sb     = int(m.startByte) - 1
  bits   = int(m.bitsLength)
  sbit   = int(m.startBit)
  bytes  = (bits+sbit-1)/8+1
  rshift = ((bytes+1)*8 - (bits+sbit))%8
  
  #check length of responce
  if (sb*3+bytes*3-1)>(len(resp)):
    return '00'
  
  #extract hex
  hexval = resp[sb*3:(sb+bytes)*3-1]
  hexval = hexval.replace(" ","")

  if raw:
    if resp.startswith(m.positive):
      return hexval
    else:
      return 'ERROR'

  #shift and mask
  val = (int(hexval,16)>>rshift)&(2**bits-1)
  
  #format result
  hexval = hex(val)[2:]
  #remove 'L'
  if hexval[-1:].upper()=='L':
    hexval = hexval[:-1]
  #add left zero if need
  if len(hexval)%2:
    hexval = '0'+hexval

  #revert byte order if little endian
  if m.littleEndian == '1':
    a = hexval
    b = ''
    if not len(a) % 2:
      for i in range(0,len(a),2):
        b = a[i:i+2]+b
      hexval = b
  
  return hexval

def get_SnapShotMnemonic(m, se, elm, dataids):
  snapshotService = ""
  posInResp = 0
  for sid in se:
    if len(se[sid].params) > 1:
      if se[sid].params[1]['type'] == 'Snapshot':
        snapshotService = se[sid]
  
  resp = executeService( snapshotService, elm, [], "", True )
  if mod_globals.opt_demo and not resp or not resp.startswith(snapshotService.simpleRsp):
    return "00"
  resp = resp.strip().replace(' ','')
  if not all(c in string.hexdigits for c in resp): resp = ''
  resp = ' '.join(a+b for a,b in zip(resp[::2], resp[1::2]))
  numberOfIdentifiers = int("0x" + resp[7*3:8*3-1],16)
  resp = resp[8*3:]

  didDict = {}
  for x in range(numberOfIdentifiers):
    dataId = resp[posInResp:posInResp + 2*3].replace(" ", "")
    posInResp += 2*3
    didDataLength = int(dataids[dataId].dataBitLength)/8
    didData = resp[posInResp: posInResp + didDataLength*3]
    posInResp += didDataLength*3
    didDict[dataId] = didData

  startByte = ""
  startBit = ""
  dataId = ""
  for did in dataids.keys():
    for mn in dataids[did].mnemolocations.keys():
      if mn == m.name:
        dataId = did
        startByte = dataids[dataId].mnemolocations[m.name].startByte
        startBit = dataids[dataId].mnemolocations[m.name].startBit

  #prepare local variables  
  sb     = int(startByte) - 1
  bits   = int(m.bitsLength)
  sbit   = int(startBit)
  bytes  = (bits+sbit-1)/8+1
  rshift = ((bytes+1)*8 - (bits+sbit))%8

  #check length of responce
  if (sb*3+bytes*3-1)>(len(didDict[dataId])):
    return '00'
  
  #extract hex
  hexval = didDict[dataId][sb*3:(sb+bytes)*3-1]
  hexval = hexval.replace(" ","")

  #shift and mask
  val = (int(hexval,16)>>rshift)&(2**bits-1)
  
  #format result
  hexval = hex(val)[2:]
  #remove 'L'
  if hexval[-1:].upper()=='L':
    hexval = hexval[:-1]
  #add left zero if need
  if len(hexval)%2:
    hexval = '0'+hexval

  #revert byte order if little endian
  if m.littleEndian == '1':
    a = hexval
    b = ''
    if not len(a) % 2:
      for i in range(0,len(a),2):
        b = a[i:i+2]+b
      hexval = b
  
  return hexval

class ecu_mnemonic:
  
  name          = ""
  littleEndian  = ""
  type          = ""
  bitsLength    = ""
  serviceID     = ""
  startByte     = ""
  startBit      = ""
  request       = ""
  delay         = ""
  nextDelay     = ""
  rOffset       = ""
  positive      = ""
  sids          = []
  
  def __str__(self):
    out = '''
  name          = %s
  littleEndian  = %s
  type          = %s
  bitsLength    = %s
  serviceID     = %s
  startByte     = %s
  startBit      = %s
  request       = %s
  delay         = %s
  nextDelay     = %s
  rOffset       = %s
  positive      = %s
  sids          = %s
    ''' % (self.name, self.littleEndian, self.type, self.bitsLength, self.serviceID,
           self.startByte, self.startBit, self.request, self.delay, self.nextDelay,
           self.rOffset, self.positive, self.sids)
    return pyren_encode(out)

    
  def __init__(self, sv, opt ):
    self.name  = sv.getAttribute("name")
    
    #print '*'*60
    #print sv.toprettyxml()

    MnemoDatas = sv.getElementsByTagName("MnemoDatas").item(0)
    if MnemoDatas:
      self.littleEndian = MnemoDatas.getAttribute("littleEndian")
      self.type         = MnemoDatas.getAttribute("type")
      self.bitsLength   = MnemoDatas.getAttribute("bitsLength")
      #print "type=",self.type

    self.sids = []
    ServiceID = sv.getElementsByTagName("ServiceID").item(0)
    ServiceIDs = sv.getElementsByTagName("ServiceID")
    if ServiceIDs:
      for ServiceID in ServiceIDs: 
        self.serviceID = ServiceID.getAttribute("name")
        self.sids.append(self.serviceID)
      
        srvxmlstr = opt["Service\\"+self.serviceID]
        sdom = xml.dom.minidom.parseString( srvxmlstr.encode( "utf-8" ) )
        sdoc = sdom.documentElement
        
        self.delay = sdoc.getAttribute("delay")
        if len(self.delay)==0: self.delay = "0"
        
        Start = sdoc.getElementsByTagName("Start").item(0)
        if Start:
          Request = sdoc.getElementsByTagName("Request").item(0)
          if Request:
            self.request = Request.getAttribute("val")
            self.nextDelay = Request.getAttribute("nextDelay")
          
        MnemoLocation = sdoc.getElementsByTagName("MnemoLocation")
        for m in MnemoLocation:
          if m.getAttribute("name") == self.name:
            self.startByte = m.getAttribute("startByte")
            self.startBit = m.getAttribute("startBit")
            self.rOffset = m.getAttribute("rOffset")
  
        self.positive = ""
        
        Simple = sdoc.getElementsByTagName("Simple").item(0)
        if Simple:
          self.positive = Simple.getAttribute("val")
          #print "positive", self.positive
          #return
          continue
             
        RepeatInProgress = sdoc.getElementsByTagName("RepeatInProgress").item(0)
        if RepeatInProgress:
          self.positive = RepeatInProgress.getAttribute("val")
          #print "positive", self.positive
          #return
          continue
  
  
class ecu_mnemonics:
 
  def __init__(self, mnemonic_list, mdoc, opt, tran ):
    
    for k in opt.keys():
      if "Mnemonic" in k:
        xmlstr = opt[k]
        odom = xml.dom.minidom.parseString( xmlstr.encode( "utf-8" ) )
        odoc = odom.documentElement

        mnemonic = ecu_mnemonic( odoc, opt )
        mnemonic_list[mnemonic.name] = mnemonic
