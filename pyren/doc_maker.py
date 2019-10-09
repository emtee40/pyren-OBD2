#!/usr/bin/env python

import sys, os, glob, copy
import mod_globals
from mod_optfile   import *
from mod_scan_ecus import families as families
from mod_dfg       import class_dfg
from mod_mtc       import acf_MTC_compare_doc

import xml.etree.ElementTree as et

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

import pickle
#from   mod_acf_func     import ACE

style = '''
div.zdiagnostic {
	background-color	:	white;
}

div.testgrp {
	border-style		: 	outset;
}

div.test1 {
	color				:	Black;
}

div.caution {
	border-style		: 	solid;
	border-color		: 	red;
	color				:	red;
}

div.warning {
	border-style		: 	solid;
	border-color		: 	red;
	color				:	red;
}

div.note {
	border-style		: 	solid;
	border-color		: 	blue;
	color				:	blue;
}

div.action {
	padding-left		:	100px;
	padding-right		:	100px;
	margin-left			:	100px;
	margin-right		:	100px;
	background-color	:	White;
	border-style		: 	solid;
}

h6.ref {
	text-align			:	right;
}

h4.result {
	padding-left		:	50px;
}

p.RN {
	color				: 	Blue;
}

table.table {
    border				: 	1px solid black;
}

th.row_h {
    border				: 	1px solid black;
    background-color	:	LightGray;
}

td.row_d {
    border				: 	1px solid black;
}

'''


mod_globals.os = os.name
 
if mod_globals.os == 'nt':
  import pip
  
  try:
    import serial
  except ImportError:
    pip.main(['install','pyserial'])

  try:
    import colorama
  except ImportError:
    pip.main(['install','colorama'])
    try:
      import colorama
    except ImportError:
      print "\n\n\n\t\t\tGive me access to the Internet for download modules\n\n\n"
      sys.exit()
  colorama.init()
else:
  # let's try android
  try:
    import androidhelper as android
    mod_globals.os = 'android'
  except:
    try:
      import android
      mod_globals.os = 'android'
    except:
      pass
  
if mod_globals.os != 'android':    
  try:
    import serial
    from serial.tools  import list_ports
    #import ply
  except ImportError:
    print "\n\n\n\tPleas install additional modules"
    print "\t\t>sudo easy_install pyserial"
    sys.exit()
    
from mod_elm       import ELM
from mod_scan_ecus import ScanEcus
from mod_utils     import *
from mod_mtc       import acf_getMTC

#global variables 

table_header = False
dfg_ds       = {}
 

def getRef( ff, pref ):
  notfound = True
  for l in ff:
    if l.startswith( pref ): 
      notfound = False
      break
  if notfound:
    return pref
  return l[:-4]

def getTitleAndRef( path, ff, root, title, l, rc = 0 ):
  
  if rc>3:
    print l
    return root, title
  
  title_el = root.find('title')  
  ref = title_el.find('xref')
  pref = ref.attrib['sie-id']
  
  notfound = True
  for l in ff:
    if l.startswith( pref ): 
      tree = et.parse(path+l)
      root = tree.getroot()
      notfound = False
      break
  if notfound: #then will try without mtc filter
    lf = os.listdir(path)
    for l in lf:
      if l.startswith( pref ): 
        tree = et.parse(path+l)
        root = tree.getroot()
        break
    return root, title
  title_el = root.find('title')
  title = title_el.text.strip()

  if title=='':
    root, title = getTitleAndRef( path, ff, root, title, l, rc+1 )
  return root, title
  
def convertXML(root, h_t, fns, ff, lid):

  global table_header
  
  for e in root.iter():
    if root.tag!='servinfo' and root.tag == e.tag:
      continue
        
    if 'v' in e.attrib.keys():
      continue
      
    e.set('v',1)

    #debug
    #print e.tag
    #xfile = ''
    
    if e.tag == 'servinfo':
      et.SubElement(h_t, 'h6', attrib={'class':'ref'}).text = e.attrib['id']
      et.SubElement(h_t, 'h6', attrib={'class':'ref'}).text = e.attrib['sieconfigid']
      #debug
      #xfile = e.attrib['id']
      
    elif e.tag == 'title':
      if fns[4]!='000000':
        title = 'DTC'+fns[4]+' '+e.text
        fns[4] = '000000'
      else:
        title = e.text
      et.SubElement(h_t, 'h2', attrib={'class':'title'}).text = title
      
    elif e.tag == 'result':
      et.SubElement(h_t, 'h4', attrib={'class':'result'}).text = e.text
      
    elif e.tag == 'question':
      et.SubElement(h_t, 'h4', attrib={'class':'question'}).text = e.text
      
    elif e.tag == 'xref':
      et.SubElement(h_t, 'br' )
      et.SubElement(h_t, 'a', attrib={'class':'xref','href':'#'+getRef( ff, e.attrib['sie-id'] )}).text = e.attrib['ref']
 
    elif e.tag == 'intxref':
      et.SubElement(h_t, 'a', attrib={'class':'intxref','href':'#'+lid + e.attrib['refid']}).text = '>>>>>>>'
     
    elif e.tag == 'RN-END-PROCEDURE':
      et.SubElement(h_t, 'a', attrib={'href':'#home'}).text = "Up"
      
    elif e.tag == 'RN-CLIP-DISPLAY-DEFAULTS':
      et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'RN-CLIP-DISPLAY-DEFAULTS '+e.attrib['DOMAIN-DESC']
      
    elif e.tag == 'RN-CLIP-ERASE-ALL-DEFAULTS':
      et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'RN-CLIP-ERASE-ALL-DEFAULTS '+e.attrib['DOMAIN-DESC']
      
    elif e.tag == 'RN-CLIP-DISPLAY':
      et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'RN-CLIP-DISPLAY Domain:('+e.attrib['DOMAIN-DESC']+') '+e.attrib['STATE-OR-PARAMETER-CODE']+'-'+e.attrib['STATE-OR-PARAMETER-NAME']
      
    elif e.tag == 'RN-RDC-ACCESS':
      if 'RDC-ELEMENT-REF' in e.attrib.keys() and 'RDC-ELEMENT-DESC' in e.attrib.keys():
        et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'RN-RDC-ACCESS RDC-ELEMENT-REF:'+e.attrib['RDC-ELEMENT-REF']+' RDC-ELEMENT-DESC:'+e.attrib['RDC-ELEMENT-DESC']
      else:
        et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'RN-RDC-ACCESS '
      
    elif e.tag == 'RN-CLIP-LAUNCH-ACTUATOR':
      et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'RN-CLIP-LAUNCH-ACTUATOR Domain:('+e.attrib['DOMAIN-DESC']+') '+e.attrib['ACTUATOR-CODE']+'-'+e.attrib['ACTUATOR-DESC']
      
    elif e.tag == 'RN-NTSE-ACCESS':
      et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'RN-NTSE-ACCESS'
      et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'WIRING-DIAGRAM-TYPE:'+e.attrib['WIRING-DIAGRAM-TYPE']
      et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'PRIMARY-WIRING-DIAGRAM-REF:'+e.attrib['PRIMARY-WIRING-DIAGRAM-REF']
      et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'PRIMARY-WIRING-DIAGRAM-DESC:'+e.attrib['PRIMARY-WIRING-DIAGRAM-DESC']
      if 'SIGNAL-CODE-REF' in e.attrib.keys() and 'SIGNAL-CODE-DESC' in e.attrib.keys():
        et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'SIGNAL-CODE-REF:'+e.attrib['SIGNAL-CODE-REF']
        et.SubElement(h_t, 'p', attrib={'class':'RN'}).text = 'SIGNAL-CODE-DESC:'+e.attrib['SIGNAL-CODE-DESC']
   
    elif e.tag == 'list1':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list1'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list1-A':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list1-A'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list1-B':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list1-B'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list1-D':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list1-D'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list2':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list2'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list2-A':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list1-A'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list2-B':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list2-B'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list2-D':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list2-D'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list3':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list3'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list3-A':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list3-A'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list3-B':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list3-B'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'list3-D':
      ni = et.SubElement(h_t, 'ul', attrib={'class':'list3-D'})
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'item':
      ni = et.SubElement(h_t, 'li', attrib={'class':'item'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'item-A':
      ni = et.SubElement(h_t, 'li', attrib={'class':'item-A'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'item-B':
      ni = et.SubElement(h_t, 'li', attrib={'class':'item-B'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'item-D':
      ni = et.SubElement(h_t, 'li', attrib={'class':'item-D'})
      convertXML( e, ni, fns, ff, lid )
      
    elif e.tag == 'ptxt':
      ni = et.SubElement(h_t, 'p', attrib={'class':'ptxt'})
      ni.text = e.text
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'zdiagnostic':
      ni = et.SubElement(h_t, 'div', attrib={'class':'zdiagnostic','id':lid+e.attrib['id']})
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'testgrp':
      ni = et.SubElement(h_t, 'div', attrib={'class':'testgrp','id':lid+e.attrib['id']})
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'topic':
      ni = et.SubElement(h_t, 'div', attrib={'class':'topic','id':lid+e.attrib['id']})
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'servinfosub':
      ni = et.SubElement(h_t, 'div', attrib={'class':'servinfosub','id':lid+e.attrib['id']})
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'caution':
      ni = et.SubElement(h_t, 'div', attrib={'class':'caution'})
      et.SubElement(ni, 'p', attrib={'class':'ptxt'}).text = 'Caution!!!'
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'warning':
      ni = et.SubElement(h_t, 'div', attrib={'class':'warning'})
      et.SubElement(ni, 'p', attrib={'class':'ptxt'}).text = 'Warning!!!'
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'note':
      ni = et.SubElement(h_t, 'div', attrib={'class':'note'})
      et.SubElement(ni, 'p', attrib={'class':'ptxt'}).text = 'Note!!!'
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'test1':
      ni = et.SubElement(h_t, 'div', attrib={'class':'test1'})
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'action':
      ni = et.SubElement(h_t, 'div', attrib={'class':'action'})
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'table':
      ni = et.SubElement(h_t, 'table', attrib={'class':'table'})
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'thead':
      table_header = True
      convertXML( e, h_t, fns, ff, lid )
      table_header = False

    elif e.tag == 'row':
      ni = et.SubElement(h_t, 'tr', attrib={'class':'row'})
      convertXML( e, ni, fns, ff, lid )

    elif e.tag == 'entry':
      if table_header: 
        ni = et.SubElement(h_t, 'th', attrib={'class':'row_h'})
      else:
        ni = et.SubElement(h_t, 'td', attrib={'class':'row_d'})      
      convertXML( e, ni, fns, ff, lid )
  
def processXML( path, l, ff ):

  tree = et.parse(path+l)
  root = tree.getroot()
  sieconfigid = root.attrib['sieconfigid']

  #ma = acf_MTC_compare_doc( sieconfigid, mtc )
  #if ma:  #document complines to MTC filter

  try:
    title = root.find('title').text.strip()
  except:
    title = ''

  try:
    if title=='': #check id documents refers to another
      root,title = getTitleAndRef( path, ff, root, title, l )
  except:
    pass
  
  lid = l[:-4]
  
  #process document
  fns = lid.split('_')
  fdo = fns[0][0]

  if fns[4]!='000000':
    title = 'DTC'+fns[4]+' '+title

  dtcId = ''
  if fns[4]!='000000' and fns[5]=='104':
    dtcId = fns[4]

  #add line to bookmark
  #cop = et.SubElement(h_o, 'p')
  #coa = et.SubElement(cop, 'a', href='#'+l[:-4]).text = title

  nel = et.Element('div')
  et.SubElement(nel, 'hr', attrib={'id':lid})

  if dtcId!='':
    et.SubElement(nel, 'a', attrib={'href':'#home','id':dtcId}).text = "Up"
  else:
    et.SubElement(nel, 'a', attrib={'href':'#home'}).text = "Up"

  convertXML( root, nel, fns, ff, lid )

  return nel, lid, title
  
def f_symptom( dfg_fet, ff, of, pref, fetname, path ):

  global dfg_ds

  fet_o = et.Element('div',attrib={'id':pref})
  et.SubElement(fet_o, 'hr')
  et.SubElement(fet_o, 'h1').text  = fetname
  
  fet_t = et.Element('div') #text
  
  for s in dfg_fet['symptomId']:
    for l in ff:
      if l.startswith(s):
        nel, lid, title = processXML( path, l, ff )
        if l in of:
          of.remove( l )   
          fet_t.append(nel)
        cop = et.SubElement(fet_o, 'p')
        et.SubElement(cop, 'a', href='#'+lid).text = title
    
  et.SubElement(fet_o, 'hr')
  fet_o.append( fet_t )   
  et.SubElement(fet_o, 'hr')
  return fet_o

def f_features( dfg_fun, ff, of, pref, funname, path ):

  fun_o = et.Element('div',attrib={'id':pref})
  et.SubElement(fun_o, 'hr')
  et.SubElement(fun_o, 'h1').text  = funname
  
  fun_t = et.Element('div') #text

  for ek in dfg_fun['feature'].keys():
    if dfg_fun['feature'][ek]['codetext'] in mod_globals.language_dict.keys():
      fetname = mod_globals.language_dict[dfg_fun['feature'][ek]['codetext']]
    else:
      fetname = dfg_fun['feature'][ek]['codetext']
    pref = dfg_fun['feature'][ek]['id_ppc']

    fet_text = f_symptom( dfg_fun['feature'][ek], ff, of, pref, fetname, path )
    
    cop = et.SubElement(fun_o, 'p')
    et.SubElement(cop, 'a', href='#'+pref).text = fetname 
    fun_t.append(fet_text)

  et.SubElement(fun_o, 'hr')
  fun_o.append( fun_t )   
  et.SubElement(fun_o, 'hr')
  return fun_o

def f_functions( dfg_dom, ff, of, pref, domname, path ):

  dom_o = et.Element('div',attrib={'id':pref})
  et.SubElement(dom_o, 'hr')
  et.SubElement(dom_o, 'h1').text  = domname
  
  dom_t = et.Element('div') #text
  
  #collect DTC
  dom_dtc_o = et.Element('div',attrib={'id':pref+'_dtc'}) 
  for l in ff:
    if l.startswith(pref):
      fns = l.split('_')
      if fns[4]!='000000':
        nel, lid, title = processXML( path, l, ff )
        of.remove( l )   
        cop = et.SubElement(dom_dtc_o, 'p')
        et.SubElement(cop, 'a', href='#'+lid).text = title
        dom_t.append(nel)
  
  cop = et.SubElement(dom_o, 'p')
  et.SubElement(cop, 'a', href='#'+pref+'_dtc').text = 'DTC'      
  
  #collect Parameters
  dom_par_o = et.Element('div',attrib={'id':pref+'_par'}) 
  for l in ff:
    if l.startswith(pref):
      fns = l.split('_')
      if fns[5]=='102':
        nel, lid, title = processXML( path, l, ff )
        of.remove( l )   
        cop = et.SubElement(dom_par_o, 'p')
        et.SubElement(cop, 'a', href='#'+lid).text = title
        dom_t.append(nel)
  
  cop = et.SubElement(dom_o, 'p')
  et.SubElement(cop, 'a', href='#'+pref+'_par').text = 'Parameters' 
  
  for fk in dfg_dom['function'].keys():
    if dfg_dom['function'][fk]['codetext'] in mod_globals.language_dict.keys():
      funname = mod_globals.language_dict[dfg_dom['function'][fk]['codetext']]
    else:
      funname = dfg_dom['function'][fk]['codetext']
    pref = dfg_dom['function'][fk]['id_ppc']
  
    fun_text = f_features( dfg_dom['function'][fk], ff, of, pref, funname, path )
    
    cop = et.SubElement(dom_o, 'p')
    et.SubElement(cop, 'a', href='#'+pref).text = funname 
    dom_t.append(fun_text)
    
  et.SubElement(dom_o, 'hr')
  dom_o.append( dom_dtc_o )   
  et.SubElement(dom_o, 'hr')
  dom_o.append( dom_par_o )   
  et.SubElement(dom_o, 'hr')
  dom_o.append( dom_t )   
  et.SubElement(dom_o, 'hr')
  return dom_o

def generateHTML(path, mtc, vin, dfg, date_madc ):

  global style
  
  lf = os.listdir(path)
  doc = et.Element('html')
  h_h = et.SubElement(doc,'head')
  h_b = et.SubElement(doc,'body')
  h_o = et.SubElement(h_b,'div',attrib={'id':'home'})   #bookmarks
  h_t = et.SubElement(h_b,'div')   #text

  et.SubElement(h_h, 'meta', charset="utf-8")
  et.SubElement(h_h, 'style' ).text = style
  
  et.SubElement(h_o, 'hr')
  et.SubElement(h_o, 'h4', attrib={'align':'right'}).text  = 'pyren'
  et.SubElement(h_o, 'h1', attrib={'align':'center'}).text  = dfg.defaultText
  et.SubElement(h_o, 'h1', attrib={'align':'center'}).text  = 'VIN : '+vin
  et.SubElement(h_o, 'h1', attrib={'align':'center'}).text  = date_madc
  et.SubElement(h_o, 'h4' ).text = 'MTC : '+' '.join( mtc )
  et.SubElement(h_o, 'hr')
      
  i = 0;
  print "\nPass 1:"
  ff = []
  for l in sorted(lf):
    print '\r\tDone:'+str(1+int(i*100./len(lf)))+'%',
    sys.stdout.flush()
    i = i + 1
    
    try:
      tree = et.parse(path+l)
      root = tree.getroot()
      sieconfigid = root.attrib['sieconfigid']
      ma = acf_MTC_compare_doc( sieconfigid, mtc )
      if ma:  #document complines to MTC filter
        ff.append( l )
    except:
      print "Error in file:", path+l
  
  ilen = len(ff);
  of = copy.deepcopy(ff)
  
  print "\nPass 2:"

  for dk in dfg.domain.keys():
    print '\r\tDone:'+str(int((ilen-len(of))*100./ilen))+'%'+' '*10,
    sys.stdout.flush()

    if dfg.domain[dk]['codetext'] in mod_globals.language_dict.keys():
      domname = mod_globals.language_dict[dfg.domain[dk]['codetext']]
    else:
      domname = dfg.domain[dk]['defaultText']
    pref = dfg.domain[dk]['id_ppc']
    
    dom_text = f_functions( dfg.domain[dk], ff, of, pref, domname, path )
    
    h_t.append(dom_text)
    cop = et.SubElement(h_o, 'p')
    et.SubElement(cop, 'a', href='#'+pref).text = domname 
    
  #collect others
  oth_o = et.Element('div',attrib={'id':pref+'_oth'}) 
  tf = copy.deepcopy(of)
  for l in tf:
    try:
      nel, lid, title = processXML( path, l, ff )
    except:
      print l
    of.remove( l )   
    cop = et.SubElement(oth_o, 'p')
    et.SubElement(cop, 'a', href='#'+lid).text = title
    h_t.append(nel)
  
  cop = et.SubElement(h_o, 'p')
  et.SubElement(cop, 'a', href='#'+pref+'_oth').text = 'Other' 

  et.SubElement(h_o, 'hr')

  h_o.append(oth_o)

  tree = et.ElementTree(doc)
  tree.write('./doc/'+vin+'.htm', encoding='UTF-8', xml_declaration=True, default_namespace=None, method='html')
  print '\r\tDone:100%'

vin_opt = ''
  
def optParser():
  '''Parsing of command line parameters. User should define at least com port name'''
  
  import argparse
  
  global vin_opt

  parser = argparse.ArgumentParser(
    #usage = "%prog -p <port> [options]",
    version="Document Viewer Version 1.0",
    description = "Tool for view DocDb"
  )
  
  parser.add_argument('-p',
      help="ELM327 com port name",
      dest="port",
      default="")

  parser.add_argument("-s",
      help="com port speed configured on ELM {38400[default],57600,115200,230400,500000} DEPRECATED",
      dest="speed",
      default="38400")

  parser.add_argument("-r",
      help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
      dest="rate",
      default="38400",)

  parser.add_argument("--si",
      help="try SlowInit first",
      dest="si",
      default=False,
      action="store_true")

  parser.add_argument("-L",
      help="language option {RU[default],GB,FR,IT,...}",
      dest="lang",
      default="RU")

  parser.add_argument("--cfc",
      help="turn off automatic FC and do it by script",
      dest="cfc",
      default=False,
      action="store_true")

  parser.add_argument("--log",
      help="log file name",
      dest="logfile",
      default="")

  parser.add_argument("--vin",
      help="vin number",
      dest="vinnum",
      default="")

  parser.add_argument("--scan",
      help="scan ECUs even if savedEcus.p file exists",
      dest="scan",
      default=False,
      action="store_true")

  parser.add_argument("--demo",
      help="for debuging purpose. Work without car and ELM",
      dest="demo",
      default=False,
      action="store_true")

  options = parser.parse_args()
  
  #if not options.port and mod_globals.os != 'android':
  #  parser.print_help()
  #  iterator = sorted(list(list_ports.comports()))
  #  print ""
  #  print "Available COM ports:"
  #  for port, desc, hwid in iterator:
  #    print "%-30s \n\tdesc: %s \n\thwid: %s" % (port,desc.decode("windows-1251"),hwid)
  #  print ""
  #  exit(2)
  #else:
  mod_globals.opt_port      = options.port
  mod_globals.opt_speed     = int(options.speed)
  mod_globals.opt_rate      = int(options.rate)
  mod_globals.opt_lang      = options.lang
  mod_globals.opt_log       = options.logfile
  mod_globals.opt_demo      = options.demo
  mod_globals.opt_scan      = options.scan
  mod_globals.opt_si        = options.si
  mod_globals.opt_cfc0      = options.cfc
  vin_opt                   = options.vinnum
    
def main():
  '''Main function
  
1) if ../BVMEXTRACTION doesn't exist then  mod_globals.opt_demo=True which means that we would not guide with MTC 
   and will show all options
2) if not demo mode and savedVIN.txt exists and not scan then check savedVIN.txt 
   else getVIN 
3) if len(vin)==0 then demo mode  
  '''

  global dfg_ds
  global vin_opt
  
  optParser()
  
  '''Check direcories'''
  if not os.path.exists('./cache'):
    os.makedirs('./cache')  
  if not os.path.exists('../MTCSAVE'):
    os.makedirs('../MTCSAVE')  

  '''If MTC database does not exists then demo mode'''
  if  not os.path.exists('../BVMEXTRACTION'):
    mod_globals.opt_demo = True

  print "Loading language "
  sys.stdout.flush()
  
  #loading language data
  lang = optfile("../Location/DiagOnCan_"+mod_globals.opt_lang+".bqm",True)
  mod_globals.language_dict = lang.dict
  print "Done"
  
  #finding zip
  #zipf = "../DocDB_"+mod_globals.opt_lang+".7ze"
  #if not os.path.exists(zipf):
  #  zipf = "../DocDB_GB.7ze"
  #  if not os.path.exists(zipf):
  #    zipFileList = glob.glob("../DocDB_*.7ze")
  #    if len(zipFileList)==0:
  #      print "\n\nERROR!!!!  Can't find any ../DocDB_*.7ze file"
  #      exit()
  #    zipf = zipFileList[0]

  VIN = ''
  if vin_opt=='' and (not mod_globals.opt_demo and (mod_globals.opt_scan or not os.path.exists('savedVIN.txt'))):
    print 'Opening ELM'
    elm = ELM( mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log )

    #change serial port baud rate 
    if mod_globals.opt_speed<mod_globals.opt_rate and not mod_globals.opt_demo:
      elm.port.soft_boudrate( mod_globals.opt_rate )
     
    print 'Loading ECUs list'
    se  = ScanEcus(elm)                    #Prepare list of all ecus
 
    SEFname = "savedEcus.p" 

    if mod_globals.opt_demo and len(mod_globals.opt_ecuid)>0:
      # demo mode with predefined ecu list
      se.read_Uces_file( all = True )    
      se.detectedEcus = []
      for i in mod_globals.opt_ecuid.split(','):
        if  i in se.allecus.keys():
          se.allecus[i]['ecuname']=i
          se.allecus[i]['idf']=se.allecus[i]['ModelId'][2:4]
          if se.allecus[i]['idf'][0]=='0': 
            se.allecus[i]['idf'] = se.allecus[i]['idf'][1]
          se.allecus[i]['pin'] = 'can' 
          se.detectedEcus.append( se.allecus[i] )    
    else:
      if not os.path.isfile(SEFname) or mod_globals.opt_scan: 
        # choosing model 
        se.chooseModel( mod_globals.opt_car )  #choose model of car for doing full scan
      
      # Do this check every time
      se.scanAllEcus()                       #First scan of all ecus
   
    de = se.detectedEcus
  
    print 'Reading VINs'
    VIN = getVIN( de, elm )
    
  elif vin_opt=='' and os.path.exists('savedVIN.txt'):

    with open('savedVIN.txt') as vinfile:
      vinlines = vinfile.readlines()
      for l in vinlines:
        l = l.strip()
        if '#' in l: continue
        if len(l)==17:
          VIN = l.upper()
          break
  
  elif vin_opt!='':
    VIN = vin_opt
            
  if len(VIN)!=17:
    print "Can't find any valid VIN. Switch to demo"
    mod_globals.opt_demo = True
  else:
    print "\tVIN     :",VIN
    
  #find and load MTC
  vindata = ''
  mtcdata = ''
  refdata = ''
  platform = ''
  if VIN!='':
    #print 'Finding MTC'
    vindata, mtcdata, refdata, platform = acf_getMTC( VIN, preferFile=True )
    
    if vindata=='' or mtcdata=='' or refdata=='':
      print "ERROR!!! Can't find MTC data in database"
      mod_globals.opt_demo = True
    
    print "\tPlatform:",platform
    #print "\tvindata:",vindata
    #print "\tmtcdata:",mtcdata
    #print "\trefdata:",refdata
    
    mtc = mtcdata.replace(' ','').replace('\n','').replace('\r','').replace('\t','').split(';')
    vda = vindata.split(';')[3].split(':')[1].split('/')
    mtc = mtc+vda
    mtcdata = ';'.join(mtc)
    date_madc = vindata.split(';')[4]
  
  #choose and load DFG
  dfg = class_dfg( platform )

  if dfg.tcom == '146':
    dfg.tcom = '159'
    dfg.dfgFile = dfg.dfgFile.replace('DFG_146', 'DFG_159')
  elif dfg.tcom == '135':
    dfg.tcom = '147'
    dfg.dfgFile = dfg.dfgFile.replace('DFG_135', 'DFG_147')

  dfg.loadDFG()

  #if os.path.isfile(dfg.cacheFile):                   #if cache exists
  #  dfg = pickle.load( open( dfg.cacheFile, "rb" ) )    #load it
  #else:                                               #else
  #  dfg.loadDFG()                                       #load file
  #  pickle.dump( dfg, open( dfg.cacheFile, "wb" ) )     #and save cache
    
  dfg_ds = dfg.dataSet  
    
  #dfg.showMenu(zipf) 
  #try:
  #if dfg.tcom == '135' : dfg.tcom = '147'
  generateHTML( "../DocDB_"+mod_globals.opt_lang+"/DocDb"+dfg.tcom+"/SIE/", mtcdata.split(';'), VIN, dfg, date_madc)
  #except:
  #  pass
    
if __name__ == '__main__':  
  main()
  
