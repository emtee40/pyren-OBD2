#!/usr/bin/env python
""" 
Extract database from installation CD
"""
import os
import sys
import os.path
import shutil
from subprocess import call
import zipfile

posix = False
if os.name == 'posix':
  posix = True
  print "Please install 'wine' package first to be able to use a i12comp.exe"
  print "'sudo apt install wine'"
  print

'''Check files'''
if not os.path.exists('./i12comp.exe') or not os.path.exists('./data2.cab') or not os.path.exists('./data1.hdr'):

  print  "######################################################"
  print  "#                                                    #"
  print  "#  First place me and i12comp.exe in one folder with #"
  print  "#  data2.cab and data1.hdr like in example below.    #"
  print  "#  Then run me again and I extract them for you      #"
  print  "#                                                    #"
  print  "#    <DIR>          ..                               #"
  print  "#    <DIR>          pyren                            #"
  print  "#    <DIR>          .                                #"
  print  "#             1,190 extrdata.bat                     #"
  print  "#           135,168 i12comp.exe                      #"
  print  "#     1,009,293,010 data2.cab                        #"
  print  "#         2,989,301 data1.hdr                        #"
  print  "#                                                    #"
  print  "######################################################"

 
''' call extract tool  '''
print "Unpacking files. It may take some minutes"
absolutePath = sys.argv[0].split("\\")[:-1]
if not absolutePath:
  absolutePath = sys.argv[0].split("/")[:-1]
  
clipImageDir =  "/".join(absolutePath) + '/'
if len(clipImageDir) == 1:
  clipImageDir = '.' + clipImageDir

filesToExtract = ['DiagOnCa*', '*.xml', '*.bqm', '*.dat', '*.zip']
  
if posix:
  for f in filesToExtract:
    call(('wine ' + clipImageDir + 'i12comp.exe x -o -d -f ' + clipImageDir +'data2.cab ' + f).split(' '))
else:
  for f in filesToExtract:
    call((clipImageDir + 'i12comp.exe x -o -d -f ' + clipImageDir +'data2.cab ' + f).split(' ')) 

for root, dirs, files in os.walk("[Applicatif BORNEO_CLIP]NS_NSR_PL_1___[TARGETDIR]/CLIP/Data/GenAppli"):
  targ = root.replace("[Applicatif BORNEO_CLIP]NS_NSR_PL_1___[TARGETDIR]/CLIP/Data/GenAppli", clipImageDir)
  if   targ[-3:-1]=='__': targ=targ[:-3]
  elif targ[-4:-2]=='__': targ=targ[:-4]

  if len(targ)>0 and not os.path.exists(targ):
    os.makedirs(targ)  

  for fil in files:
    src = root+'/'+fil
    dst = targ+'/'+fil[:-4]+fil[-4:].lower()
    shutil.copyfile(src,dst)
    print dst

for root, dirs, files in os.walk("[MTC_CLIP_X91]NS_NSR_NPL_1___[TARGETDIR]__1"):
  targ = root.replace("[MTC_CLIP_X91]NS_NSR_NPL_1___[TARGETDIR]__1", clipImageDir)

  for fil in files:
    src = root+'/'+fil
    dst = targ+'/'+fil[:-4]+fil[-4:].lower()
    shutil.copyfile(src,dst)
    print dst

for root, dirs, files in os.walk("[MTC_CLIP_X91]NS_NSR_NPL_1___[TARGETDIR]"):
  targ = root.replace("[MTC_CLIP_X91]NS_NSR_NPL_1___[TARGETDIR]","./BVMEXTRACTION")
  print targ
  if   targ[-3:-1]=='__': targ=targ[:-3]
  elif targ[-4:-2]=='__': targ=targ[:-4]

  if len(targ)>0 and not os.path.exists(targ):
    os.makedirs(targ)  

  for fil in files:
    src = root+'/'+fil
    dst = targ+'/'+fil[:-4]+fil[-4:].lower()
    shutil.copyfile(src,dst)
    print dst

print "Extracting BVM"
zipfile.ZipFile(clipImageDir + "Archives/BvmConfig.zip").extractall(clipImageDir)
if os.path.exists(clipImageDir + 'BVMEXTRACTION'):
  if posix:
    os.system('rm -r {}BVMEXTRACTION'.format(clipImageDir))
  else:
    os.system('rmdir "{}BVMEXTRACTION" /S /Q'.format(clipImageDir))
shutil.move(clipImageDir + "BVM_CONFIG", clipImageDir + "BVMEXTRACTION")

dirsToDelete = [
  "[Applicatif BORNEO_CLIP_RSM]NS_NSR_PL_1___[TARGETDIR]",
  "[Applicatif BORNEO_CLIP_RSM]NS_NSR_PL_1___[TARGETDIR]",
  "[Applicatif BORNEO_CLIP_X91]NS_NSR_PL_2___[WINDIR]__1",
  "[Applicatif BORNEO_CLIP]NS_NSR_NPL_544___[TARGETDIR]",
  "[Applicatif BORNEO_CLIP_X91]NS_NSR_PL_1___[TARGETDIR]",
  "[CONFIG_AUTO_FCT_X91]NS_NSR_NPL_544___[TARGETDIR]",
  "[DocDiag_CLIP_X91]NS_NSR_PL_1___[TARGETDIR]__1",
  "[Update Agent]NS_NSR_PL_1___[TARGETDIR]",
  "[Applicatif BORNEO_CLIP]NS_NSR_PL_1___[TARGETDIR]",
  "[MTC_CLIP_X91]NS_NSR_NPL_1___[TARGETDIR]",
  "[MTC_CLIP_X91]NS_NSR_NPL_1___[TARGETDIR]__1",
  "BL"
]

print "Deliting unused files"
if posix:
  for directory in dirsToDelete:
    os.system('rm -r "' + directory + '"')
else: 
  for directory in dirsToDelete:
    os.system('rmdir "' + directory + '" /S /Q')

print "Done" 

