#!/usr/bin/env python

from mod_utils              import *
from mod_ecu_screen         import *
from mod_ecu_default        import *
from mod_ecu_dataids        import *
from mod_ecu_state          import *
from mod_ecu_parameter      import *
from mod_ecu_command        import *
from mod_ecu_identification import *
from mod_ecu_service        import *
from mod_ecu_mnemonic       import *
from mod_optfile            import *
from mod_ply                import *
from mod_elm                import ELM
from mod_elm                import snat
from mod_elm                import dnat
from mod_elm                import AllowedList
if mod_globals.os != 'android':    
  from mod_ddt                import DDT

import mod_globals
import mod_db_manager

from xml.dom.minidom        import parse
from datetime               import datetime
from collections            import OrderedDict
from mod_utils              import show_doc
import xml.dom.minidom
#import xml.etree.ElementTree as et
#import struct
import sys
import os
import time
import gc
import re

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

#sys.setdefaultencoding('utf-8')

F2A = {           "01":"7A", "02":"01", "03":"51", "04":"26", "05":"2C", "06":"00", "07":"24", "08":"29", "09":"6E",  
       "10":"57", "11":"52", "12":"79", "13":"0D", "14":"00", "15":"32", "16":"37", "17":"6B", "18":"04", "19":"3F",
       "20":"27", "21":"08", "22":"00", "23":"3A", "24":"50", "25":"1C", "26":"00", "27":"99", "28":"00", "29":"07",
       "30":"66", "31":"A7", "32":"60", "33":"4B", "34":"2B", "35":"1B", "36":"61", "37":"25", "38":"1E", "39":"D2",
       "40":"23", "41":"0E", "42":"40", "43":"7C", "44":"97", "45":"3C", "46":"82", "47":"4D", "48":"11", "49":"47",
       "50":"02", "51":"0F", "52":"70", "53":"71", "54":"72", "55":"0E", "56":"1A", "57":"5D",            "59":"E2",
       "60":"A5", "61":"A6", "62":"00", "63":"65", "64":"DF", "65":"2A", "66":"FE", "67":"7B", "68":"73", "69":"16",
       "70":"62",            "72":"00", "73":"63", "74":"81",            "76":"13", "77":"77", "78":"64", "79":"D1",
       "80":"F7", "81":"F8",                                             "86":"2E", "87":"06",
       "90":"59", "91":"86", "92":"87", "93":"00", "94":"67", "95":"93", "96":"95", "97":"68", "98":"A8", "99":"C0"} 
       
ecudump = {} # {'request':'response'}
favouriteScreen = ecu_own_screen( "FAV" )

class ECU:
  '''Contains data for one specific ECU
     implement menu for ecu'''
  
  path = "EcuRenault/Sessions/"
 
  getDTCmnemo     = ""
  resetDTCcommand = ""
  screens         = []
  Defaults        = {}
  Parameters      = {}
  States          = {}
  Identifications = {}
  Commands        = {}
  Services        = {}
  Mnemonics       = {}
  DataIds         = {}
  
  # variables for extended DE information 
  ext_de          = []
  
  ecudata  = {}
  
  minimumrefreshrate = 0.100
    
  def __init__(self, cecu, tran ):
  
    self.elm     = 0
    self.ecudata = cecu

    self.getDTCmnemo     = ""
    self.resetDTCcommand = ""
    self.screens         = []
    self.Defaults        = {}
    self.Parameters      = {}
    self.States          = {}
    self.Identifications = {}
    self.Commands        = {}
    self.Services        = {}
    self.Mnemonics       = {}
    self.DataIds         = {}
    
    print 'Deflen:',len(self.Defaults)

    print "ECU type: ", cecu['stdType']
 
    mdom = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(self.path+self.ecudata['ModelId'].strip()[:-3]+'xml'))
    mdoc = mdom.documentElement
  
    print "Loading screens "
    self.screens = []
    sc_class = ecu_screens( self.screens, mdoc, tran )

    print "Loading optimyzer"
    self.defaults = []
    opt_file = optfile(self.path+self.ecudata['OptimizerId'].strip()[:-3]+'xml')
       
    print "Loading defaults"
    df_class = ecu_defaults       ( self.Defaults,        mdoc, opt_file.dict, tran )
    print "Loading parameters"
    pr_class = ecu_parameters     ( self.Parameters,      mdoc, opt_file.dict, tran )
    print "Loading states"
    st_class = ecu_states         ( self.States,          mdoc, opt_file.dict, tran )
    print "Loading identifications"
    id_class = ecu_identifications( self.Identifications, mdoc, opt_file.dict, tran )
    print "Loading commands"
    cm_class = ecu_commands       ( self.Commands,        mdoc, opt_file.dict, tran )
    print "Loading services"
    sv_class = ecu_services       ( self.Services,        mdoc, opt_file.dict, tran )
    print "Loading mnemonics"
    mm_class = ecu_mnemonics      ( self.Mnemonics,       mdoc, opt_file.dict, tran )
    print "Loading DTC commands"
    self.getDTCmnemo, self.resetDTCcommand = df_class.getDTCCommands( mdoc, opt_file.dict, cecu['stdType'] )
    if "DataIds" in opt_file.dict.keys():
      print "Loading DataIds"     
      xmlstr = opt_file.dict["DataIds"]
      ddom = xml.dom.minidom.parseString( xmlstr.encode( "utf-8" ) )
      ddoc = ddom.documentElement
      di_class = ecu_dataids( self.DataIds, ddoc, opt_file.dict, tran )
      
  def initELM(self, elm):

    print "Loading PLY "
    self.calc = Calc()
    
    print "Init ELM"

    self.elm = elm

    if self.ecudata['pin'].lower()=='can':
      self.elm.init_can()
      self.elm.set_can_addr( self.ecudata['dst'], self.ecudata )
    else:
      self.elm.init_iso()
      self.elm.set_iso_addr( self.ecudata['dst'], self.ecudata )
    
    self.elm.start_session( self.ecudata['startDiagReq'] )

    if mod_globals.os == 'android' or mod_globals.opt_csv:
      if self.ecudata['pin'].lower()=='can' and self.DataIds and mod_globals.opt_perform:
        self.elm.checkModulePerformaceLevel(self.DataIds)

    print "Done"  
    
    global ecudump
    ecudump = {}
    
  def saveDump( self ):
    ''' save responces from all 21xx, 22xxxx commands '''
    
    dumpname = './dumps/'+str(int(time.time()))+'_'+self.ecudata['ecuname']+'.txt'    
    df = open(dumpname,'wt')
    
    self.elm.clear_cache()

    im = ' from ' + str(len(self.Services.keys()))
    i = 0
    for service in self.Services.values():
      i = i + 1
      print '\r\t\t\t\r', str(i)+im,
      sys.stdout.flush()
      if service.startReq[:2] in AllowedList+['17','19']:
        if service.startReq[:2] == '19' and service.startReq[:4] != '1902':
          continue
        pos = chr(ord(service.startReq[0])+4)+service.startReq[1]
        rsp = self.elm.request(service.startReq, pos, False)
        if ':' in rsp: continue
        df.write('%s:%s\n'%(service.startReq,rsp))
    
    df.close()
    
  def loadDump( self, dumpname='' ):
    ''' load saved dump for demo mode '''
    
    global ecudump
    
    ecudump = {}
    
    if len(dumpname)==0:
      flist = []
      for root, dirs, files in os.walk("./dumps"):
        for f in files:
          if (self.ecudata['ecuname']+'.txt') in f:
            flist.append(f)
      
      if len(flist)==0: return
      flist.sort()
      dumpname = os.path.join("./dumps/", flist[-1])

    #print 'Loading dump:', dumpname

    self.elm.loadDump(dumpname)
    #df = open(dumpname,'rt')
    #lines = df.readlines()
    #df.close()
    #
    #for l in lines:
    #  l = l.strip().replace('\n','')
    #  if l.count(':')==1:
    #    req,rsp = l.split(':')
    #    ecudump[req] = rsp
    #
    #self.elm.setDump( ecudump )
    
  def get_st( self, name ):
    if name not in self.States.keys():
      for i in self.States.keys():
        if name==self.States[i].agcdRef:
          name = i
          break
    if name not in self.States.keys():
       return 'none','unknown state'      
    self.elm.clear_cache()
    datastr, help, csvd = get_state( self.States[name], self.Mnemonics, self.Services, self.elm, self.calc )
    return csvd, datastr

  def get_ref_st( self, name ):
    if name not in self.States.keys():
      for i in self.States.keys():
        if name==self.States[i].agcdRef:
          name = i
          break
    if name not in self.States.keys():
       return None
    return self.States[name]     
      
  def get_pr( self, name ):
    if name not in self.Parameters.keys():
      for i in self.Parameters.keys():
        if name==self.Parameters[i].agcdRef:
          name = i
          break
    if name not in self.Parameters.keys():
      return 'none','unknown parameter'      
    self.elm.clear_cache()
    datastr, help, csvd = get_parameter( self.Parameters[name], self.Mnemonics, self.Services, self.elm, self.calc )
    return csvd, datastr
      
  def get_ref_pr( self, name ):
    if name not in self.Parameters.keys():
      for i in self.Parameters.keys():
        if name==self.Parameters[i].agcdRef:
          name = i
          break
    if name not in self.Parameters.keys():
      return None      
    return self.Parameters[name]
      
  def get_id( self, name, raw = False):
    if name not in self.Identifications.keys():
      for i in self.Identifications.keys():
        if name==self.Identifications[i].codeMR:
          name = i
          break
    if name not in self.Identifications.keys():
      return 'none','unknown identification'      
    if raw:
      return get_identification( self.Identifications[name], self.Mnemonics, self.Services, self.elm, self.calc, raw)
    self.elm.clear_cache()
    datastr, help, csvd = get_identification( self.Identifications[name], self.Mnemonics, self.Services, self.elm, self.calc )
    return csvd, datastr

  def get_ref_id( self, name ):
    if name not in self.Identifications.keys():
      for i in self.Identifications.keys():
        if name==self.Identifications[i].codeMR:
          name = i
          break
    if name not in self.Identifications.keys():
      return None      
    return self.Identifications[name]

  def get_val( self, name ):
    r1, r2 = self.get_st( name )
    if r1!='none': return r1, r2
    r1, r2 = self.get_pr( name )
    if r1!='none': return r1, r2
    r1, r2 = self.get_id( name )
    if r1!='none': return r1, r2
    return 'none','unknown name' 
    
  def run_cmd( self, name, param = '', partype = 'HEX' ):
    if name not in self.Commands.keys():
      for i in self.Commands.keys():
        if name==self.Commands[i].codeMR:
          name = i
          break
    if name not in self.Commands.keys():
      return 'none'      
    self.elm.clear_cache()
    resp = runCommand( self.Commands[name], self, self.elm, param, partype )
    return resp
      
  def get_ref_cmd( self, name ):
    if name not in self.Commands.keys():
      for i in self.Commands.keys():
        if name==self.Commands[i].codeMR:
          name = i
          break
    if name not in self.Commands.keys():
      return None      
    return self.Commands[name]
      
  def show_commands(self, datarefs, path):
    while(True): 
      clearScreen()
      header =  "ECU : "+self.ecudata['ecuname']+'  '+self.ecudata['doc']+'\n'
      header = header + "Screen : "+path 
      print pyren_encode( header )   
      menu = []
      cmds = []
      for dr in datarefs:
        datastr = dr.name;
        if dr.type=='State':
          datastr = self.States[dr.name].name + 'States not supported on one screen with commands'
        if dr.type=='Parameter':
          datastr = self.Parameters[dr.name].name + 'Parameters not supported on one screen with commands'
        if dr.type=='Identification':
          datastr = self.Identifications[dr.name].name + 'Identifications not supported on one screen with commands'
        if dr.type=='Command':
          datastr = self.Commands[dr.name].codeMR + " [Command] " + self.Commands[dr.name].label
          cmds.append( dr.name )
        menu.append( datastr )

      menu.append("<Up>")
      choice = ChoiceLong(menu, "Choose :", header)
      if choice[0]=="<Up>": return
      
      header = header +" -> "+cmds[int(choice[1])-1] + " [Command] "
      executeCommand( self.Commands[cmds[int(choice[1])-1]], self, self.elm, header )
         
  def show_datarefs(self, datarefs, path):
  
    clearScreen()
    if os.name == 'nt':
      initScreen = chr(27)+"[;H"
    else:
      initScreen = chr(27)+"[2J"+chr(27)+"[;H"

    csvf = 0
    self.elm.currentScreenDataIds = []

    mask = False
    masks = []
    datarefsToRemove = []

    for st in self.States:
      if st.startswith('MAS'):
        mask = True
        get_state( self.States[st], self.Mnemonics, self.Services, self.elm, self.calc )
        if int(self.States[st].value):
          masks.append(self.States[st].name)
    
    if mask and not mod_globals.opt_demo:
      for dr in datarefs:
        if dr.type=='State':
          if self.States[dr.name].mask and self.States[dr.name].mask not in masks:
            datarefsToRemove.append(dr)
        if dr.type=='Parameter':
          if self.Parameters[dr.name].mask and self.Parameters[dr.name].mask not in masks:
            datarefsToRemove.append(dr)
        if dr.type=='Identification':
          if self.Identifications[dr.name].mask and self.Identifications[dr.name].mask not in masks:
            datarefsToRemove.append(dr)
        if dr.type=='Command':
          if self.Commands[dr.name].mask and self.Commands[dr.name].mask not in masks:
            datarefsToRemove.append(dr)
      for dr in datarefsToRemove:
        datarefs.remove(dr)
    
    #Check if datarefs contains any commands
    for dr in datarefs:
      if dr.type=='Command':
        self.show_commands(datarefs, path)
        return

    if mod_globals.opt_csv and mod_globals.ext_cur_DTC == '000000':
      # prepare to csv save
      self.minimumrefreshrate = 0
      csvline = "sep=\\t\n"
      csvline += u"Time"
      nparams = 0
      for dr in datarefs:
        if dr.type=='State':
          csvline += ";" + self.States[dr.name].codeMR + ":" + self.States[dr.name].label
          nparams += 1
        if dr.type=='Parameter':
          csvline += (";" + self.Parameters[dr.name].codeMR + ":" +self.Parameters[dr.name].label + " [" + self.Parameters[dr.name].unit + "]")
          nparams += 1
      if mod_globals.opt_usrkey: csvline += ";User events"
      csvline = pyren_encode(csvline)
      if nparams:
        csv_filename = datetime.now().strftime("%y_%m_%d_%H_%M_%S")
        #here the problem with russian letters. and very long name
        csv_filename = csv_filename+'_'+self.ecudata['ecuname']+'_'+path
        csv_filename += ".csv"
        csv_filename = csv_filename.replace('/','_')
        csv_filename = csv_filename.replace(' : ','_')
        csv_filename = csv_filename.replace(' -> ','_')
        csv_filename = csv_filename.replace(' ','_')
        #if mod_globals.os == 'android':
        #  csv_filename = csv_filename.encode("ascii","ignore")
        csvf = open("./csv/"+pyren_encode(csv_filename), "wt")

    DTCpos = path.find('DTC')
    if DTCpos > 0:
      IDstr = '#' + path[DTCpos+3:DTCpos + 9]
    else:
      IDstr = ''

    #debug
    #show_doc(self.ecudata['dst'], IDstr)

    kb = KBHit()

    tb = time.time()   #time of begining 

    if len(datarefs)==0 and 'DE' not in path: return
    self.elm.clear_cache()

    #csv_only mode workflow in performance mode
    #1. Read all parameters from the current screen using defalut mode  
    #2. Get all dataIds from the 22 service requests and create a list from them according to a module performance level
    #3. Collect all 21 service requests and push them into requests list
    #4. Create a complex requests from the all dataIds list and push them into requests list
    #5. Send reqests from the requests list and save the responses in a responseHistory list
    #6. On exit generate csv log file from the responseHistory
    
    if mod_globals.opt_csv_only:
      print "Data is sending directly to csv-file"
      print ""
      print "Press any key to exit"

    page = 0

    displayedDataIds = [] #Current screen dataIds list for csv_only mode
    responseHistory = OrderedDict()
    requests = OrderedDict() #list of requests to send in csv_only mode
    
    while(True):
      
      strlst = []
      datarefsRequestTime = int(round(time.time() * 1000))
      
      if mod_globals.opt_csv_human and csvf!=0:
        csvline = csvline + "\n"
        #csvline = csvline.replace('.',',')
        #csvline = csvline.replace(',','.')
        csvline = csvline.replace(';','\t')
        csvf.write(pyren_decode(csvline).encode('utf8'))
        #if mod_globals.os == 'nt' or mod_globals.os == 'android':
        #  csvf.write(pyren_decode(csvline).encode('cp1251')  if mod_globals.opt_csv_human else csvline)
        #else:
        #  csvf.write(pyren_decode(csvline).encode('utf8')  if mod_globals.opt_csv_human else csvline)
        csvf.flush() 
        csvline = datetime.now().strftime("%H:%M:%S.%f")

      #Collect all the requests from the current screen
      if mod_globals.opt_perform and self.elm.performanceModeLevel > 1 and mod_globals.opt_csv_only:
        if self.elm.rsp_cache:
          if not requests:
            requests = self.generateRequestsList()

      self.elm.clear_cache()
      if not (mod_globals.opt_csv_only and requests):
        for dr in datarefs:
          datastr = dr.name
          help    = dr.type
          if dr.type=='State':
            if self.DataIds and "DTC" in path and dr in self.Defaults[mod_globals.ext_cur_DTC[:4]].memDatarefs:
              datastr, help, csvd = get_state( self.States[dr.name], self.Mnemonics, self.Services, self.elm, self.calc, self.DataIds )
            else:
              datastr, help, csvd = get_state( self.States[dr.name], self.Mnemonics, self.Services, self.elm, self.calc )
          if dr.type=='Parameter':
            if self.DataIds and "DTC" in path and dr in self.Defaults[mod_globals.ext_cur_DTC[:4]].memDatarefs:
              datastr, help, csvd = get_parameter( self.Parameters[dr.name], self.Mnemonics, self.Services, self.elm, self.calc, self.DataIds )
            else:
              datastr, help, csvd = get_parameter( self.Parameters[dr.name], self.Mnemonics, self.Services, self.elm, self.calc )
          if dr.type=='Identification':
            datastr, help, csvd = get_identification( self.Identifications[dr.name], self.Mnemonics, self.Services, self.elm, self.calc )       
          if dr.type=='Command':
            datastr = dr.name + " [Command] " + self.Commands[dr.name].label
          if dr.type=="Text":
            datastr = dr.name
            help = ""
          if mod_globals.opt_csv_human and csvf!=0 and (dr.type=='State' or dr.type=='Parameter'):
            csvline += ";" + pyren_encode(csvd)

          if not (mod_globals.opt_csv and mod_globals.opt_csv_only):
            strlst.append(datastr)
            if mod_globals.opt_verbose and len(help)>0:
              tmp_str = ''
              for s in help:
                #s = s.replace('\n','\n\t')
                s = s.replace('\r','\n')
                s = s.replace('&gt;','>')           
                s = s.replace('&le;','<')           
                tmp_str = tmp_str + s + '\n\n'
              W = 50
              for line in tmp_str.split('\n'):
                i = 0
                while i*W<len(line):
                  strlst.append('\t'+line[i*W:(i+1)*W])
                  i=i+1
              strlst.append('')
      else: #Send requests, do not calculate data
        for req in requests:
          self.elm.request(req)

      if not (mod_globals.opt_csv and mod_globals.opt_csv_only):
        newScreen = initScreen
        connectionData = ('   (RT:'+'{0:.4f}'.format(self.elm.response_time)+ ' ' 
                            + 'RR:' + '{:>5.1f}'.format(self.elm.getRefreshRate()) +')   ')
        
        header =  'ECU : '+self.ecudata['ecuname']+ connectionData +self.ecudata['doc']+'\n'
        header = header + "Screen : "+path
        newScreen = newScreen + pyren_encode( header ) + '\n'
      
        H = 25
        
        pages = len(strlst)/H
        for l in strlst[page*H:(page+1)*H]:
          newScreen = newScreen + pyren_encode( l ) + '  \n'
        if not path[:3] == 'FAV':
          if pages>0:
            newScreen = newScreen+'\n'+"[Page "+str(page+1)+" from "+str(pages+1)+"] [N-next P-prev.] H for help or any other to exit"
          else:
            newScreen = newScreen+'\n'+"Press H for help or any key to exit"
        else:
          newScreen = newScreen+'\n'+"Press ENTER to add or delete parameter or any other key to exit" 

        print newScreen,
        sys.stdout.flush ()
        
        # check refresh rate
        if mod_globals.opt_demo:
          self.minimumrefreshrate = 1

        tc = time.time()
        if ((tc - tb) < self.minimumrefreshrate):
          time.sleep(tb + self.minimumrefreshrate - tc)
        tb = tc
      
      if mod_globals.opt_csv_only:
        responseHistory[datarefsRequestTime] = self.elm.rsp_cache #Collect data to generate a file

      if mod_globals.opt_perform and self.elm.performanceModeLevel > 1:
        self.elm.currentScreenDataIds = self.getDataIds(self.elm.rsp_cache, self.DataIds)
        if self.elm.currentScreenDataIds: #DataIds list is generated only at first data read pass in csv_only mode
          displayedDataIds = self.elm.currentScreenDataIds #We save it for file generating function

      if kb.kbhit():
        c = kb.getch()
        if len(c)!=1: continue
        if path[:3] == 'FAV':
          if ord(c) == 13 or ord(c) == 10:
            kb.set_normal_term()
            self.add_favourite()
            kb.set_getch_term()
          else:
            if mod_globals.opt_csv and (c in mod_globals.opt_usrkey):
              csvline += ";" + pyren_encode(c)
              continue
            kb.set_normal_term()
            self.saveFavList()
            if mod_globals.opt_csv and csvf!=0:
              if mod_globals.opt_csv_human:
                csvf.close()
                return
              self.createFile(responseHistory, displayedDataIds, csvline, csvf, datarefs)
            return
        else:
          n = ord(c)-ord('0')
          if (not mod_globals.opt_csv_only) and n>0 and n<=(pages+1):
            page = n-1
            clearScreen()
            continue
          if c in ['h','H']:
            show_doc(self.ecudata['dst'], IDstr)
            continue
          if c in ['p','P']:
            if page>0:
              page = page-1
            clearScreen()
            continue
          if c in ['n','N']:
            if page<pages:
              page = page+1
            clearScreen()
            continue
          if mod_globals.opt_csv and (c in mod_globals.opt_usrkey):
            csvline += ";" + pyren_encode(c)
            continue
          kb.set_normal_term()
          if mod_globals.opt_csv and csvf!=0:
            if mod_globals.opt_csv_human:
              csvf.close()
              return
            self.createFile(responseHistory, displayedDataIds, csvline, csvf, datarefs)
          if "DTC" in path:
            mod_globals.ext_cur_DTC = "000000"
          return
  
  def generateRequestsList(self):
    requests = OrderedDict()

    currentScreenDataIdsLength = len(self.elm.currentScreenDataIds)
    for reqDidsIndex in range(currentScreenDataIdsLength): #Create complex requests from all 22 requests
      firstRequest = '22' + self.elm.currentScreenDataIds[0][0].id
      complexRequest, sentDataIdentifires = prepareComplexRequest(firstRequest, self.elm.currentScreenDataIds)
      requests[complexRequest] = complexRequest
    for req in self.elm.rsp_cache.keys(): #Get all the 21 requests
      if req.startswith('21'):
        requests[req] = req
    
    return requests

  def createFile(self, responseHistory, displayedDataIds, csvline, csvf, datarefs):
    clearScreen()
    print 'Generating a file. Please wait...'
    
    for reqTime, reqCache in responseHistory.iteritems():
      for req, rsp in reqCache.iteritems():
        if req.startswith('22') and len(req) > 6:
          for reqDids in displayedDataIds:
            if reqDids[0].id == req[2:6]:
              parseComplexResponse(self.elm, '62', rsp.replace(' ', ''), reqDids)
        else:
          self.elm.rsp_cache[req] = rsp

      csvline = csvline + "\n"
      csvline = csvline.replace(';','\t')
      csvf.write(pyren_decode(csvline).encode('utf8'))
      csvf.flush()
      csvline = datetime.fromtimestamp(reqTime/1000.0).strftime("%H:%M:%S.%f")[:-3]

      for dr in datarefs:
        datastr = dr.name
        help    = dr.type
        if dr.type=='State':
          datastr, help, csvd = get_state( self.States[dr.name], self.Mnemonics, self.Services, self.elm, self.calc )
        if dr.type=='Parameter':
          datastr, help, csvd = get_parameter( self.Parameters[dr.name], self.Mnemonics, self.Services, self.elm, self.calc )
        if csvf!=0 and (dr.type=='State' or dr.type=='Parameter'):
          csvline += ";" + pyren_encode(csvd)
    
    csvf.close()

  def add_favourite(self):
    H = 25
    if len(favouriteScreen.datarefs) < H:
      userDataStr = raw_input("\nEnter parameter that you want to monitor: ").upper()
      for userData in userDataStr.split(','):
        userData = userData.strip()
        if userData == "CLEAR":
          del favouriteScreen.datarefs[:]
        pr = self.add_elem(userData)
        if pr:
          for dr in favouriteScreen.datarefs:
            if pr == dr.name:
              favouriteScreen.datarefs.remove(dr)
    else:
      raw_input("\nYou have reached parameters limit. Removing last parameter.")
      favouriteScreen.datarefs.pop()
    clearScreen()

  def loadFavList(self):

    fn = "./cache/favlist_"+self.ecudata['ecuname']+".txt"

    if not os.path.isfile(fn):
      favlistfile = open( fn, "wb" )
      favlistfile.close()

    fl = open(fn, "r").readlines()
    if len(fl):
      for drname in fl:
        drname = drname.strip().replace('\n','')
        if not (drname.startswith("PR") or drname.startswith("ET") or drname.startswith("ID")):
          return False
        else:
          self.add_elem(drname)
      return True
    else:
      return False

  def add_elem(self, elem):
    if elem[:2] == "PR":
      for pr in self.Parameters.keys():
        if self.Parameters[pr].agcdRef == elem:
          if not any(pr == dr.name for dr in favouriteScreen.datarefs):
            favouriteScreen.datarefs.append(ecu_screen_dataref("",pr,"Parameter"))
            return False
          else:
            return pr
    elif elem[:2] =="ET":
      for st in self.States.keys():
        if self.States[st].agcdRef == elem:
          if not any(st == dr.name for dr in favouriteScreen.datarefs):
            favouriteScreen.datarefs.append(ecu_screen_dataref("",st,"State"))
            return False
          else:
            return st
    elif elem[:2] =="ID":
      for idk in self.Identifications.keys():
        if self.Identifications[idk].agcdRef == elem:
          if not any(idk == dr.name for dr in favouriteScreen.datarefs):
            favouriteScreen.datarefs.append(ecu_screen_dataref("",idk,"Identification"))
            return False
          else:
            return idk        
    else:
      return False  

  def saveFavList(self):
    fl = open("./cache/favlist_"+self.ecudata['ecuname']+".txt", "w")
    for dr in favouriteScreen.datarefs:
      if dr.name.startswith('P'):
        for pr in self.Parameters.keys():
          if dr.name == pr:
            fl.write(self.Parameters[pr].agcdRef + "\n")
      if dr.name.startswith('E'):
        for st in self.States.keys():
          if dr.name == st:
            fl.write(self.States[st].agcdRef + "\n")
      if dr.name.startswith('I'):
        for idk in self.Identifications.keys():
          if dr.name == idk:
            fl.write(self.Identifications[idk].agcdRef + "\n")
    fl.close() 

  def show_subfunction(self, subfunction, path):
    while(1): 
      clearScreen()
      header = "ECU : "+self.ecudata['ecuname']+'  '+self.ecudata['doc']+'\n'
      header = header + "Screen : "+path+" -> "+subfunction.text 
      print pyren_encode( header )
         
      menu = []
      if len(subfunction.datarefs)!=0 and len(subfunction.datarefs)>0:
        self.show_datarefs(subfunction.datarefs, path+" -> "+subfunction.text )
        return
      else:
        return        
   
  def show_function(self, function, path):
    while(1): 
      clearScreen()
      header =  "ECU : "+self.ecudata['ecuname']+'  '+self.ecudata['doc']+'\n'
      header = header + "Screen : "+path+" -> "+function.text
      print pyren_encode( header ) 
         
      menu = []
      if len(function.datarefs)!=0 and len(function.subfunctions)!=0:
        print "Warning: both datarefs and functions not empty"
      if len(function.subfunctions)!=0:
        for sfu in function.subfunctions:
          menu.append(sfu.text)
        menu.append("<Up>")
        choice = Choice(menu, "Choose :")
        if choice[0]=="<Up>": return
        self.show_subfunction(function.subfunctions[int(choice[1])-1], path+" -> "+function.text )    
      if len(function.datarefs)!=0:
        self.show_datarefs(function.datarefs, path+" -> "+function.text )
        return        
   
  def show_screen(self, screen):
    while(1): 
      clearScreen()
      header = "ECU : "+self.ecudata['ecuname']+'  '+self.ecudata['doc']+'\n'
      header = header + "Screen : "+screen.name    
      print pyren_encode( header ) 
      
      menu = []
      if len(screen.datarefs)!=0 and len(screen.functions)!=0:
        print "Warning: both datarefs and functions not empty"
      if len(screen.functions)!=0:
        for fu in screen.functions:
          menu.append(fu.text)
        menu.append("<Up>")
        choice = Choice(menu, "Choose :")
        if choice[0]=="<Up>": return
        self.show_function(screen.functions[int(choice[1])-1],screen.name)    
      if len(screen.datarefs)!=0:
        self.show_datarefs(screen.datarefs, screen.name)
        return        
  
  def show_defaults_std_a(self):
    while(1):
      path = "DE (STD_A)"
      clearScreen()
      header =  "ECU : "+self.ecudata['ecuname']+'  '+self.ecudata['doc']+'\n'
      header = header + "Screen : " + path 
      print pyren_encode( header ) 
          
      menu = []
      
      defstr = {}
      hlpstr = {}
  
      self.elm.clear_cache()
  
      dtcs, defstr, hlpstr = get_default_std_a( self.Defaults, self.Mnemonics, self.Services, self.elm, self.calc, self.getDTCmnemo )
      
      listkeys = defstr.keys()
      for d in listkeys:
        menu.append(defstr[d])

      menu.append("<Up>")
      menu.append("<Clear>")
      choice = Choice(menu, "Choose one for detailed view or <Clear>:")
  
      if choice[0]=="<Up>": return
      if choice[0]=="<Clear>": 
        print "Executing command ", self.resetDTCcommand
        executeCommand( self.Commands[self.resetDTCcommand], self, self.elm, header )
        return
      
      index = int(choice[1])-1
      dtchex = listkeys[index] if len(listkeys) > index else listkeys[0]
      mod_globals.ext_cur_DTC = dtchex
      
      path = path+' -> '+defstr[dtchex]+'\n\n'+hlpstr[dtchex]+'\n'

      cur_dtrf = []
      mem_dtrf = []

      if self.Defaults[dtchex[:4]].datarefs:
        cur_dtrf = [ecu_screen_dataref(0, "\n" + mod_globals.language_dict['300'] + "\n", 'Text')] + self.Defaults[dtchex[:4]].datarefs
      if self.Defaults[dtchex[:4]].memDatarefs:
        mem_dtrf_txt = mod_globals.language_dict['299'] + " DTC" + mod_globals.ext_cur_DTC + "\n"
        mem_dtrf = [ecu_screen_dataref(0, mem_dtrf_txt, 'Text')] + self.Defaults[dtchex[:4]].memDatarefs
      
      tmp_dtrf = mem_dtrf + cur_dtrf

      self.show_datarefs(tmp_dtrf, path)
    
  def show_defaults_std_b(self):
    while(1):
      path = "DE (STD_B)"
      clearScreen()
      header = "ECU : "+self.ecudata['ecuname']+'  '+self.ecudata['doc']+'\n'
      header = header + "Screen : " + path
      print pyren_encode( header ) 
           
      menu = []
      
      defstr = {}
      hlpstr = {}
  
      self.elm.clear_cache()
  
      dtcs, defstr, hlpstr = get_default_std_b( self.Defaults, self.Mnemonics, self.Services, self.elm, self.calc, self.getDTCmnemo )
      
      listkeys = defstr.keys()
      for d in listkeys:
        menu.append(defstr[d])
         
      menu.append("<Up>")
      menu.append("<Clear>")
      choice = Choice(menu, "Choose one for detailed view or <Clear>:")
  
      if choice[0]=="<Up>": return
      if choice[0]=="<Clear>": 
        print "Executing command ", self.resetDTCcommand
        executeCommand( self.Commands[self.resetDTCcommand], self, self.elm, header )
        return
          
      index = int(choice[1])-1
      dtchex = listkeys[index] if len(listkeys) > index else listkeys[0]
      mod_globals.ext_cur_DTC = dtchex

      path = path+' -> '+defstr[dtchex]+'\n\n'+hlpstr[dtchex]+'\n'

      cur_dtrf = []
      mem_dtrf = []
      ext_info_dtrf = []

      if self.Defaults[dtchex[:4]].datarefs:
        cur_dtrf = [ecu_screen_dataref(0, "\n" + mod_globals.language_dict['300'] + "\n", 'Text')] + self.Defaults[dtchex[:4]].datarefs
      if self.Defaults[dtchex[:4]].memDatarefs:
        mem_dtrf_txt = mod_globals.language_dict['299'] + " DTC" + mod_globals.ext_cur_DTC + "\n"
        mem_dtrf = [ecu_screen_dataref(0, mem_dtrf_txt, 'Text')] + self.Defaults[dtchex[:4]].memDatarefs
      if self.ext_de:
        ext_info_dtrf = [ecu_screen_dataref(0, "\n" + mod_globals.language_dict['1691'] + "\n", 'Text')] + self.ext_de

      tmp_dtrf = mem_dtrf + cur_dtrf + ext_info_dtrf
      
      #self.show_datarefs(self.Defaults[dtchex[:4]].datarefs, path) 
      self.show_datarefs(tmp_dtrf, path) 
    
  def show_defaults_failflag(self):
    while(1):
      path = "DE (FAILFLAG)"
      clearScreen()
      header =  "ECU : "+self.ecudata['ecuname']+'  '+self.ecudata['doc']+'\n'      
      header = header + "Screen : " + path
      print pyren_encode( header ) 
           
      menu = []
      
      defstr = {}
      hlpstr = {}
  
      self.elm.clear_cache()
      
      dtcs, defstr, hlpstr = get_default_failflag( self.Defaults, self.Mnemonics, self.Services, self.elm, self.calc )
      
      for d in sorted(defstr.keys()):
        menu.append(defstr[d])
         
      menu.append("<Up>")
      menu.append("<Clear>")
      choice = Choice(menu, "Choose one for detailed view or <Clear>:")
  
      if choice[0]=="<Up>": return
      if choice[0]=="<Clear>": 
        print "Executing command ", self.resetDTCcommand
        #header = "ECU : "+self.ecudata['ecuname']+'  '+self.ecudata['doc']+'\n'+ \
        #     "Screen : "+path
        executeCommand( self.Commands[self.resetDTCcommand], self, self.elm, header )
        return
          
      dtchex = dtcs[int(choice[1])-1]
      mod_globals.ext_cur_DTC = dtchex
      
      path = path+' -> '+defstr[dtchex]+'\n\n'+hlpstr[dtchex]+'\n'
      
      self.show_datarefs(self.Defaults[dtchex].datarefs, path) 
    
  def show_screens(self):
    self.screens.append(favouriteScreen)
    while(1):
      clearScreen()
      header = "ECU : "+self.ecudata['ecuname']+'  '+self.ecudata['doc']+'\n'
      print pyren_encode( header ) 

      menu = []
      for l in self.screens:
        if l.name=="DE": l.name = "DE : Device errors"
        if l.name=="ID": l.name = "ID : Identifications"
        if l.name=="SY": l.name = "SY : System state"
        if l.name=="LC": l.name = "LC : System configuration"
        if l.name=="SP": l.name = "SP : System parameters"
        if l.name=="AC": l.name = "AC : Executing tests"
        if l.name=="CF": l.name = "CF : Changing configuration"
        if l.name=="VP": l.name = "VP : VIN programming"
        if l.name=="RZ": l.name = "RZ : Resets"
        if l.name=="SC": l.name = "SC : Configuration scenarios"
        if l.name=="SCS": l.name = "SCS : Security configuration scenarios"
        if l.name=="EZ": l.name = "EZ : EZSTEP"
        if l.name=="FAV": l.name = "FAV : Favourite Parameters"
        if l.name=="ED":           
          self.ext_de = l.datarefs
          l.name = "ED : DE extra information"
          continue
        menu.append(l.name)
      if mod_globals.opt_cmd : menu.append("ECM : Extended command set")
      if self.Parameters : menu.append("PRA : Parameters list")
      if self.States : menu.append("ETA : States list")
      if self.Identifications : menu.append("IDA : Identifications list")
      if mod_globals.opt_ddt : menu.append("DDT : DDT screens")
      menu.append("<Up>")
      choice = Choice(menu, "Choose :")
      if choice[0]=="<Up>":
        favouriteScreen.datarefs = []
        return
      
      if choice[0][:2]=="DE": 
        if self.ecudata['stdType']=='STD_A':
          self.show_defaults_std_a()
        if self.ecudata['stdType']=='STD_B' or self.ecudata['stdType']=='UDS' :
          self.show_defaults_std_b()
        if self.ecudata['stdType']=='FAILFLAG':
          self.show_defaults_failflag()
        continue

      if choice[0][:3]=="ECM":  
        scrn = ecu_screen( "ECM" ) 
        scrn.datarefs = []
        for cm in sorted(self.Commands):
          scrn.datarefs.append( ecu_screen_dataref("",cm,"Command")) 
        self.show_screen(scrn)
        continue

      if choice[0][:3]=="PRA":  
        scrn = ecu_screen( "PRA" ) 
        scrn.datarefs = []
        tempDict = {}
        for pr in self.Parameters:
          if not self.Parameters[pr].agcdRef.endswith('FF'):
            tempDict[pr] = self.Parameters[pr].codeMR
        sortedParams = sorted(tempDict.items(), key=lambda x:int(x[1][2:]))
        for pr in sortedParams:
          if self.Parameters[pr[0]].mnemolist:
            if self.Mnemonics[self.Parameters[pr[0]].mnemolist[0]].serviceID:
              scrn.datarefs.append( ecu_screen_dataref("",pr[0],"Parameter")) 
        self.show_screen(scrn)
        continue
      
      if choice[0][:3]=="ETA":  
        scrn = ecu_screen( "ETA" ) 
        scrn.datarefs = []
        tempDict = {}
        for st in self.States:
          if not self.States[st].agcdRef.endswith('FF') and self.States[st].agcdRef.startswith('ET'):
            tempDict[st] = self.States[st].codeMR
        sortedStates = sorted(tempDict.items(), key=lambda x:[int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', x[1])])
        for st in sortedStates:
          if self.States[st[0]].mnemolist:
            if self.Mnemonics[self.States[st[0]].mnemolist[0]].serviceID:
              scrn.datarefs.append( ecu_screen_dataref("",st[0],"State")) 
        self.show_screen(scrn)
        continue

      if choice[0][:3]=="IDA":  
        scrn = ecu_screen( "IDA" ) 
        scrn.datarefs = []
        for idk in sorted(self.Identifications):
          scrn.datarefs.append( ecu_screen_dataref("",idk,"Identification")) 
        self.show_screen(scrn)
        continue
      
      if choice[0][:3]=="DDT":
        langmap = self.getLanguageMap()  
        ddt = DDT(self.elm, self.ecudata, langmap)
        del(ddt)
        gc.collect ()
        continue

      fav_sc = self.screens[int(choice[1]) - 1]
      if choice[0][:3] == "FAV":
        for sc in self.screens:
            if sc.name.startswith('FAV'):
                fav_sc = sc
        if not favouriteScreen.datarefs:
          if self.loadFavList():
            self.show_screen(fav_sc)
          else:
            self.add_favourite()
        else:
          self.show_screen(fav_sc)
      else:   
        self.show_screen(fav_sc)
      
  def getLanguageMap(self):
    
    map = {}
    
    for i in sorted(self.Parameters.keys()):
              
      m = self.Mnemonics[self.Parameters[i].mnemolist[0]]
      
      label = self.Parameters[i].label
      
      if 'ETAT' in label:   continue
           
      if len(self.Parameters[i].mnemolist)!=1:
        continue
      if m.bitsLength=='':  continue
      if m.startBit=='':    continue
      if m.startByte=='':   continue
      
      key = "%s:%s:%s:%s"%(m.request,m.startByte,m.startBit,m.bitsLength)
      
      map[key] = label
      
    for i in sorted(self.States.keys()):
        
      m = self.Mnemonics[self.States[i].mnemolist[0]]
      
      label = self.States[i].label

      if 'ETAT' in label:   continue
      
      if len(self.States[i].mnemolist)!=1:
        continue
      if m.bitsLength=='':  continue
      if m.startBit=='':    continue
      if m.startByte=='':   continue
      
      bitsLength =m.bitsLength
      startBit   =m.startBit
      
      #experiment
      comp = self.States[i].computation
      if (m.name+'#') in comp:
        comp = comp.split(m.name+'#')[1]
        startBit = 7 - int( comp[0] )
        bitsLength = 1
        
      #if m.littleEndian != '1':
      #  startBit = 7 - int(startBit)
        
      key = "%s:%s:%s:%s"%(m.request,m.startByte,startBit,bitsLength)
      
      #debug
      #print key, m.littleEndian, label
      
      map[key] = label
    
    return map
  
  def getDataIds(self, cache, dataids):
    dataIdsList = []
    if self.elm.performanceModeLevel == 1:
      return dataIdsList
    
    for req in cache:
      if req.startswith('22'):
        if req[2:] in dataids.keys():
          if req not in self.elm.notSupportedCommands:
            dataIdsList.append(dataids[req[2:]])

    chunk_size = self.elm.performanceModeLevel
    if dataIdsList:
      # split dataIdsList into chunks based on the performace level
      return [dataIdsList[offset:offset+chunk_size] for offset in range(0, len(dataIdsList), chunk_size)]
    
    return dataIdsList

def bukva( bt, l, sign = False ):
  S1 = chr((bt-l) % 26 + ord('A'))
  ex = int(bt-l) / 26
  if ex:
    S2 = chr((ex-1) % 26 + ord('A'))
    S1 = S2 + S1
  if sign: 
    S1 = 'signed('+S1+')'
  return S1

def gen_equ( m ):

  l = len(m.request)/2+1  
  sb = int(m.startByte)
  bits   = int(m.bitsLength)
  sbit   = int(m.startBit)
  bytes  = (bits+sbit-1)/8+1
  rshift = ((bytes+1)*8 - (bits+sbit))%8
  mask = str(2**bits-1)
  
  if m.type.startswith('SNUM'):
    sign = True
  else:
    sign = False
  
  equ = bukva(sb,l,sign)
  
  if bytes==2:
    equ = bukva(sb,l,sign)+'*256+'+bukva(sb+1,l)
  if bytes==3:
    equ = bukva(sb,l,sign)+'*65536+'+bukva(sb+1,l)+'*256+'+bukva(sb+2,l)
  if bytes==4:
    equ = bukva(sb,l,sign)+'*16777216+'+bukva(sb+1,l)+'*65536+'+bukva(sb+2,l)+'*256+'+bukva(sb+3,l)
    
  if m.littleEndian == '1':
    if bytes==2:
      equ = bukva(sb+1,l,sign)+'*256+'+bukva(sb,l)
    if bytes==3:
      equ = bukva(sb+2,l,sign)+'*65536+'+bukva(sb+1,l)+'*256+'+bukva(sb,l)
    if bytes==4:
      equ = bukva(sb+3,l,sign)+'*16777216+'+bukva(sb+2,l)+'*65536+'+bukva(sb+1,l)+'*256+'+bukva(sb,l)

  if len(equ)>2:
    if equ[0]=='(' and equ[-1]==')':
      pass
    else:
      equ = '('+equ+')'

  if bits%8:
    smask = '&'+mask
  else:
    smask = ''

  if bits==1:
    equ = "{"+equ+":"+str(rshift)+"}"
  elif rshift==0:
    equ = equ+smask
  else:
    equ = "("+equ+">"+str(rshift)+")"+smask
  
  if len(equ)>2:
    if (equ[0]=='(' and equ[-1]==')') or (equ[0]=='{' and equ[-1]=='}') :
      pass
    else:
      equ = '('+equ+')'
  
  return equ 

def find_real_ecuid( eid ):

  fastinit = ''
  slowinit = ''
  protocol = ''
  candst   = ''
  startDiagReq = '10C0'

  DOMTree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip("EcuRenault/Uces.xml"))
  Ecus = DOMTree.documentElement
  EcuDatas = Ecus.getElementsByTagName("EcuData")

  if EcuDatas:
    for EcuData in EcuDatas:
      
      name = EcuData.getAttribute("name")
      
      if name==eid:
        
        if EcuData.getElementsByTagName("ModelId").item(0).firstChild:
          eid = EcuData.getElementsByTagName("ModelId").item(0).firstChild.nodeValue
        else:
          eid = name

        ecui = EcuData.getElementsByTagName("ECUInformations")
        if ecui:
          
          fastinit_tag = ecui.item(0).getElementsByTagName("FastInitAddress")
          if fastinit_tag:
            fastinit = fastinit_tag.item(0).getAttribute("value")
          
          slowinit_tag = ecui.item(0).getElementsByTagName("SlowInitAddress")
          if slowinit_tag:
            slowinit = slowinit_tag.item(0).getAttribute("value")
                    
          protocol_tag = ecui.item(0).getElementsByTagName("Protocol")
          if protocol_tag:
            protocol = protocol_tag.item(0).getAttribute("value")
          
          addr = ecui.item(0).getElementsByTagName("Address")
          if addr:
            candst = addr.item(0).getAttribute("targetAddress")
                        
          frms = ecui.item(0).getElementsByTagName("Frames")
          if frms:
            StartDiagSession = frms.item(0).getElementsByTagName("StartDiagSession")
            if StartDiagSession:
              startDiagReq = StartDiagSession.item(0).getAttribute("request")
        break

  if len(eid)>5:
    eid = eid.upper().replace('FG','')
    eid = eid.upper().replace('.XML','')

  return eid, fastinit, slowinit, protocol, candst, startDiagReq

  
def main():

  try:
    import androidhelper as android
    mod_globals.os = 'android'
  except:
    try:
      import android
      mod_globals.os = 'android'
    except:
      pass
      
  if mod_globals.os == 'android':    
    ecuid = raw_input('Enetr  ECU ID:')
    lanid = raw_input('Language [RU]:')
    if len(lanid)<2: lanid = 'RU'
    sys.argv.append(ecuid)
    sys.argv.append(lanid)
    sys.argv.append('TORQ')    
    
  if len(sys.argv)<3:
    print "Usage: mod_ecu.py <ID> <language> [torq] [nochk]"
    print "Example:"
    print "   mod_ecu.py 10016 RU "
    sys.exit(0)
  
  ecuid = sys.argv[1]
  lanid = sys.argv[2]

  mod_db_manager.find_DBs()

  if len(ecuid)==5:
    ecuid, fastinit, slowinit, protocol, candst, startDiagReq = find_real_ecuid(ecuid)
    sys.argv[1] = ecuid
  
  Defaults        = {}
  Parameters      = {}
  States          = {}
  Identifications = {}
  Commands        = {}
  Services        = {}
  Mnemonics       = {}
  
  print "Loading language "
  sys.stdout.flush()                                         
  lang = optfile("Location/DiagOnCAN_"+lanid+".bqm",True)
  print "Done"
  sys.stdout.flush()                                         
  
  fgfile = "EcuRenault/Sessions/FG"+ecuid+".xml"
  sgfile = "EcuRenault/Sessions/SG"+ecuid+".xml"

  mdom = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(fgfile))
  mdoc = mdom.documentElement
  
  print "Loading optimyzer"
  sys.stdout.flush()                                         
  #opt_file = optfile(mod_db_manager.get_file_from_clip(sgfile))
  opt_file = optfile(sgfile)

  print "Loading defaults"
  df_class = ecu_defaults       ( Defaults,        mdoc, opt_file.dict, lang.dict )
  print "Loading parameters"
  pr_class = ecu_parameters     ( Parameters,      mdoc, opt_file.dict, lang.dict )
  print "Loading states"
  st_class = ecu_states         ( States,          mdoc, opt_file.dict, lang.dict )
  print "Loading identifications"
  id_class = ecu_identifications( Identifications, mdoc, opt_file.dict, lang.dict )
  print "Loading commands"
  cm_class = ecu_commands       ( Commands,        mdoc, opt_file.dict, lang.dict )
  print "Loading mnemonics"
  mm_class = ecu_mnemonics      ( Mnemonics,       mdoc, opt_file.dict, lang.dict )
  
  #for p in Parameters.values():
  #  print p
  #for s in States.values():
  #  print s
  #for m in Mnemonics.values():
  #  print m
  
  if len(sys.argv)==3:
    print 
    print "Defaults"
    print 
    for i in sorted(Defaults.keys()):
      print pyren_encode( Defaults[i].name+"["+i+"] "+Defaults[i].label )
  
    print 
    print "Parameters"
    print 
    for i in sorted(Parameters.keys()):
      print pyren_encode( Parameters[i].codeMR+"["+i+"] "+Parameters[i].label )
  
    print 
    print "States"
    print 
    for i in sorted(States.keys()):
      print pyren_encode( States[i].codeMR+"["+i+"] "+States[i].label )
  
    print 
    print "Identifications"
    print 
    for i in sorted(Identifications.keys()):
      print pyren_encode( Identifications[i].codeMR+"["+i+"] "+Identifications[i].label )
  
    print 
    print "Commands"
    print 
    for i in sorted(Commands.keys()):
      print pyren_encode( Commands[i].codeMR+"["+i+"] "+Commands[i].label )
      
    sys.exit(0)
    
  if len(sys.argv)>3 and sys.argv[3].upper()!='TORQ':
    sys.exit(0)
    
  family = sys.argv[1][:2]
  eindex = sys.argv[1][2:] 
  if len(candst)>1: 
    sss = snat[F2A[family]]
    ddd = dnat[F2A[family]]
    filename  = "PR_"+ddd+"_"+sss+"_"+eindex+"_"+sys.argv[2]+".csv"
  else:
    sss = '82'+F2A[family]+'F1'
    ddd = '82'+F2A[family]+'F1'
    filename  = "PR_"+F2A[family]+"_"+eindex+"_"+sys.argv[2]+".csv"
  	  
  if mod_globals.os=='android' and os.path.exists('/sdcard/.torque/extendedpids'):
    filename = '/sdcard/.torque/extendedpids/'+filename

  cf = open( filename, "w")
     
  line = "%s,%s,%s,%s,%s,%s,%s,%s\n"%("name","ShortName","ModeAndPID","Equation","Min Value","Max Value","Units","Header")
  cf.write( line )
  
  memIt = []
  for i in sorted(Parameters.keys()):
    
    if Parameters[i].codeMR in memIt:
      continue
    else:
      memIt.append(Parameters[i].codeMR)
      
    m = Parameters[i].mnemolist[0]
    
    if len(Parameters[i].mnemolist)!=1:
      continue
    if '?' in Parameters[i].computation: 
      if len(sys.argv)==5 and sys.argv[4].upper()=='NOCHK':
        pass
      else:
        continue
    if Mnemonics[m].bitsLength=='':
      continue
    if Mnemonics[m].startBit=='':
      continue
    if Mnemonics[m].startByte=='':
      continue
      
    equ = gen_equ( Mnemonics[m] )   

    c_name = Parameters[i].label.replace(',','.')
    c_short = Parameters[i].codeMR
    c_pid = Mnemonics[m].request
    c_equ = Parameters[i].computation.replace( m, equ )
    c_min = Parameters[i].min
    c_max = Parameters[i].max
    c_unit = Parameters[i].unit
    
    line = '"PR_%s","%s","%s","%s","%s","%s","%s","%s"\n'%(c_name,c_short,c_pid,c_equ,c_min,c_max,c_unit,ddd)
    cf.write( line.encode('utf-8') )

  memIt = []
  for i in sorted(States.keys()):

    if States[i].codeMR in memIt:
      continue
    else:
      memIt.append(States[i].codeMR)
      
    m = States[i].mnemolist[0]
    
    if len(States[i].mnemolist)!=1:
      continue
    if Mnemonics[m].bitsLength=='':
      continue
    if Mnemonics[m].startBit=='':
      continue
    if Mnemonics[m].startByte=='':
      continue
    
    equ = gen_equ( Mnemonics[m] )   

    c_name = States[i].label.replace(',','.')
    c_short = States[i].codeMR
    c_pid = Mnemonics[m].request
    if len(sys.argv)==5 and sys.argv[4].upper()=='NOCHK':
      c_equ = States[i].computation.replace( m, equ )
    else:
      c_equ = equ
    c_min = '0'
    c_max = '0'
    c_unit = ''
    
    line = '"ST_%s","%s","%s","%s","%s","%s","%s","%s"\n'%(c_name,c_short,c_pid,c_equ,c_min,c_max,c_unit,ddd)
    cf.write( line.encode('utf-8') )

  cf.close()
  
  print
  print "File:", filename, "created"
  print 

  # fastinit, slowinit, protocol, candst
  can250init =  "ATAL\\nATSH"+ddd+"\\nATCRA"+sss+"\\nATFCSH"+ddd+"\\nATFCSD300000\\nATFCSM1\\nATSP8\\n"+startDiagReq
  can500init =  "ATAL\\nATSH"+ddd+"\\nATCRA"+sss+"\\nATFCSH"+ddd+"\\nATFCSD300000\\nATFCSM1\\nATSP6\\n"+startDiagReq
  slow05init   =  "ATSH81"+F2A[family]+"F1\\nATSW96\\nATIB10\\nATSP4\\nATSI\\n"+startDiagReq
  fast10init   =  "ATSH81"+F2A[family]+"F1\\nATSW96\\nATIB10\\nATSP5\\nATFI\\n"+startDiagReq

  if len(candst)>1:
    print "Init string for CAN 500:"
    print can500init
    print
    print "Init string for CAN 250:"
    print can250init
    print
  if len(fastinit)>1:
    print "Init string for Engine K-line (FAST INIT):"
    print fast10init
    print
  if len(slowinit)>1:
    print "Init string for Engine K-line (SLOW INIT):"
    print slow05init
    print
    
  # make profile for torque  
  profilename = str(int(time.time()))+'.tdv'
  if mod_globals.os=='android' and os.path.exists('/sdcard/.torque/vehicles'):
    profilename = '/sdcard/.torque/vehicles/'+str(int(time.time()))+'.tdv'
  
  prn = open( profilename, "w")
  prn.write( '#This is an ECU profile generated by pyren\n'.encode('utf-8') )
  prn.write( 'fuelType=0\n'.encode('utf-8') )
  prn.write( 'obdAdjustNew=1.0\n'.encode('utf-8') )
  prn.write( 'lastMPG=0.0\n'.encode('utf-8') )
  prn.write( 'tankCapacity=295.5\n'.encode('utf-8') )
  prn.write( 'volumetricEfficiency=85.0\n'.encode('utf-8') )
  prn.write( 'weight=1400.0\n'.encode('utf-8') )
  prn.write( 'odoMeter=0.0\n'.encode('utf-8') )
  prn.write( 'adapterName=OBDII [00\:00\:00\:00\:00\:0]\n'.encode('utf-8') )
  prn.write( 'adapter=00\:00\:00\:00\:00\:00\n'.encode('utf-8') )
  prn.write( 'boostAdjust=0.0\n'.encode('utf-8') )
  prn.write( 'mpgAdjust=1.0\n'.encode('utf-8') )
  prn.write( 'fuelCost=0.18000000715255737\n'.encode('utf-8') )
  prn.write( 'ownProfile=false\n'.encode('utf-8') )
  prn.write( 'displacement=1.6\n'.encode('utf-8') )
  prn.write( 'tankUsed=147.75\n'.encode('utf-8') )
  prn.write( 'lastMPGCount=0\n'.encode('utf-8') )
  prn.write( 'maxRpm=7000\n'.encode('utf-8') )
  prn.write( 'fuelDistance=0.0\n'.encode('utf-8') )
  prn.write( 'fuelUsed=0.0\n'.encode('utf-8') )
  prn.write( 'alternateHeader=true\n'.encode('utf-8') )
  prn.write( ('name=PR_'+ecuid+'\n').encode('utf-8') )
  if len(candst)>1:
    prn.write( ('customInit='+can500init.replace('\\','\\\\')+'\n').encode('utf-8') )
    prn.write( 'preferredProtocol=7\n'.encode('utf-8') )
  elif len(fastinit)>1:
    prn.write( ('customInit='+fast10init.replace('\\','\\\\')+'\n').encode('utf-8') )
    prn.write( 'preferredProtocol=6\n'.encode('utf-8') )
  else:
    prn.write( ('customInit='+slow05init.replace('\\','\\\\')+'\n').encode('utf-8') )
    prn.write( 'preferredProtocol=5\n'.encode('utf-8') )
  prn.close()

  print
  print "Torque profile:", profilename, "created"
  print 
  
if __name__ == "__main__":
  main()  
  
