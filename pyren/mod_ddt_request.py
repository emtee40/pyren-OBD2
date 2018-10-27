#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys, os
import operator

import xml.dom.minidom

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

import mod_globals
from   mod_utils    import *

import xml.etree.ElementTree as et

class DataItem:
  Name      = ""
  Endian    = ""
  FirstByte = 1
  BitOffset = 0
  Ref       = False
  
  def __str__(self):
    out = 'Endian = %-5s FirstByte = %2d BitOffset = %2d  Ref = %1d Name = %s' % (self.Endian, 
       self.FirstByte, self.BitOffset, self.Ref, self.Name)
    return pyren_encode(out)  

  def __init__(self, di, defaultEndian ):
    self.Name  = di.attrib["Name"]

    if "Endian" in di.attrib.keys():
      self.Endian = di.attrib["Endian"]
    else:
      self.Endian=defaultEndian

    if "FirstByte" in di.attrib.keys ():
      self.FirstByte = int(di.attrib["FirstByte"])

    if "BitOffset" in di.attrib.keys ():
      self.BitOffset = int(di.attrib["BitOffset"])

    if "Ref" in di.attrib.keys ():
      Ref = di.attrib["Ref"]
      if Ref=='1': self.Ref=True
      else:        self.Ref=False
    else:
      self.Ref = False
  
class decu_request:

  Name                  = ""
  DossierMaintenabilite = None
  ManuelSend            = None
  DenyAccess            = []
  SentBytes             = ""
  SentDI                = {}
  VariableLength        = False
  ReceivedDI            = {}
  MinBytes              = 1
  ShiftBytesCount       = 0
  ReplyBytes            = ""
  
  def __str__(self):
  
    sd = ''
    for s in sorted(self.SentDI.values(), key=operator.attrgetter("FirstByte","BitOffset")):
      sd = sd + '\n'+str(s)
    sd = pyren_decode(sd)
    
    rd = ''
    for r in sorted(self.ReceivedDI.values(), key=operator.attrgetter("FirstByte","BitOffset")): 
      rd = rd + '\n'+str(r)
    rd = pyren_decode(rd)
    
    out = '''
  Name                  = %s
  DossierMaintenabilite = %d
  ManuelSend            = %d
  DenyAccess            = %s
  SentBytes             = %s
  SentDI                = %s
  VariableLength        = %d
  ReceivedDI            = %s
  MinBytes              = %d
  ShiftBytesCount       = %d
  ReplyBytes            = %s
    ''' % (self.Name, self.DossierMaintenabilite, self.ManuelSend, self.DenyAccess, self.SentBytes, 
           sd, self.VariableLength, rd, self.MinBytes, self.ShiftBytesCount, self.ReplyBytes)
    return pyren_encode(out)  
  
  def __init__(self, rq, defaultEndian ):
  
    ns = {'ns0': 'http://www-diag.renault.com/2002/ECU',
          'ns1': 'http://www-diag.renault.com/2002/screens'}
  
    self.Name  = rq.attrib["Name"]

    self.DossierMaintenabilite = False
    DossierMaintenabilite = rq.findall("ns0:DossierMaintenabilite",ns) #[0]
    if DossierMaintenabilite: self.DossierMaintenabilite=True

    self.ManuelSend = False
    ManuelSend = rq.findall("ns0:ManuelSend",ns)
    if ManuelSend: self.ManuelSend=True

    self.DenyAccess = []
    DenyAccess = rq.findall("ns0:DenyAccess",ns) #[0]
    if DenyAccess:
      NoSDS = DenyAccess[0].findall("ns0:NoSDS",ns)
      if NoSDS: self.DenyAccess.append('NoSDS')

      Supplier = DenyAccess[0].findall("ns0:Supplier",ns)
      if Supplier: self.DenyAccess.append('Supplier')

      Engineering = DenyAccess[0].findall("ns0:Engineering",ns)
      if Engineering: self.DenyAccess.append('Engineering')

      Plant = DenyAccess[0].findall("ns0:Plant",ns)
      if Plant: self.DenyAccess.append('Plant')

      AfterSales = DenyAccess[0].findall("ns0:AfterSales",ns)
      if AfterSales: self.DenyAccess.append('AfterSales')
    
    
    Sent = rq.findall("ns0:Sent",ns) #[0]
    if len(Sent):
      self.SentBytes = ""
      SentBytes = Sent[0].findall("ns0:SentBytes",ns)
      if len(SentBytes): self.SentBytes = SentBytes[0].text #[0].text

      self.VariableLength = False
      VariableLength = Sent[0].findall("ns0:VariableLength",ns)
      if len(VariableLength): self.VariableLength=True

      self.SentDI = {}
      DataItems = Sent[0].findall("ns0:DataItem",ns)
      if DataItems:
        for di in DataItems:
          dataitem = DataItem( di, defaultEndian )
          self.SentDI[dataitem.Name]=dataitem
          
    Received = rq.findall("ns0:Received",ns) #[0]
    if len(Received):
      self.MinBytes = 0
      MinBytes = Received[0].attrib["MinBytes"]
      if MinBytes: self.MinBytes = int(MinBytes)

      self.ShiftBytesCount = 0
      ShiftBytesCount = Received[0].findall("ns0:ShiftBytesCount",ns)
      if len(ShiftBytesCount): self.ShiftBytesCount = int(ShiftBytesCount[0].text) #[0].text)

      self.ReplyBytes = ""
      ReplyBytes = Received[0].findall("ns0:ReplyBytes",ns)
      if len(ReplyBytes): self.ReplyBytes = ReplyBytes[0].text #[0].text

      self.ReceivedDI = {}
      DataItems = Received[0].findall("ns0:DataItem",ns)
      if len(DataItems):
        for di in DataItems:
          dataitem = DataItem( di, defaultEndian  )
          self.ReceivedDI[dataitem.Name]=dataitem

class decu_requests:
  def __init__(self, requiest_list, xdoc):
  
    ns = {'ns0': 'http://www-diag.renault.com/2002/ECU',
          'ns1': 'http://www-diag.renault.com/2002/screens'}
  
    #try to find default endian
    tmpdoc = xdoc.findall('ns0:Target/ns0:Requests', ns) #getElementsByTagName("Requests")
    defaultEndian = ''
    
    if tmpdoc and ('Endian' in tmpdoc[0].attrib.keys()):
      defaultEndian = tmpdoc[0].attrib["Endian"]
    else:
      defaultEndian = "Big"
    
    requests = tmpdoc[0].findall("ns0:Request", ns)
    if requests:
      for rq in requests:
        request = decu_request( rq, defaultEndian )
        requiest_list[request.Name] = request
        #print request
        
