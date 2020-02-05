#!/usr/bin/env python

import os
import sys
import re
import time
import string
import mod_globals
import mod_utils
import mod_ecu
from mod_utils import clearScreen
from mod_utils import pyren_encode
from mod_utils import KBHit
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


	DOMTree = xml.dom.minidom.parse(data)
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

	paramsToSend = ""
	
	identList = ['ID101', 'ID102', 'ID103', 'ID125', 'ID126', 'ID105', 'ID106', 'ID107', 'ID108', 'ID109', 'ID110', 'ID111', 'ID112', 'ID113', 'ID114', 'ID115', 'ID116', 'ID117', 'ID118', 'ID119', 'ID120', 'ID121', '00000000', 'ID123', 'ID124', 'ID186', 'ID187']
	
	for ident in identList:
		if ident.startswith("ID"):
			paramsToSend += ecu.get_id(ident, 1)
		else:
			paramsToSend += ident
	
	ch = raw_input('Do you want to continue? <yes/no> ')
	while (ch.upper() != 'YES') and (ch.upper()!= 'NO'):
		ch = raw_input('Do you want to continue? <yes/no> ')
	if ch.upper() != 'YES':
		return

	responce = ecu.run_cmd(ScmParam['Cmde1'], paramsToSend)

	print
	ch = raw_input('Press ENTER to exit')
	return
