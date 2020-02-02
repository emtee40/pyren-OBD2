#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys, os
import math

import xml.dom.minidom

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

import mod_globals
from   mod_utils    import *

class decu_data:

  Name                  = ""
  Comment               = ""
  Mnemonic              = ""
  Description           = ""
  Bytes                 = False
  BytesCount            = 1
  BytesASCII            = False
  Bits                  = False
  BitsCount             = 8
  signed                = False
  Binary                = False
  List                  = {}
  Scaled                = False
  Step                  = 1.0
  Offset                = 0.0
  DivideBy              = 1.0
  Format                = ""
  Unit                  = ""
  
  def __str__(self):
    
    li = ''
    for k in self.List.keys():
      li = li + '\n'+'%4s:%s'%(k,self.List[k])

    out = '''
  Name                  = %s
  Comment               = %s
  Mnemonic              = %s
  Description           = %s
  Bytes                 = %d
  BytesCount            = %d
  BytesASCII            = %d
  Bits                  = %d
  BitsCount             = %d
  signed                = %d
  Binary                = %d
  List                  = %s
  Scaled                = %d
  Step                  = %f
  Offset                = %f
  DivideBy              = %f
  Format                = %s
  Unit                  = %s 
  ''' % (self.Name, self.Comment, self.Mnemonic, self.Description, self.Bytes,
      self.BytesCount, self.BytesASCII, self.Bits, self.BitsCount, self.signed, self.Binary,
      li, self.Scaled, self.Step, self.Offset, self.DivideBy, self.Format, self.Unit)
    
    return pyren_encode(out)  
   


  def __init__(self, dt):
  
    ns = {'ns0': 'http://www-diag.renault.com/2002/ECU',
          'ns1': 'http://www-diag.renault.com/2002/screens'}
  
    self.Name  = dt.attrib["Name"]
    #print self.Name

    self.Comment = ""
    Comment = dt.findall("ns0:Comment",ns)
    if Comment: self.Comment=Comment[0].text

    self.Mnemonic = ""
    Mnemonic = dt.findall("ns0:Mnemonic",ns)
    if Mnemonic: self.Mnemonic=Mnemonic[0].text

    self.Description = ""
    Description = dt.findall("ns0:Description",ns)
    if Description: self.Description=Description[0].text.replace('<![CDATA[','').replace(']]>','')

    Bytes = dt.findall("ns0:Bytes", ns)
    if len(Bytes):
      by = Bytes[0]
      
      self.Bytes = True
      
      self.BytesCount = 1
      if "count" in by.attrib.keys():
        self.BytesCount = int(math.ceil(float(by.attrib["count"])))
      
      self.BitsCount = self.BytesCount * 8

      self.BytesASCII = False
      if "ascii" in by.attrib.keys():
        self.BytesASCII = True
    
    Bits = dt.findall("ns0:Bits", ns)
    if Bits:
      bi = Bits[0]
    
      self.Bits = True
      
      self.BitsCount = 8
      if "count" in bi.attrib.keys():
        self.BitsCount = int(bi.attrib["count"])

      self.BytesCount = int(math.ceil(self.BitsCount / 8.0))

      self.signed = False
      if "signed" in bi.attrib.keys():
        self.signed = True
    
      self.Binary = False
      Binary = bi.findall("ns0:Binary", ns)
      if len(Binary): self.Binary = True
     
      self.List = {}
      Items = bi.findall("ns0:List/ns0:Item", ns)
      if len(Items):
        for i in Items:
          Value = 0
          if "Value" in i.attrib.keys():
            Value = int(i.attrib["Value"])
          
          Text  = ""
          if "Text" in i.attrib.keys():
            Text = i.attrib["Text"]
          if ';' in Text: Text = Text.split(';')[0].strip()
          self.List[Value] = Text
          
      self.Scaled = False
      Scaled = bi.findall("ns0:Scaled", ns)
      if len(Scaled):
        sc = Scaled[0]
        
        self.Scaled = True
        
        self.Step = 1.0
        if "Step" in sc.attrib.keys():
          self.Step = float(sc.attrib["Step"])
        
        self.Offset = 0.0
        if "Offset" in sc.attrib.keys() and sc.attrib["Offset"]!='':
          self.Offset = float (sc.attrib["Offset"])

        self.DivideBy = 1.0
        if "DivideBy" in sc.attrib.keys():
          self.DivideBy = float (sc.attrib["DivideBy"])

        self.Format = ""
        if "Format" in sc.attrib.keys():
          self.Format = sc.attrib["Format"]

        self.Unit = ""
        if "Unit" in sc.attrib.keys():
          self.Unit = sc.attrib["Unit"]

class decu_datas:
  def __init__(self, data_list, xdoc):

    ns = {'ns0': 'http://www-diag.renault.com/2002/ECU',
          'ns1': 'http://www-diag.renault.com/2002/screens'}
          
    data = xdoc.findall('ns0:Target/ns0:Datas', ns)
  
    datas = data[0].findall('ns0:Data', ns)
    if datas:
      for dt in datas:
        data = decu_data( dt )
        data_list[data.Name] = data
        #print data
        