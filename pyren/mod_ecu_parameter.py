#!/usr/bin/env python

from mod_ecu_mnemonic   import *
from mod_utils          import Choice
from xml.dom.minidom    import parse
from xml.dom.minidom    import parseString
import xml.dom.minidom
import mod_globals

def get_parameter( pr, mn, se, elm, calc ):

  comp = pr.computation
  comp = comp.replace("&amp;","&")
  comp = comp.strip()

  for m in sorted(pr.mnemolist, key=len, reverse=True):
    
    val = get_mnemonic( mn[m], se, elm )
    if mn[m].type=="SNUM8" and int(val,16)>0x7f:
      val = str(int(val,16)-0x100)
    elif mn[m].type=="SNUM16" and int(val,16)>0x7fff:
      val = str(int(val,16)-0x10000)
    elif mn[m].type=="SNUM32" and int(val,16)>0x7fffffff:
      val = str(int(val,16)-0x100000000)
    else:
      val = "0x"+val
          
    comp = comp.replace(m, val) 
    
  pr.value = calc.calculate(comp)
  csv_data = unicode(pr.value) if mod_globals.opt_csv_human else pr.value
  if '.' in str(pr.value):
    pr.value = "%10.2f"%float(pr.value)
    
  tmpmin = str(pr.min)
  tmpmax = str(pr.max)
  if tmpmin.strip()=='0' and tmpmax.strip()=='0':
    tmpmin = ''
    tmpmax = ''
  
  if mod_globals.os=='android':
    return "%-6s %-41s %8s %-5s"%(pr.codeMR,pr.label,pr.value,pr.unit), pr.helps, csv_data 
  else:
    return "%-6s %-50s %5s %10s %-10s %-5s"%(pr.codeMR,pr.label,tmpmin,pr.value,pr.unit,tmpmax), pr.helps, csv_data 
  

class ecu_parameter:

  name    = ""
  agcdRef = ""
  codeMR  = ""
  label   = ""
  unit    = ""
  type    = ""
  min     = 0
  value   = 0
  max     = 0
  format  = 0
  domains     = []
  helps       = []
  computation = ""
  mnemolist   = []
  
  def __str__(self):
    hlps = '['
    for h in self.helps: hlps += '\'' + h + '\'\n'
    hlps += ']'
    out = '''
  name    = %s
  agcdRef = %s
  codeMR  = %s
  label   = %s
  unit    = %s
  type    = %s
  min     = %s
  value   = %s
  max     = %s
  format  = %s
  domains     = %s
  helps       = %s
  computation = %s
  mnemolist   = %s
    ''' % (self.name, self.agcdRef, self.codeMR, self.label, self.unit, self.type, 
           self.min, self.value, self.max, self.format, str(self.domains), hlps,
           self.computation, str(self.mnemolist))
    return pyren_encode(out)  
  
  def __init__(self, pr, opt, tran ):
    self.name = pr.getAttribute("name")
    self.agcdRef = pr.getAttribute("agcdRef")
    self.codeMR  = pr.getAttribute("codeMR")
    
    Label = pr.getElementsByTagName("Label")
    codetext = Label.item(0).getAttribute("codetext")
    defaultText = Label.item(0).getAttribute("defaultText")
    self.label = ""
    if codetext:
      if codetext in tran.keys():
        self.label = tran[codetext]
      elif defaultText:
        self.label = defaultText
            
    Unit = pr.getElementsByTagName("Unit")
    if Unit:
      codetext = Unit.item(0).getAttribute("codetext")
      defaultText = Unit.item(0).getAttribute("defaultText")
      self.unit = ""
      if codetext:
        if codetext in tran.keys():
          self.unit = tran[codetext]
        elif defaultText:
          self.unit = defaultText
      
    format_tmp = pr.getElementsByTagName("Format")
    if format_tmp:
      format = format_tmp.item(0).firstChild.nodeValue
    
    Limits = pr.getElementsByTagName("Limits")
    if Limits:
      self.min = Limits.item(0).getAttribute("min")
      self.max = Limits.item(0).getAttribute("max")
      
    self.domains = []
    Domains = pr.getElementsByTagName("Domains")
    if Domains:
      for dm in Domains:
        Domain = dm.getElementsByTagName("Domain")
        if Domain:
          domain = Domain.item(0).firstChild.nodeValue
          self.domains.append(domain)
          
    self.helps = []
    Helps = pr.getElementsByTagName("Helps")
    if Helps:
      for hl in Helps:
        Lines = hl.getElementsByTagName("Line")
        if Lines:
          for ln in Lines:
            line = ""
            Label = ln.getElementsByTagName("Label")
            if Label:
              for la in Label:
                codetext = la.getAttribute("codetext")
                defaultText = la.getAttribute("defaultText")
                if codetext:
                  if codetext in tran.keys():
                    line = line + tran[codetext]
                  elif defaultText:
                    line = line + defaultText
            self.helps.append(line+'\n')
    
    xmlstr = opt["Parameter\\"+self.name]
    odom = xml.dom.minidom.parseString( xmlstr.encode( "utf-8" ) )
    odoc = odom.documentElement
    
    self.computation = ""
    Computation = odoc.getElementsByTagName("Computation")
    if Computation:
      for cmpt in Computation:
        self.type = cmpt.getAttribute("type")
        tmp = cmpt.getElementsByTagName("Value").item(0).firstChild.nodeValue
        self.computation = tmp.replace(" ","").replace("&amp;","&")
        
        self.mnemolist = []
        Mnemo = cmpt.getElementsByTagName("Mnemo")
        if Mnemo:
          for mn in Mnemo:
            self.mnemolist.append(mn.getAttribute("name"))

class ecu_parameters:
 
  def __init__(self, parameter_list, mdoc, opt, tran ):
    Parameters = mdoc.getElementsByTagName("Parameter")
    if Parameters:
      for pr in Parameters:
        parameter = ecu_parameter( pr, opt, tran )
        parameter_list[parameter.name] = parameter
        
