#!/usr/bin/env python

import os
import sys
import re
import time
import string
import mod_globals
import mod_utils
import mod_ecu
import mod_db_manager
from mod_utils import clearScreen
from mod_utils import pyren_encode
from mod_utils import KBHit
import mod_ecu_mnemonic
import xml.dom.minidom

def run( elm, ecu, command, data ):

	clearScreen()
	header =  '['+command.codeMR+'] '+command.label
  
	ScmSet   = {}
	ScmParam = {}

	def get_message( msg ):
		if msg in ScmParam.keys():
			value = ScmParam[msg]
		else:
			value = msg
		if value.isdigit() and value in mod_globals.language_dict.keys():
			value = pyren_encode( mod_globals.language_dict[value] )
		return value

	def get_message_by_id( id ):
		if id.isdigit() and id in mod_globals.language_dict.keys():
			value = pyren_encode( mod_globals.language_dict[id] )
		return value


	DOMTree = xml.dom.minidom.parse(mod_db_manager.get_file_from_clip(data))
	ScmRoom = DOMTree.documentElement
  
	ScmParams = ScmRoom.getElementsByTagName("ScmParam")
	
	for Param in ScmParams:
		name  = pyren_encode( Param.getAttribute("name")  )
		value = pyren_encode( Param.getAttribute("value") )
        
		ScmParam[name] = value

	ScmSets = ScmRoom.getElementsByTagName("ScmSet")
 
	for Set in ScmSets:
		setname  = pyren_encode(Set.getAttribute("name"))
		ScmParams = Set.getElementsByTagName("ScmParam")
	
		for Param in ScmParams:
			name  = pyren_encode( Param.getAttribute("name")  )
			value = pyren_encode( Param.getAttribute("value") )
			
			ScmSet[setname]= value
			ScmParam[name] = value
    
	kb = KBHit()

	confirm = get_message_by_id('19800')
	title = get_message("Title")
	messageInfo = get_message("Message1")
	succesMessage = get_message("CommandFinished")
	failMessage = get_message("CommandImpossible")

	mnemonics = ecu.get_ref_id(ScmParam["default"]).mnemolist

	if mnemonics[0][-2:] > mnemonics[1][-2:]:
		mnemo1 = mnemonics[1]
		mnemo2 = mnemonics[0]
	else:
		mnemo1 = mnemonics[0]
		mnemo2 = mnemonics[1]
	
	byteFrom = int(mnemo1[-2:])
	byteTo = int(re.findall("\d+", mnemo2)[1])
	byteCount = byteTo - byteFrom - 1
	resetBytes = byteCount * "00"

	mnemo1Data = mod_ecu_mnemonic.get_mnemonic(ecu.Mnemonics[mnemo1], ecu.Services, elm, 1)
	mnemo2Data = mod_ecu_mnemonic.get_mnemonic(ecu.Mnemonics[mnemo2], ecu.Services, elm, 1)

	paramsToSend = mnemo1Data + resetBytes + mnemo2Data
	
	print title
	print '*'*80
	print messageInfo
	print '*'*80
	print
	ch = raw_input(confirm + ' <YES/NO>: ')
	while (ch.upper()!='YES') and (ch.upper()!='NO'):
		ch = raw_input(confirm + ' <YES/NO>: ')
	if ch.upper()!='YES':
		return
	
	clearScreen()

	print
	response = ecu.run_cmd(ScmParam['Cmde1'], paramsToSend)
	print

	if "NR" in response:
		print failMessage
	else:
		print succesMessage
	
	print
	ch = raw_input('Press ENTER to exit')
	return
