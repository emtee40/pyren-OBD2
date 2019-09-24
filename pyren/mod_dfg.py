#!/usr/bin/env python

from xml.dom.minidom import parse
import xml.dom.minidom
import pickle


from mod_utils   import Choice
from mod_utils   import ChoiceLong
from mod_utils   import ChoiceFromDict
from mod_utils   import pyren_encode
from mod_utils   import clearScreen
import mod_globals
import sys
import glob
import os
import string

class class_dfg:

  tcom        = ''
  dfgFile     = ''
  cacheFile   = ''
  codetext    = ''
  defaultText = ''
  domain  = {} 
  dataSet = {}
  symptom = {}
   
  #domain
  #key=id value={'id_ppc':text,
  #              'codetext':text,
  #              'defaultText':text,
  #              'function':{}}
  #
  #domain[id]['function'] = {}  
  #key=id value={'id_ppc':text,
  #              'codetext':text,
  #              'defaultText':text,
  #              'feature':{}}    
  #
  #domain[id]['function'][id]['feature'] = {}
  #key=id value={'id_ppc':text,
  #              'codetext':text,
  #              'defaultText':text,
  #              'comp_id':text,
  #              'formula':text
  #              'dataSetId':[]
  #              'symptomId':[]}
  
  def __init__(self, platform):

    #find TCOM by platform
    if platform!='':    
      for file in glob.glob("../Vehicles/TCOM_*.[Xx]ml"):
        try: 
          model_n = int(file[17:20])
          if model_n<86: continue
        except ValueError:
          pass
        DOMTree = xml.dom.minidom.parse(file)
        vh = DOMTree.documentElement
        if vh.hasAttribute("defaultText"):
          TCOM = vh.getAttribute("TCOM")
          vehTypeCode = vh.getAttribute("vehTypeCode")
          if vehTypeCode.upper()==platform.upper():
            self.tcom = TCOM
            break
      self.dfgFile = '../Vehicles/DFG/DFG_'+self.tcom+'.Xml'
    else:
      vhcls = []
      for file in glob.glob("../Vehicles/DFG/DFG_*.[Xx]ml"):
        DOMTree = xml.dom.minidom.parse(file)
        vh = DOMTree.documentElement
        if vh.hasAttribute("defaultText"):
          TCOM = vh.getAttribute("TCOM")
          vehiclename = vh.getAttribute("defaultText")
          vhcls.append([vehiclename,file,TCOM])

      models = []
      for row in vhcls:
        models.append( row[2]+" "+row[0] )
          
      ch = ChoiceLong(models, "Choose model :")
      
      model = ch[0]
      self.dfgFile = vhcls[int(ch[1])-1][1]
      self.tcom =  self.dfgFile[20:23]
       
    self.cacheFile = './cache/dfg_'+self.tcom+'.p'
    
    return

  def loadDFG( self ):
    try:
      DOMTree = xml.dom.minidom.parse(self.dfgFile)
    except:
      print "ERROR loading dfg-file"
      #if 'DFG_135' in self.dfgFile:
      #  self.dfgFile = self.dfgFile.replace('DFG_135', 'DFG_147')

    fs = DOMTree.documentElement #functionsStructure
    
    if fs.hasAttribute("TCOM"):
      tmp_tcom         = fs.getAttribute("TCOM")
      self.codetext    = fs.getAttribute("codetext")
      self.defaultText = fs.getAttribute("defaultText")
    else:
      return

    self.domain  = {} 
    self.dataSet = {}
    self.symptom = {}
    
    domain = fs.getElementsByTagName("domain")
    if domain:
      for do in domain:
        do_id         = do.getAttribute("id")
        do_ = {}
        do_['id_ppc']     = do.getAttribute("id_ppc")
        do_['codetext']   = do.getAttribute("codetext")
        do_['defaultText']= do.getAttribute("defaultText")
        do_['function']   = {}
        
        function = do.getElementsByTagName("function")
        if function:
          for fu in function:
            fu_id         = fu.getAttribute("id")
            fu_ = {}
            fu_['id_ppc']     = fu.getAttribute("id_ppc")
            fu_['codetext']   = fu.getAttribute("codetext")
            fu_['defaultText']= fu.getAttribute("defaultText")
            fu_['feature']    = {}
        
            feature = fu.getElementsByTagName("feature")
            if feature:
              for fe in feature:
                fe_id         = fe.getAttribute("id")
                fe_ = {}
                fe_['id_ppc']     = fe.getAttribute("id_ppc")
                fe_['codetext']   = fe.getAttribute("codetext")
                fe_['defaultText']= fe.getAttribute("defaultText")
                fe_['comp_id']    = ''
                fe_['formula']    = ''
                fe_['dataSetId']  = []
                fe_['symptomId']  = []
                computation = fe.getElementsByTagName("computation")
                if computation:
                  for co in computation:
                    fe_['comp_id'] = co.getAttribute("id") 
                    fe_['formula'] = co.getAttribute("formula")
                dataSetIds = fe.getElementsByTagName("dataSetId")
                if dataSetIds: 
                  for dataSetId in dataSetIds:
                    dataSet = dataSetId.firstChild.nodeValue
                    fe_['dataSetId'].append(dataSet)
                symptomIds = fe.getElementsByTagName("symptomId")
                if symptomIds: 
                  for symptomId in symptomIds:
                    symptom = symptomId.firstChild.nodeValue
                    fe_['symptomId'].append(symptom)
        
                fu_['feature'][fe_id] = fe_
            do_['function'][fu_id] = fu_
        self.domain[do_id] = do_
               
    dataSets = fs.getElementsByTagName("dataSets")
    if dataSets:
      for dataSet in dataSets:
        ds_id         = dataSet.getAttribute("id")
        self.dataSet[ds_id] = {}
        self.dataSet[ds_id]['id_ppc'] = dataSet.getAttribute("id_ppc")
        self.dataSet[ds_id]['name']   = dataSet.getAttribute("name")
        computation = dataSet.getElementsByTagName("computation")
        if computation:
          for co in computation:
            self.dataSet[ds_id]['comp_id'] = co.getAttribute("id") 
            self.dataSet[ds_id]['formula'] = co.getAttribute("formula")
        

    symptomList = fs.getElementsByTagName("symptomList")
    if symptomList:
      for symptom in symptomList:
        sy_id         = symptom.getAttribute("id")
        self.symptom[sy_id] = {}
        self.symptom[sy_id]['codetext']   = symptom.getAttribute("codetext")
        self.symptom[sy_id]['defaultText']= symptom.getAttribute("defaultText")
      
    return        
          
  def showMenu( self, zip ):
     
    while(True):
      clearScreen()
      path = '/'
      header =  self.tcom + ' : ' +  self.defaultText + '\n'
      header = header + "Path : "+path
      print header 
      menu = {}
      for dk in self.domain.keys():
        if self.domain[dk]['codetext'] in mod_globals.language_dict.keys():
          menu[dk] = pyren_encode( mod_globals.language_dict[self.domain[dk]['codetext']] )
        else:
          menu[dk] = pyren_encode( self.domain[dk]['defaultText'] )
          
      menu["<EXIT>"] = "Exit"
      choice = ChoiceFromDict(menu, "Choose :",False)
      if choice[0]=="<EXIT>": return
      dk = choice[0]

      path = path + mod_globals.language_dict[self.domain[dk]['codetext']]
      while(True):
        clearScreen()
        header =  self.tcom + ' : ' +  self.defaultText + '\n'
        header = header + self.domain[dk]['id_ppc'] + " : "+path 
        print header 
        menu = {}
        for fk in self.domain[dk]['function'].keys():
          if self.domain[dk]['function'][fk]['codetext'] in mod_globals.language_dict.keys():
            menu[fk] = pyren_encode( mod_globals.language_dict[self.domain[dk]['function'][fk]['codetext']] )
          else:
            menu[fk] = pyren_encode( self.domain[dk]['function'][fk]['codetext'] )
            
        menu["<UP>"] = "UP"
        choice = ChoiceFromDict(menu, "Choose :", False)
        if choice[0]=="<UP>": break
        fk = choice[0]
    
        path = path + '/' + mod_globals.language_dict[self.domain[dk]['function'][fk]['codetext']]
        while(True):
          clearScreen()
          header =  self.tcom + ' : ' +  self.defaultText + '\n'
          header = header + self.domain[dk]['function'][fk]['id_ppc'] + " : "+path 
          print header 
          menu = {}
          for ek in self.domain[dk]['function'][fk]['feature'].keys():
            if self.domain[dk]['function'][fk]['feature'][ek]['codetext'] in mod_globals.language_dict.keys():
              menu[ek] = pyren_encode( mod_globals.language_dict[self.domain[dk]['function'][fk]['feature'][ek]['codetext']] )
            else:
              menu[ek] = pyren_encode( self.domain[dk]['function'][fk]['feature'][ek]['codetext'] )
              
          menu["<UP>"] = "UP"
          choice = ChoiceFromDict(menu, "Choose :", False)
          if choice[0]=="<UP>": break
          ek = choice[0]
    
          clearScreen()
          print self.domain[dk]['function'][fk]['feature'][ek]['id_ppc']
          
          ch = raw_input()