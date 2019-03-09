#!/usr/bin/env python

opt_port      = ""
opt_ecuid     = ""
opt_ecuAddr   = ""
opt_protocol  = ""
opt_speed     = 38400
opt_rate      = 38400
opt_lang      = ""
opt_car       = ""
opt_log       = ""
opt_demo      = False
opt_scan      = False
opt_csv       = False
opt_csv_only  = False
opt_csv_human = False
opt_usrkey    = ""
opt_verbose   = False
opt_cmd       = False
opt_ddt       = False
opt_si        = False    #try slow init every time
opt_cfc0      = False    #turn off automatic FC and do it by script 
opt_n1c       = False    #turn off L1 cache
opt_dev       = False    #switch to development session for commands from DevList
opt_devses    = '1086'   #development session for commands from DevList
opt_exp       = False    #allow to use buttons in ddt
opt_dump      = False    #dump responces from all 21xx and 22xxxx requests
opt_can2      = False    #can connected to pins 13 and 12
opt_ddtxml    = ""

dumpName = ""

state_scan    = False

currentDDTscreen = None

ext_cur_DTC = "000000"

none_val = 'None'

mtcdir = '../MTCSAVE/VIN'

ddtroot = '..'  # parent folder for backward compatibility. for 9n and up use ../DDT2000data

os = ""

language_dict = {}

