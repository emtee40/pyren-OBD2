#!/usr/bin/env python

from mod_utils       import Choice
from xml.dom.minidom import parse
import xml.dom.minidom

class ecu_screen_dataref:
  
  name = ""
  type = ""
  
  def __init__(self, dr, n="", t=""):
    if len(n):
      self.name = n
      self.type = t
      return
    self.name = dr.getAttribute("name")
    self.type = dr.getAttribute("type")

class ecu_own_screen:

  datarefs = []
  functions = []
  name = ""

  def __init__(self, n):
    self.name = n
    
class ecu_screen_subfunction:
  
  datarefs      = []
  name = ""
  text = ""
  
  def __init__(self, sfu, tran ):
    self.name = sfu.getAttribute("name")
    codetext = sfu.getAttribute("codetext")
    defaultText = sfu.getAttribute("defaultText")
    self.text = ""
    if codetext:
      if codetext in tran.keys():
        self.text = tran[codetext]
      elif defaultText:
        self.text = defaultText
    DataRefs = sfu.getElementsByTagName("DataRef")
    if DataRefs:
      self.datarefs = []
      for dr in DataRefs:
        dataref = ecu_screen_dataref( dr ) 
        self.datarefs.append( dataref )

class ecu_screen_function:
  
  subfunctions  = []
  datarefs      = []
  name = ""
  text = ""
  
  def __init__(self, fu, tran ):
    self.name = fu.getAttribute("name")
    codetext = fu.getAttribute("codetext")
    defaultText = fu.getAttribute("defaultText")
    self.text = ""
    if codetext:
      if codetext in tran.keys():
        self.text = tran[codetext]
      elif defaultText:
        self.text = defaultText
    SubFunctions = fu.getElementsByTagName("SubFunction")
    if SubFunctions:
      self.subfunctions = []
      for sfu in SubFunctions:
        subfunction = ecu_screen_subfunction( sfu, tran )
        self.subfunctions.append( subfunction )
      return
    DataRefs = fu.getElementsByTagName("DataRef")
    if DataRefs:
      self.datarefs = []
      for dr in DataRefs:
        dataref = ecu_screen_dataref( dr ) 
        self.datarefs.append( dataref )

class ecu_screen:
  
  functions  = []
  datarefs   = []
  name = ""
  text = ""
  
  def __init__(self, sc, tran = None):
    if tran is None:
      self.name = sc
      return
    self.name = sc.getAttribute("name")
    codetext = sc.getAttribute("codetext")
    defaultText = sc.getAttribute("defaultText")
    self.text = ""
    if codetext:
      if codetext in tran.keys():
        self.text = tran[codetext]
      elif defaultText:
        self.text = defaultText
    Functions = sc.getElementsByTagName("Function")
    if Functions:
      self.functions = []
      for fu in Functions:
        function = ecu_screen_function( fu, tran )
        self.functions.append( function )
      return
    DataRefs = sc.getElementsByTagName("DataRef")
    if DataRefs:
      self.datarefs = []
      for dr in DataRefs:
        dataref = ecu_screen_dataref( dr ) 
        self.datarefs.append( dataref )
         
class ecu_screens:
  
  def __init__(self, screen_list, mdoc, tran ):
    Screens = mdoc.getElementsByTagName("Screens").item(0)
    if Screens:
      Screen = Screens.getElementsByTagName("Screen")
      if Screen:
        for sc in Screen:
          screen = ecu_screen( sc, tran )
          if len(screen.functions)>0 or len(screen.datarefs)>0:
            screen_list.append(screen)
        