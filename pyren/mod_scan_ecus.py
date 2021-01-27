#!/usr/bin/env python
'''
   version: 170417
'''

# allecus contains such dictionaries
#
#'dst': '7A'
#'src': 'F1'
#'OptimizerId': 'SG0110577.XML'
#'ModelId': 'FG0110577.XML'}
#'stdType': 'STD_A'
#'doc': 'DCM1.2_L4DB_58_ X61_A'
#'idf': '1'
#'pin': 'can'
#'pin1': '6'
#'pin2': '14'
#'startDiagReq': '10C0'
#'startDiagRsp': '50C0'
#'stopDiagReq': '1081'
#'stopDiagRsp': '5081'
#'ids': ['2180','6180','0','6','FF','58','2180','6180','0','16','FF','4D']


from xml.dom.minidom import parse
import xml.dom.minidom
import pickle


from mod_utils   import Choice
from mod_utils   import ChoiceLong
from mod_utils   import pyren_encode
from mod_utils   import DBG
#from mod_elm     import ELM
import mod_db_manager
import mod_elm   as m_elm
import mod_globals
import sys
import glob
import os
import string

opt_demo = False

families = {"1":"13712",  "2":"13002",  "3":"13010",  "4":"13713",  "5":"13016",  "6":"13715",  "7":"60761",  
	    "8":"13004",  "9":"13012", "10":"13718", "11":"13719", "12":"13003", "13":"19763", "14":"13722",  
	   "15":"17782", "16": "7301", "17":"58508", "18":"13005", "19":"55948", "20":"13727", "21":"13920",  
	   "22":"23586", "23": "7305", "24":"51605", "25":"15664", "26":"15666", "27":"18638", "28":"15665",  
	   "29":"19606", "30":"61183", "31":"58925", "32":"58926", "33":"24282", "34":"60773", "35":"60777",  
	   "36":"60778", "37":"61750", "38":"53126", "39":"61751", "40": "8711", "41":"24353", "42":"61293",
	   "43": "5773", "44":"63135", "45":"C3P_73545", "46":"61883", "47":"58943", "48":"61882",
	   "49":"62658", "50":"13009", "51":"30504", "52":"13019", "53":"31980", "54":"31981", "55":"13922", 
	   "56":"13921", "57":"62659", "58":"62660", "59":"62661", "60":"11331", "61":"11332", "62": "9446",
	   "63":"55050", "64":"62720", "65":"29705", "66":"29706", "67":"62721", "68":"62722", "69":"62723",
	   "70":"57741", "72": "8992", "73":"61294", "74":"62724", "76":"11297",
	   "77":"56580", "78":"61295", "79":"60146", "80":"51172", "81":"51173",
	   "86":"57713", "87":"60779", "88":"63847", "89":"63848", "90": "4672", "91":"51666", "92":"53725",
     "93":"55049", "94":"56538", "95":"56539", "96":"56540", "97":"56562", "98":"57970", "99":"58003"} 

class ScanEcus:
  '''List all possible ECUs of this car'''
  
  allecus = {}       #all ecus possible in this model
  idTxT   = {}       #table of transmit addresses
  idRxT   = {}       #table of receive addresses
  detectedEcus = []  #ecus detected in car during scan
  vhcls  = []
  ecus   = []
  models = []
  reqres = []        #results of previous requests
  selectedEcu = 0
  vehTypeCode = ''
  
  def __init__(self, elm_ref):
    self.elm = elm_ref
    
    ####### Get list car models from vehicles directory #######
    self.vhcls  = []

    file_list = mod_db_manager.get_file_list_from_clip('Vehicles/TCOM_*.[Xx]ml')
    for file in file_list:
      try: 
        model_n = file[-7:-4]
        if model_n in ["005","010","026","035","054","064","066","069","088","107","110","114"]:
          continue
        #model_n = int(file[-7:-4])
        #if model_n<86: continue
      except ValueError:
        pass
      DOMTree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(file))
      vh = DOMTree.documentElement
      if vh.hasAttribute("defaultText"):
        vehiclename = vh.getAttribute("defaultText").strip()
        vehTypeCode = vh.getAttribute("vehTypeCode").strip()
        vehTCOM     = int(vh.getAttribute("TCOM"))
        vehindexTopo = int(vh.getAttribute("indexTopo"))
        self.vhcls.append([vehiclename,file,vehTypeCode,vehTCOM,vehindexTopo])
          
  def scanAllEcus(self):
    '''scan all ecus. If savedEcus.p exists then load it and return'''

    SEFname = "savedEcus.p" 
    if mod_globals.opt_can2:
      SEFname = "savedEcus2.p" 
    
    # check if savedEcus exists
    if os.path.isfile(SEFname) and not mod_globals.opt_scan: 
      
      # load it
      self.detectedEcus = pickle.load( open( SEFname, "rb" ) )
      
      #debug
      #check vehTypeCode
      if (len(self.detectedEcus)>0 and 'vehTypeCode' not in self.detectedEcus[0].keys() ):
        self.vehTypeCode = raw_input('Enter vehTypeCode:')
        # renew savedEcus
        self.allecus = {}
        for i in self.detectedEcus:
          i['vehTypeCode'] = self.vehTypeCode
          self.allecus[i['ecuname']] = i
        self.detectedEcus = []
        for i in self.allecus.keys ():
          self.detectedEcus.append (self.allecus[i])
        # sort list of detected ECUs
        self.detectedEcus = sorted (self.detectedEcus, key=lambda k: int (k['idf']))
        # save renewed version
        if (len (self.detectedEcus)): pickle.dump (self.detectedEcus, open (SEFname, "wb"))
  
      # check if savedEcus has old version
      if (len(self.detectedEcus)>0 and 'idTx' not in self.detectedEcus[0].keys() ):
        # renew savedEcus
        self.allecus = {}
        for i in self.detectedEcus:
          self.allecus[i['ecuname']] = i
        self.read_Uces_file()
        self.detectedEcus = []
        for i in self.allecus.keys():
          self.detectedEcus.append( self.allecus[i] )
        #sort list of detected ECUs
        self.detectedEcus = sorted(self.detectedEcus, key=lambda k: int(k['idf']))
        # save renewed version
        if (len(self.detectedEcus)): pickle.dump( self.detectedEcus, open( SEFname, "wb" ) )
      return
    else:
      mod_globals.opt_scan = True
    
    mod_globals.state_scan = True
      
    self.reqres = []
    self.errres = []
    
    i = 0
    print '\r'+'\t\t\t\t'+'\rScanning:'+str(i)+'/'+str(len(self.allecus))+" Detected: "+str(len(self.detectedEcus)),
    sys.stdout.flush()
    
    #scan CAN ecus
    
    canH  = '6'
    canL  = '14'
    if mod_globals.opt_can2:
      canH  = '13'
      canL  = '12'
    
    self.elm.init_can()
    #print self.allecus
    for ecu, row in sorted(self.allecus.iteritems(),key = lambda (x,y) :y['idf']+y['protocol']+str(1/float(len(y['ids'])))):
      if (self.allecus[ecu]['pin']=='can' and
          self.allecus[ecu]['pin1']==canH  and
          self.allecus[ecu]['pin2']==canL):        
        i = i+1
        print '\r'+'\t\t\t\t'+'\rScanning:'+str(i)+'/'+str(len(self.allecus))+" Detected: "+str(len(self.detectedEcus)),
        sys.stdout.flush()
        
        self.elm.set_can_addr( self.allecus[ecu]['dst'], self.allecus[ecu] )
        self.scan_can( self.allecus[ecu] )

    self.elm.close_protocol()

    #scan KWP ecus
    if not mod_globals.opt_can2:
      self.elm.init_iso()   #actually it executed every time the address is changed
      for ecu, row in sorted(self.allecus.iteritems(),key = lambda (x,y) :y['idf']+y['protocol']):
        if (self.allecus[ecu]['pin']=='iso' and 
            self.allecus[ecu]['pin1']=='7'  and 
            self.allecus[ecu]['pin2']=='15'):
          
          i = i+1
          print '\r'+'\t\t\t\t'+'\rScanning:'+str(i)+'/'+str(len(self.allecus))+" Detected: "+str(len(self.detectedEcus)),
          sys.stdout.flush()
     
          self.elm.set_iso_addr( self.allecus[ecu]['dst'], self.allecus[ecu] )
          self.scan_iso( self.allecus[ecu] )

    print '\r'+'\t\t\t\t'+'\rScanning:'+str(i)+'/'+str(len(self.allecus))+" Detected: "+str(len(self.detectedEcus))
    
    mod_globals.state_scan = False
    
    #sort list of detected ECUs
    self.detectedEcus = sorted(self.detectedEcus, key=lambda k: int(k['idf']))
    if (len(self.detectedEcus)): pickle.dump( self.detectedEcus, open( SEFname, "wb" ) )
    #print self.detectedEcus
        
  def reScanErrors(self):
    '''scan only detectedEcus for re-check errors'''
    
    mod_globals.opt_scan = True
      
    self.reqres = []
    self.errres = []
    
    i = 0
    print '\r'+'\t\t\t\t'+'\rScanning:'+str(i)+'/'+str(len(self.detectedEcus)),
    sys.stdout.flush()
    
    #scan CAN ecus
    canH  = '6'
    canL  = '14'
    if mod_globals.opt_can2:
      canH  = '13'
      canL  = '12'
    
    self.elm.init_can()
    for row in sorted(self.detectedEcus, key=lambda k: int(k['idf'])):
      if (row['pin']=='can' and
          row['pin1']==canH  and
          row['pin2']==canL):        
        
        i = i+1
        print '\r'+'\t\t\t\t'+'\rScanning:'+str(i)+'/'+str(len(self.detectedEcus)),
        sys.stdout.flush()
        
        self.elm.set_can_addr( row['dst'], row )
        self.scan_can( row )

    self.elm.close_protocol()

    #scan KWP ecud
    if not mod_globals.opt_can2:
      self.elm.init_iso()
      for row in sorted(self.detectedEcus, key=lambda k: int(k['idf'])):
        if (row['pin']=='iso' and 
            row['pin1']=='7'  and 
            row['pin2']=='15'):
          
          i = i+1
          print '\r'+'\t\t\t\t'+'\rScanning:'+str(i)+'/'+str(len(self.detectedEcus)),
          sys.stdout.flush()
     
          self.elm.set_iso_addr( row['dst'], row )
          self.scan_iso( row )
    
    print '\r'+'\t\t\t\t'+'\rScanning:'+str(i)+'/'+str(len(self.detectedEcus))
    
    #sort list of detected ECUs
    self.detectedEcus = sorted(self.detectedEcus, key=lambda k: int(k['idf']))
        
  def chooseECU(self, ecuid ):
    
    if len(self.detectedEcus)==0:
      self.scanAllEcus()
    
    if len(self.detectedEcus)==0:
      print "NO ECU detected. Nothing to do. ((("
      exit( 2 )
    
    if len(ecuid)>4:
      i = 0
      for row in self.detectedEcus:
        if ecuid in row['ecuname']:
          self.selectedEcu = i
          return self.detectedEcus[self.selectedEcu]
        i = i + 1
    
    listecu = []
    
    if mod_globals.os == 'android':
      if mod_globals.opt_scan:
        print pyren_encode( "\n     %-40s %s" % ("Name","Warn") )
      else:
        print pyren_encode( "\n     %-40s %s" % ("Name","Type") )
      
      for row in self.detectedEcus:
        if families[row['idf']] in mod_globals.language_dict.keys():
          fmlyn = mod_globals.language_dict[families[row['idf']]]
          if mod_globals.opt_scan:
            line = "%-40s %s" % (fmlyn,row['rerr'])
          else:
            line = "%-40s %s" % (fmlyn,row['stdType'])
        else:
          if mod_globals.opt_scan:
            line = "%-40s %s" % (row['doc'].strip(),row['rerr'])
          else:
            line = "%-40s %s" % (row['doc'].strip(),row['stdType'])
        listecu.append( line )
    else:
      if mod_globals.opt_scan:
        print pyren_encode( "\n     %-7s %-6s %-5s %-40s %s" % ("Addr","Family","Index","Name","Warn") )
      else:
        print pyren_encode( "\n     %-7s %-6s %-5s %-40s %s" % ("Addr","Family","Index","Name","Type") )
    
      for row in self.detectedEcus:
        if 'idf' not in row.keys():
          row['idf'] = ''
        if row['dst'] not in m_elm.dnat.keys():
          m_elm.dnat[row['dst']] = '000'
          m_elm.snat[row['dst']] = '000'
        if row['idf'] in families.keys() and families[row['idf']] in mod_globals.language_dict.keys():
          fmlyn = mod_globals.language_dict[families[row['idf']]]
          if mod_globals.opt_scan:
            line = "%-2s(%3s) %-6s %-5s %-40s %s" % (row['dst'], m_elm.dnat[row['dst']], row['idf'],row['ecuname'],fmlyn,row['rerr'])
          else:
            line = "%-2s(%3s) %-6s %-5s %-40s %s" % (row['dst'], m_elm.dnat[row['dst']], row['idf'],row['ecuname'],fmlyn,row['stdType'])
        else:
          if mod_globals.opt_scan:
            line = "%-2s(%3s) %-6s %-5s %-40s %s" % (row['dst'], m_elm.dnat[row['dst']], row['idf'],row['ecuname'],row['doc'].strip(),row['rerr'])
          else:
            line = "%-2s(%3s) %-6s %-5s %-40s %s" % (row['dst'], m_elm.dnat[row['dst']], row['idf'],row['ecuname'],row['doc'].strip(),row['stdType'])
        listecu.append( line )

    listecu.append( "Rescan errors" )    
    listecu.append( "<Exit>" )    
    choice = Choice(listecu, "Choose ECU :")

    if choice[0]=="Rescan errors": 
      self.reScanErrors()
      return -1
      
    if choice[0].lower()=="<exit>": 
      exit(1)

    i = int(choice[1])-1
    self.selectedEcu = i
    return self.detectedEcus[self.selectedEcu]
  
  def getselectedEcu(self):
    return self.detectedEcus[self.selectedEcu]
    
  def load_model_ECUs( self, file ):

    # loading name list of all possible ECUs
    
    ecuname = ''

    DOMTree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(file))
    vh = DOMTree.documentElement

    if vh.hasAttribute ("vehTypeCode"):
      self.vehTypeCode = vh.getAttribute ("vehTypeCode")

    connector = vh.getElementsByTagName("Connector")
    cannetwork = connector.item(0).getElementsByTagName("CANNetwork")
    isonetwork = connector.item(0).getElementsByTagName("ISONetwork")
    
    for pin in cannetwork:
      canH = pin.getAttribute("canH")
      canL = pin.getAttribute("canL")

      canids = pin.getElementsByTagName("CanId")
      if canids:
        for canid in canids:
          targetAddress = canid.getAttribute("targetAddress").strip()
          idTx = canid.getAttribute("idTx").strip()
          if len(idTx)==4 : idTx = idTx[1:]
          idRx = canid.getAttribute("idRx").strip()
          if len(idRx)==4 : idRx = idRx[1:]
          self.idTxT[targetAddress] = idTx
          self.idRxT[targetAddress] = idRx
      
      brp = ''
      CANNetworkParams = pin.getElementsByTagName("CANNetworkParams")
      if CANNetworkParams:
        for CANNetworkParam in CANNetworkParams:
          brp += CANNetworkParam.getAttribute("brp").strip()
          
      eculist = pin.getElementsByTagName("EcuList")
      if eculist:
        ecukind = eculist.item(0).getElementsByTagName("EcuKind")
        for ek in ecukind:
          idf = ek.getAttribute("idFamily")
          ecuref = ek.getElementsByTagName("EcuRef")
          for er in ecuref:
            ecuname = er.getAttribute("name").strip()
            ecudoc  = er.getAttribute("doc").strip()
            self.allecus[ecuname] = {}
            self.allecus[ecuname]["pin"] ="can"
            self.allecus[ecuname]["pin1"]=canH
            self.allecus[ecuname]["pin2"]=canL
            self.allecus[ecuname]["idf"] =idf
            self.allecus[ecuname]["doc"] =ecudoc
            self.allecus[ecuname]["ecuname"] = ecuname
            self.allecus[ecuname]["brp"] = brp
            self.allecus[ecuname]["vehTypeCode"] = self.vehTypeCode
      
    for pin in isonetwork:
      pinK = pin.getAttribute("pinK")
      pinL = pin.getAttribute("pinL")
      eculist = pin.getElementsByTagName("EcuList")
      if eculist:
        ecukind = eculist.item(0).getElementsByTagName("EcuKind")
        for ek in ecukind:
          idf = ek.getAttribute("idFamily")
          ecuref = ek.getElementsByTagName("EcuRef")
          for er in ecuref:
            ecuname = er.getAttribute("name").strip()
            ecudoc  = er.getAttribute("doc").strip()
            self.allecus[ecuname] = {}
            self.allecus[ecuname]["pin"] ="iso"
            self.allecus[ecuname]["pin1"]=pinK
            self.allecus[ecuname]["pin2"]=pinL
            self.allecus[ecuname]["idf"] =idf
            self.allecus[ecuname]["doc"] =ecudoc
            self.allecus[ecuname]["ecuname"] = ecuname
            self.allecus[ecuname]["vehTypeCode"] = self.vehTypeCode

    self.read_Uces_file()
        
  def read_Uces_file( self, all = False ):

    # Finding them in Uces.xml and loading 
    DOMTree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip("EcuRenault/Uces.xml"))
    Ecus = DOMTree.documentElement
    EcuDatas = Ecus.getElementsByTagName("EcuData")
    if EcuDatas:
      for EcuData in EcuDatas:
        name = EcuData.getAttribute("name")
        if name in self.allecus.keys() or all:
        
          if all:
            self.allecus[name] = {}
            self.allecus[name]["doc"] = ''
          
          self.allecus[name]["stdType"] = EcuData.getAttribute("stdType")
          
          if EcuData.getElementsByTagName("ModelId").item(0).firstChild:
            self.allecus[name]["ModelId"] = EcuData.getElementsByTagName("ModelId").item(0).firstChild.nodeValue.strip()
          else:
            self.allecus[name]["ModelId"] = name
            
          if EcuData.getElementsByTagName("OptimizerId").item(0).firstChild:
            self.allecus[name]["OptimizerId"] = EcuData.getElementsByTagName("OptimizerId").item(0).firstChild.nodeValue.strip()
          else:
            self.allecus[name]["OptimizerId"] = ''
            
          if self.allecus[name]["doc"]=='':
             self.allecus[name]["doc"] = self.allecus[name]["ModelId"]
          
          ecui = EcuData.getElementsByTagName("ECUInformations")
          if ecui:
            isodst = ""
            candst = ""
            src = "F1"
            
            fastinit = ''
            fastinit_tag = ecui.item(0).getElementsByTagName("FastInitAddress")
            if fastinit_tag:
              fastinit = fastinit_tag.item(0).getAttribute("value")
            self.allecus[name]["fastInit"] = fastinit
            
            slowinit = ''
            slowinit_tag = ecui.item(0).getElementsByTagName("SlowInitAddress")
            if slowinit_tag:
              slowinit = slowinit_tag.item(0).getAttribute("value")
            self.allecus[name]["slowInit"] = slowinit
            
            errordelay = ''
            errordelay_tag = ecui.item(0).getElementsByTagName("ErrorDelay")
            if errordelay_tag:
              errordelay = errordelay_tag.item(0).getAttribute("value")
            self.allecus[name]["errorDelay"] = errordelay
 
            replaytorequestdelay = ''
            replaytorequestdelay_tag = ecui.item(0).getElementsByTagName("ReplyToRequestDelay")
            if replaytorequestdelay_tag:
              replaytorequestdelay = replaytorequestdelay_tag.item(0).getAttribute("value")
            self.allecus[name]["replyToRequestDelay"] = replaytorequestdelay
            
            commretry = ''
            commretry_tag = ecui.item(0).getElementsByTagName("CommRetry")
            if commretry_tag:
              commretry = commretry_tag.item(0).getAttribute("value")
            self.allecus[name]["commRetry"] = commretry
            
            programmable = ''
            programmable_tag = ecui.item(0).getElementsByTagName("Programmable")
            if programmable_tag:
              programmable = programmable_tag.item(0).getAttribute("value")
            self.allecus[name]["programmable"] = programmable
            
            baudrate = ''
            baudrate_tag = ecui.item(0).getElementsByTagName("BaudRate")
            if baudrate_tag:
              baudrate = baudrate_tag.item(0).getAttribute("value")
            self.allecus[name]["baudRate"] = baudrate
            
            kw1 = ''
            kw1_tag = ecui.item(0).getElementsByTagName("KW1")
            if kw1_tag:
              kw1 = kw1_tag.item(0).getAttribute("value")
            self.allecus[name]["KW1"] = kw1
            
            kw2 = ''
            kw2_tag = ecui.item(0).getElementsByTagName("KW2")
            if kw2_tag:
              kw2 = kw2_tag.item(0).getAttribute("value")
            self.allecus[name]["KW2"] = kw2
            
            timings = ''
            timings_tag = ecui.item(0).getElementsByTagName("Timings")
            if timings_tag:
              timings = timings_tag.item(0).getAttribute("value")
            self.allecus[name]["timings"] = timings
            
            protocol = ''
            protocol_tag = ecui.item(0).getElementsByTagName("Protocol")
            if protocol_tag:
              protocol = protocol_tag.item(0).getAttribute("value")
            self.allecus[name]["protocol"] = protocol
            
            canconfig = ''
            canconfig_tag = ecui.item(0).getElementsByTagName("CANConfig")
            if canconfig_tag:
              canconfig = canconfig_tag.item(0).getAttribute("value")
            self.allecus[name]["CANConfig"] = canconfig
           
            addr = ecui.item(0).getElementsByTagName("Address")
            if addr:
              candst = addr.item(0).getAttribute("targetAddress")
              src = addr.item(0).getAttribute("toolAddress")
             
            if candst in self.idTxT.keys():
              self.allecus[name]["idTx"] = self.idTxT[candst] 
            else:
              self.allecus[name]["idTx"] = ""
              
            if candst in self.idRxT.keys():
              self.allecus[name]["idRx"] = self.idRxT[candst] 
            else:
              self.allecus[name]["idRx"] = ""
               
            self.allecus[name]["src"] = src
            if len(candst)>0:
              self.allecus[name]["dst"] = candst
            else:
              if len(fastinit)>0: 
                self.allecus[name]["dst"] = fastinit
              else:
                self.allecus[name]["dst"] = ''
               
            frms = ecui.item(0).getElementsByTagName("Frames")
            if frms:
              StartDiagSession = frms.item(0).getElementsByTagName("StartDiagSession")
              if StartDiagSession:
                self.allecus[name]["startDiagReq"] = StartDiagSession.item(0).getAttribute("request")
                self.allecus[name]["startDiagRsp"] = StartDiagSession.item(0).getAttribute("response")
              else:
                self.allecus[name]["startDiagReq"] = ''
                self.allecus[name]["startDiagRsp"] = ''
              StopDiagSession = frms.item(0).getElementsByTagName("StopDiagSession")
              if StopDiagSession:
                self.allecus[name]["stopDiagReq"] = StopDiagSession.item(0).getAttribute("request")
                self.allecus[name]["stopDiagRsp"] = StopDiagSession.item(0).getAttribute("response")
              else:
                self.allecus[name]["stopDiagReq"] = ''
                self.allecus[name]["stopDiagRsp"] = ''
              KeepAlive = frms.item(0).getElementsByTagName("KeepAlive")
              if KeepAlive:
                self.allecus[name]["keepAliveReq"] = KeepAlive.item(0).getAttribute("request")
                self.allecus[name]["KeepAlivePeriod"] = KeepAlive.item(0).getAttribute("period")
              else:
                self.allecus[name]["keepAliveReq"] = ''
                self.allecus[name]["KeepAlivePeriod"] = ''
            else:
              self.allecus[name]["startDiagReq"] = ''
              self.allecus[name]["startDiagRsp"] = ''
              self.allecus[name]["stopDiagReq"] = ''
              self.allecus[name]["stopDiagRsp"] = ''
              self.allecus[name]["keepAliveReq"] = ''
              self.allecus[name]["KeepAlivePeriod"] = ''
                
            idtt = []
            ids  = ecui.item(0).getElementsByTagName("Ids")
            if ids:
              for id in ids:
                IdFrame = id.getElementsByTagName("IdFrame")
                if IdFrame:
                  idreq = IdFrame.item(0).getAttribute("request")
                  idrsp = IdFrame.item(0).getAttribute("response")
                  idlen = IdFrame.item(0).getAttribute("length")
                idbytes = id.getElementsByTagName("IdByte")
                if idbytes:
                  for idb in idbytes:
                    idrank = idb.getAttribute("rank")
                    idmask = idb.getAttribute("mask")
                    idval  = idb.getAttribute("value")
                    idtt.append(idreq)
                    idtt.append(idrsp)
                    idtt.append(idlen)
                    idtt.append(idrank)
                    idtt.append(idmask)
                    idtt.append(idval) 
            self.allecus[name]["ids"] = idtt
            
  def chooseModel(self, num):

    orderBy = 0    # 0 = vehiclename
                   # 1 = file
                   # 2 = vehTypeCode
                   # 3 = vehTCOM
                   # 4 = vehindexTopo

    for row in sorted( self.vhcls, key=lambda k : k[orderBy]):
      self.models.append( row[2]+" "+row[0] )
        
    if num==0 or num>len(self.models):
      ch = ChoiceLong(self.models, "Choose model :")
    else:
      ch = [self.models[num-1],num]

    choice = sorted( self.vhcls, key=lambda k : k[orderBy])[int(ch[1])-1]

    model = choice[0]
    tcomfilename = choice[1]
      
    print "Loading data for :", model, tcomfilename,
    sys.stdout.flush()
    
    self.allecus = {}

    if self.elm.lf!=0:
      self.elm.lf.write("#load: "+model+' '+tcomfilename+"\n")
      self.elm.lf.flush()    

    #self.load_model_ECUs( "../Vehicles/"+tcomfilename )
    self.load_model_ECUs( tcomfilename )
    print "  - "+str(len(self.allecus))+" ecus loaded"
    
  def compare_ecu( self, row, rrsp, req ):

    if len( req )/2==3: rrsp = rrsp[3:]
    
    base = 0
    res = 0
    att = 0
    
    ttrrsp = rrsp.replace(' ','')
    if not all(c in string.hexdigits for c in ttrrsp): return False 
    
    while base+6<=len(row) and (int(row[base+3])*3+2)<=len(rrsp):
      if row[base]!=req:
        req = row[base]
        rrsp = self.elm.cmd(req)[3:]

        ttrrsp = rrsp.replace(' ','')
        if not all(c in string.hexdigits for c in ttrrsp): return False
        
        if len( req )/2==3: rrsp = rrsp[3:]

      byte = int(rrsp[int(row[base+3])*3:int(row[base+3])*3+2],16)
      mask = int(row[base+4],16)
      val  = int(row[base+5],16)
      
      if (byte&mask)==val:
        res += 1
      att += 1
      if att!=res:
        break
      base += 6
      
    if res==att and res>0:
      return True
    else:
      return False
       
  def request_can( self, row ):
   
    global opt_demo
    
    self.elm.start_session(row['startDiagReq']) 	#open session    
    rrsp = self.elm.cmd(row['ids'][0])	#get identification data
    
    self.elm.cmd("at st fa")              #set timeout to 1 second
    self.elm.cmd("at at 0")               #disable adaptive timing

    rerr = ''
    if row['stdType']=='STD_A': 
      rerr = self.elm.cmd('17FF00')	    #get errors STD_A

    if row['stdType']=='STD_B': 
      rerr = self.elm.cmd('1902AF')	    #get errors STD_B
      
    if row['stdType']=='UDS': 
      rerr = self.elm.cmd('1902AF')	    #get errors UDS
    
    if len(row['stopDiagReq'])>0:
      self.elm.cmd(row['stopDiagReq'])	#close session

    self.elm.cmd("at at 1")               #enable adaptive timing
    
    return rrsp,rerr
  
  def request_iso( self, row ):
  
    global opt_demo
    
    if len(row['dst'])!=2: return 'addr error','addr error' 
    
    rsp = ''
    cKey = row['dst']+row['startDiagReq']+row['stdType']+row['protocol']
    for r in self.reqres:
      if cKey==r[0]:
        rsp = r[1]
        break
    
    #if len(rsp)==0:
    #  rsp = self.elm.cmd("81")	 		    #init bus
    #  self.reqres.append([cKey,rsp,''])
    
    rrsp = ""
    rerr = ""
    rerrPositive = ""
    if "ERROR" not in rsp and "ERROR" not in self.elm.lastinitrsp.upper():
      self.elm.start_session(row['startDiagReq']) 	#open session    

      rrsp = self.elm.cmd(row['ids'][0])	#get identification data

      self.elm.cmd("at st fa")              #set timeout to 1 second
      self.elm.cmd("at at 0")               #disable adaptive timing

      rerr = ''    
      if row['stdType']=='STD_A': 
        rerr = self.elm.cmd('17FF00')	    #get errors STD_A
        rerrPositive = "57"
        
      if row['stdType']=='STD_B': 
        rerr = self.elm.cmd('1902AF')	    #get errors STD_B
        rerrPositive = "59"
        
      if row['stdType']=='UDS': 
        rerr = self.elm.cmd('1902AF')	    #get errors UDS
        rerrPositive = "59"

      self.elm.cmd("at at 1")               #enable adaptive timing

        
      if len(row['stopDiagReq'])>0:
        self.elm.cmd(row['stopDiagReq'])	#close session

    res = ""
    for s in rrsp.split('\n'):
      dss = s.replace(' ','')
      if len(dss)==0:
        continue
      if dss.startswith(row['ids'][1]):
        res = s
      elif len(row['ids'][1])==(len(row['ids'][0])+2) and str(row['dst'] + dss).startswith(row['ids'][1]):
        #sometimes ids contains addr
        res = s

    rrsp = res

    res = ""
    for s in rerr.split('\n'):
      if s.replace(' ','').startswith(rerrPositive):
        res = s
    rerr = res
    
    return rrsp,rerr

  def scan_can( self, row ):
    
    rrsp = ''
    rerr = ''
    
    if self.elm.lf!=0:
      self.elm.lf.write("#check: "+row['ecuname']+" Addr:"+row['dst']+"\n")
      self.elm.lf.flush()    

 
    for r in self.reqres:
      if (row['dst']+row['startDiagReq']+row['stdType']+row['ids'][0]+row['protocol'])==r[0]:
        rrsp = r[1]
        rerr = r[2]

    #debug
    #print rrsp

    if rrsp=='':
      rrsp,rerr = self.request_can( row )

      if not rrsp: rrsp = ''
      if not rerr: rerr = ''
      
      if row['stdType']=='STD_A':
        rerr = (str (int (rerr[3:5], 16)) if len (rerr) > 5 and rerr[:2] == '57' else '0')
      if row['stdType']=='STD_B':
        rerr = (str ((len (rerr) - 8) / 12) if len (rerr) > 8 and rerr[:2] == '59' else '0')
      if row['stdType']=='UDS':
        rerr = (str ((len (rerr) - 8) / 12) if len (rerr) > 8 and rerr[:2] == '59' else '0')
      if row['stdType']=='FAILFLAG':
        rerr = 'N/A'

      row['rerr'] = rerr   

      if rrsp!='':
        self.reqres.append([row['dst']+row['startDiagReq']+row['stdType']+row['ids'][0]+row['protocol'],rrsp,rerr]) #populate cache for not to ask again
 
    compres = False
    if 'ERROR' not in rrsp:
      rrsp = rrsp[3:]
      compres = self.compare_ecu( row['ids'], rrsp, row['ids'][0] )

    if compres:
      familynotdeteced = True
      for i in self.detectedEcus:
        if i['idf']==row['idf']:
          familynotdeteced = False
      if familynotdeteced:
        # than we found new ecu 
        row['rerr'] = rerr   
        self.detectedEcus.append(row)
    
  def scan_iso( self, row ):

    rrsp = ''
    rerr = '0'

    if self.elm.lf!=0:
      self.elm.lf.write("#check: "+row['ecuname']+" Addr:"+row['dst']+" Protocol:"+row['protocol']+" ids:" + row['ids'][0] + "\n")
      self.elm.lf.flush()    

    for r in self.reqres:
      if (row['dst']+row['startDiagReq']+row['stdType']+row['ids'][0]+row['protocol'])==r[0]:
        rrsp = r[1]
        rerr = r[2]

    if rrsp=='':
      rrsp,rerr = self.request_iso( row )

      #debug
      DBG('rrsp', rrsp)

      if not rrsp: rrsp = ''
      if not rerr: rerr = ''
      
      if row['stdType']=='STD_A':
        rerr = (str(int(rerr[3:5],16)) if len(rerr)>5 and rerr[:2]=='57' else '0')  
      if row['stdType']=='STD_B':
        rerr = (str((len(rerr)-8)/12) if len(rerr)>8 and rerr[:2]=='59' else '0')
      if row['stdType']=='UDS':
        rerr = (str((len(rerr)-8)/12) if len(rerr)>8 and rerr[:2]=='59' else '0')
      if row['stdType']=='FAILFLAG':
        rerr = 'N/A'
        
      row['rerr'] = rerr   
      
      if rrsp!='':
        self.reqres.append([row['dst']+row['startDiagReq']+row['stdType']+row['ids'][0]+row['protocol'],rrsp,rerr]) #populate cache for not to ask again

    #debug
    DBG( 'reqres', str( self.reqres ) )

    compres = False
    if 'ERROR' not in rrsp:
      rrsp = rrsp[3:]
      compres = self.compare_ecu( row['ids'], rrsp, row['ids'][0] )

    #debug
    DBG( 'compres', str( str(compres) + ' ' + row['ecuname']) )

    if not rerr: rerr = ''

    if compres:
      familynotdeteced = True
      for i in self.detectedEcus:
        if i['idf']==row['idf']:
          familynotdeteced = False
      if familynotdeteced:    
        # than we found new ecu    
        row['rerr'] = rerr   
        self.detectedEcus.append(row)

def readECUIds( elm ):

  # clear cache
  elm.clear_cache()

  StartSession = ''
  DiagVersion = ''
  Supplier = ''
  Version = ''
  Soft = ''
  Std = ''
  VIN = ''
  rsp = ''

  # check session start command
  if elm.startSession == '':
    # check 10C0
    res = elm.request(req='10C0', positive='50', cache=False)

    if res=='' or 'ERROR' in res: # no response from ecu
      return StartSession, DiagVersion, Supplier, Version, Soft, Std, VIN

    if res.startswith('50'):
        StartSession = '10C0'
    else:
        res = elm.request(req='1003', positive='50', cache=False)
        if res.startswith('50'):
            StartSession = '1003'
        else:
          res = elm.request(req='10A0', positive='50', cache=False)
          if res.startswith('50'):
            StartSession = '10A0'
          else:
            res = elm.request(req='10B0', positive='50', cache=False)
            if res.startswith('50'):
              StartSession = '10B0'


  else:
      StartSession = elm.startSession
      res = elm.request(req=elm.startSession, positive='50', cache=False)

  if not res.startswith('50'):
      # debug
      # print 'ERROR: Could not open the session
      pass

  # check STD_A
  IdRsp = elm.request(req='2180', positive='61', cache=False)

  '''      0         1         2         3         4         5         6         7      '''
  '''      01234567890123456789012345678901234567890123456789012345678901234567890123456'''
  # Debug
  # IdRsp = '61 80 34 36 33 32 52 45 34 42 45 30 30 33 37 52 00 83 9D 00 1A 90 01 01 00 88 AA'
  '''                           -- --------                ----- -----                  '''
  '''              DiagVersion--+      |                     |     +--Version           '''
  '''                        Supplier--+                     +--Soft                    '''

  if len(IdRsp) > 59:

    DiagVersion = str(int(IdRsp[21:23], 16))
    Supplier = IdRsp[24:32].replace(' ', '').strip().decode('hex').decode('ASCII', errors='ignore')
    Soft = IdRsp[48:53].strip().replace(' ', '')
    Version = IdRsp[54:59].strip().replace(' ', '')

    Std = 'STD_A'

    vinRsp = elm.request(req='2181', positive='61', cache=False)
    # debug
    # vinRsp = '61 81 56 46 31 30 30 30 30 30 30 30 30 30 30 30 30 30 30 00 00 00 00 00 00 00 00'
    if len(vinRsp)>55 and 'NR' not in vinRsp:
      VIN = vinRsp[6:56].strip().replace(' ', '').decode('hex').decode('ASCII', errors='ignore')

  else:
    try:
      # DiagVersion F1A0
      IdRsp_F1A0 = elm.request(req='22F1A0', positive='62', cache=False)
      if len(IdRsp_F1A0) > 8 and 'NR' not in IdRsp_F1A0 and 'BUS' not in IdRsp_F1A0:
        DiagVersion = str(int(IdRsp_F1A0[9:11], 16))

      # Supplier F18A
      IdRsp_F18A = elm.request(req='22F18A', positive='62', cache=False)
      if len(IdRsp_F18A) > 8 and 'NR' not in IdRsp_F18A and 'BUS' not in IdRsp_F18A:
        Supplier = IdRsp_F18A[9:].strip().replace(' ', '').decode('hex').decode('ASCII', errors='ignore')

      # Soft F194
      IdRsp_F194 = elm.request(req='22F194', positive='62', cache=False)
      if len(IdRsp_F194) > 8 and 'NR' not in IdRsp_F194 and 'BUS' not in IdRsp_F194:
        Soft = IdRsp_F194[9:].strip().replace(' ', '').decode('hex').decode('ASCII', errors='ignore')

      # Version F195
      IdRsp_F195 = elm.request(req='22F195', positive='62', cache=False)
      if len(IdRsp_F195) > 8 and 'NR' not in IdRsp_F195 and 'BUS' not in IdRsp_F195:
        Version = IdRsp_F195[9:].strip().replace(' ', '').decode('hex').decode('ASCII', errors='ignore')

      Std = 'STD_B'

      # Vin F190
      vinRsp = elm.request(req='22F190', positive='62', cache=False)
      if len(vinRsp) > 58:
        VIN = vinRsp[9:59].strip().replace(' ', '').decode('hex').decode('ASCII', errors='ignore')
    except:
      pass

  return StartSession, DiagVersion, Supplier, Version, Soft, Std, VIN


def findTCOM( addr, cmd, rsp ):
  ecuvhc = {}
  vehicle = ''
  print 'Read models'
  file_list = mod_db_manager.get_file_list_from_clip('Vehicles/TCOM_*.[Xx]ml')
  for file in file_list:
    vehicle = ''
    DOMTree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(file))
    vh = DOMTree.documentElement
    if vh.hasAttribute("defaultText"):
      vehiclename = vh.getAttribute("defaultText")
      vehTypeCode = vh.getAttribute("vehTypeCode")
      vehTCOM     = vh.getAttribute("TCOM")
      vehicle = vehiclename+'#'+vehTCOM;

      #print vehicle

      connector = vh.getElementsByTagName("Connector")
      cannetwork = connector.item(0).getElementsByTagName("CANNetwork")
      isonetwork = connector.item(0).getElementsByTagName("ISONetwork")
      for pin in cannetwork:
        eculist = pin.getElementsByTagName("EcuList")
        if eculist:
          ecukind = eculist.item(0).getElementsByTagName("EcuKind")
          for ek in ecukind:
            ecuref = ek.getElementsByTagName("EcuRef")
            for er in ecuref:
              ecuname = er.getAttribute("name")
              if ecuname in ecuvhc.keys():
                ecuvhc[ecuname].append(vehicle)
              else:
                ecuvhc[ecuname] = [vehicle]                
      for pin in isonetwork:
        eculist = pin.getElementsByTagName("EcuList")
        if eculist:
          ecukind = eculist.item(0).getElementsByTagName("EcuKind")
          for ek in ecukind:
            ecuref = ek.getElementsByTagName("EcuRef")
            for er in ecuref:
              ecuname = er.getAttribute("name")
              if ecuname in ecuvhc.keys():
                ecuvhc[ecuname].append(vehicle)
              else:
                ecuvhc[ecuname] = [vehicle]

  se = ScanEcus( None )
  print 'Loading Uces.xml'
  se.read_Uces_file(True)
  #print ecuvhc
  for r in se.allecus.keys():
    if se.allecus[r]['dst']!=addr: continue
    if se.allecus[r]['ids'][0]!=cmd: continue
    if se.compare_ecu( se.allecus[r]['ids'], rsp, cmd ):
      try:
        print r, se.allecus[r]['doc'], se.allecus[r]['ids'], ecuvhc[r]
      except:
        print
def generateSavedEcus( eculist, fileName ):  
  se  = ScanEcus( 0 )
  se.read_Uces_file( all = True )
  
  se.detectedEcus = []
  for i in eculist.split(','):
    if  i in se.allecus.keys():
      se.allecus[i]['ecuname']=i
      se.allecus[i]['idf']=se.allecus[i]['ModelId'][2:4]
      if se.allecus[i]['idf'][0]=='0': 
        se.allecus[i]['idf'] = se.allecus[i]['idf'][1]
      se.allecus[i]['pin'] = 'can' 
      se.detectedEcus.append( se.allecus[i] )
  #se.detectedEcus = sorted(se.detectedEcus, key=lambda k: int(k['idf']))
  print se.detectedEcus
  if (len(se.detectedEcus)): pickle.dump( se.detectedEcus, open( fileName, "wb" ) )
  
  
if __name__ == "__main__":

  mod_db_manager.find_DBs()

  # 10016,10074 savedEcus.p_gen  
  if len(sys.argv)==3: generateSavedEcus( sys.argv[1], sys.argv[2] )
  
  # 2C 2180 '80 31 38 35 33 52 04 41 4D 52 30 32 30 34 30 16 30 16 30 00 DD 01 00 00 88 00'  
  if len(sys.argv)==4: findTCOM( sys.argv[1], sys.argv[2], sys.argv[3] )
   
