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
    
	kb = KBHit()
	
	mainText = get_message('TexteTitre')
	important = get_message('TexteConsigne')
	tilt = get_message('TexteValeurInclinaison')
	degreeSymbol = get_message('TexteDegre')
	value2, datastr2 = ecu.get_pr(ScmParam['ParametreInclinaison'])

	clearScreen()
	print pyren_encode(header)
	print mainText
	print '*'*80
	print
	print important
	print

	ch = raw_input('Do you want to continue? <yes/no> ')
	while (ch.upper() != 'YES') and (ch.upper()!= 'NO'):
		ch = raw_input('Do you want to continue? <yes/no> ')
	if ch.upper() != 'YES':
		return
	
	clearScreen()
	cmd = ecu.get_ref_cmd(get_message('Commande1'))
	resVal = ScmParam['ParametreCommande1']
	print '*'*80
	responce = ecu.run_cmd(ScmParam['Commande1'], resVal)
	print '*'*80
	if 'NR' in responce:
		print get_message('TexteProcedureInterompue')
	else:
		print get_message('TexteInitialisationEffectuee')
	print
	print tilt, pyren_encode(':'), value2, degreeSymbol
	print

	ch = raw_input('Press ENTER to exit')
	return
