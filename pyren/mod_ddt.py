#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import operator
import ast
import gc
import time

import mod_ddt_utils
import mod_utils
import mod_db_manager

from shutil import copyfile


os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

import mod_globals
import mod_scan_ecus
import mod_ddt_ecu
import mod_elm

try:
    # Python2
    import Tkinter as tk
    import ttk
    import tkFont
    import tkMessageBox
    import tkFileDialog
    import tkSimpleDialog

except ImportError:
    # Python3
    import tkinter as tk
    import tkinter.ttk as ttk
    import tkFont
    import tkMessageBox
    import tkFileDialog

from mod_ddt_ecu import DDTECU
from mod_ddt_screen import DDTScreen

import xml.etree.ElementTree as et

from xml.dom.minidom import parse
import xml.dom.minidom

mod_globals.os = os.name

if mod_globals.os == 'nt':
    import pip

    try:
        import serial
    except ImportError:
        pip.main(['install', 'pyserial'])

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
        from serial.tools import list_ports
        # import ply
    except ImportError:
        print "\n\n\n\tPleas install additional modules"
        print "\t\t>sudo easy_install pyserial"
        sys.exit()

from mod_elm import ELM
from mod_optfile import *
from mod_utils import *


class DDT():
    decu = None  # ddt ecu
    cecu = None  # chosen ecu

    def __init__(self, elm, cecu, langmap={}):
        self.elm = elm
        self.cecu = cecu

        clearScreen()
        print "Starting DDT process"

        # make or load ddt ecu
        decucashfile = "./cache/ddt_" + cecu['ModelId'] + ".p"

        if os.path.isfile(decucashfile) and mod_globals.opt_ddtxml == '':  # if cache exists and no xml defined
            self.decu = pickle.load(open(decucashfile, "rb"))  # load it
        else:  # else
            self.decu = DDTECU(self.cecu)  # init class
            self.decu.setELM(self.elm)  # define ELM for it
            self.decu.scanECU()  # scan and loading original data for chosen ECU
            self.decu.setELM(None)  # clear elm before serialization
            if len(self.decu.ecufname) > 0:
                pickle.dump(self.decu, open(decucashfile, "wb"))  # and save cache

        self.decu.setELM(self.elm)  # re-define ELM
        self.decu.setLangMap(langmap)

        if len(self.decu.ecufname) == 0:
            return

        if '/' in self.decu.ecufname:
            xfn = self.decu.ecufname[:-4].split('/')[-1]
        else:
            xfn = self.decu.ecufname[:-4].split('\\')[-1]

        dumpIs = False
        for root, dirs, files in os.walk("./dumps"):
            for f in files:
                if (xfn + '.') in f:
                    dumpIs = True
                    break

        if not mod_globals.opt_demo and not dumpIs and not mod_globals.opt_dump:
            answer = raw_input('Save dump ? [y/n] : ')
            if 'N' in answer.upper():
                dumpIs = True

        if mod_globals.opt_demo:
            print "Loading dump"
            self.decu.loadDump()
        elif mod_globals.opt_dump or not dumpIs:
            print "Saving dump"
            self.decu.saveDump()

        # Load XML
        if not self.decu.ecufname.startswith(mod_globals.ddtroot):
            tmp_f_name = self.decu.ecufname.split('/')[-1]
            self.decu.ecufname = 'ecus/'+tmp_f_name

        if not mod_db_manager.file_in_ddt(self.decu.ecufname):
            print "No such file: ", self.decu.ecufname
            return None

        ns = {'ns0': 'http://www-diag.renault.com/2002/ECU',
              'ns1': 'http://www-diag.renault.com/2002/screens'}

        tree = et.parse(mod_db_manager.get_file_from_ddt(self.decu.ecufname))
        xdoc = tree.getroot()

        # Show screen
        print "Show screen"
        scr = DDTScreen(self.decu.ecufname, xdoc, self.decu)

        del scr
        del self.decu

    def __del__(self):
        # debug
        # print sys.getrefcount(self.elm)
        del self.elm
        del self.cecu


def optParser():
    '''Parsing of command line parameters. User should define at least com port name'''
    '''Not used in current version'''

    import argparse

    parser = argparse.ArgumentParser(
        # usage = "%prog -p <port> [options]",
        version="mod_ddt Version 0.9.q",
        description="mod_ddt - python program for diagnostic Renault cars"
    )

    parser.add_argument('-p',
                        help="ELM327 com port name",
                        dest="port",
                        default="")

    parser.add_argument("-r",
                        help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
                        dest="rate",
                        default="38400", )

    parser.add_argument("-a",
                        help="functional address of ecu",
                        dest="ecuAddr",
                        default="")

    parser.add_argument("-i",
                        help="interface protocol [can250|250|can500|500|kwpS|S|kwpF|F]",
                        dest="protocol",
                        default='500')

    parser.add_argument("-L",
                        help="language option {RU[default],GB,FR,IT,...}",
                        dest="lang",
                        default="RU")

    parser.add_argument("--cfc",
                        help="turn off automatic FC and do it by script",
                        dest="cfc",
                        default=False,
                        action="store_true")

    parser.add_argument("--n1c",
                        help="turn off L1 cache",
                        dest="n1c",
                        default=False,
                        action="store_true")

    parser.add_argument("--log",
                        help="log file name",
                        dest="logfile",
                        default="")

    parser.add_argument("--xml",
                        help="xml file name",
                        dest="ddtxml",
                        default="")

    parser.add_argument("--demo",
                        help="for debuging purpose. Work without car and ELM",
                        dest="demo",
                        default=False,
                        action="store_true")

    parser.add_argument("--dump",
                        help="dump responces from all 21xx and 22xxxx requests",
                        dest="dump",
                        default=True,
                        action="store_true")

    parser.add_argument("--exp",
                        help="swith to Expert mode (allow to use buttons in DDT)",
                        dest="exp",
                        default=False,
                        action="store_true")

    options = parser.parse_args()

    if not options.port and mod_globals.os != 'android':
        parser.print_help()
        iterator = sorted(list(list_ports.comports()))
        print ""
        print "Available COM ports:"
        for port, desc, hwid in iterator:
            print "%-30s \n\tdesc: %s \n\thwid: %s" % (port, desc.decode("windows-1251"), hwid)
        print ""
        exit(2)
    else:
        mod_globals.opt_port = options.port
        mod_globals.opt_ecuAddr = options.ecuAddr.upper()
        mod_globals.opt_rate = int(options.rate)
        mod_globals.opt_lang = options.lang
        mod_globals.opt_log = options.logfile
        mod_globals.opt_demo = options.demo
        mod_globals.opt_dump = options.dump
        mod_globals.opt_exp = options.exp
        mod_globals.opt_cfc0 = options.cfc
        mod_globals.opt_n1c = options.n1c
        mod_globals.opt_ddtxml = options.ddtxml
        if 'S' in options.protocol.upper():
            mod_globals.opt_protocol = 'S'
        elif 'F' in options.protocol.upper():
            mod_globals.opt_protocol = 'F'
        elif '250' in options.protocol:
            mod_globals.opt_protocol = '250'
        elif '500' in options.protocol:
            mod_globals.opt_protocol = '500'
        else:
            mod_globals.opt_protocol = '500'

class DDTLauncher():
    def __init__(self):

        self.eculist = mod_ddt_utils.loadECUlist()
        self.carecus = []

        self.root = tk.Tk()
        self.root.title("mod_ddt Launcher")
        self.style = ttk.Style ()
        self.style.theme_use ('classic')

        self.var_dump = tk.BooleanVar()
        self.var_log = tk.BooleanVar()
        self.var_cfc = tk.BooleanVar()
        self.var_can2 = tk.BooleanVar()

        self.var_portList = []
        self.var_speedList = []

        self.var_port = tk.StringVar()
        self.var_speed = tk.StringVar()

        self.var_logName = tk.StringVar()

        self.elm = None
        self.save = mod_ddt_utils.settings()
        self.loadSettings()

        self.currentEcu = None
        self.v_xmlList = []
        self.v_dumpList = []

        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1, minsize=300)
        self.root.columnconfigure(1) # not stretchable
        self.root.columnconfigure(2, weight=3, minsize=300)

        optsGrid = {'ipadx': 0, 'ipady': 0, 'sticky': 'nswe'}
        optsGrid_w = {'ipadx': 0, 'ipady': 0, 'sticky': 'w'}
        optsGrid_e = {'ipadx': 0, 'ipady': 0, 'sticky': 'e'}
        btn_style = { 'activebackground':"#d9d9d9",
                      'activeforeground':"#000000",
                      'background':"#d9d9d9",
                      'foreground':"#000000",
                      'highlightbackground':"#d9d9d9"}

        ent_style = { 'background':"#FFFFFF",
                      'foreground':"#000000",
                      'highlightbackground':"#d9d9d9"}

        self.tf = tk.Frame(self.root)
        self.tf.grid(row=0, column=0, **optsGrid )

        self.tf.rowconfigure(0)  # not stretchable
        self.tf.rowconfigure(1, weight=1)
        self.tf.columnconfigure(0, weight=1)
        self.tf.columnconfigure(1)

        self.filterText = tk.StringVar()
        self.filtentry = tk.Entry(self.tf, textvariable=self.filterText, **ent_style)
        self.filtentry.bind('<Return>', self.fltBtnClick)
        self.filtentry.grid(row=0, column=0, **optsGrid)

        self.filtbutton = tk.Button(self.tf, text="Filter", command=self.fltBtnClick, **btn_style)
        self.filtbutton.grid(row=0, column=1, **optsGrid)

        self.ptree = ttk.Treeview(self.tf, columns = ['name','segment'], height=10)
        self.ptree.grid(row=1, column=0, columnspan = 2, **optsGrid)

        self.vsb = ttk.Scrollbar(self.root, orient="vertical", command=self.ptree.yview)
        self.vsb.grid(row=0, column=1, **optsGrid)
        self.ptree.configure(yscrollcommand=self.vsb.set)

        #self.ptree.bind('<Double-1>', self.OnDoubleClick)
        self.ptree.bind('<ButtonRelease-1>', self.CarDoubleClick)


        self.ptree.heading('#0', text='Project')
        self.ptree.heading('name', text='Name', anchor='center')
        self.ptree.heading('segment', text='Segm', anchor='e')
        self.ptree.column('#0', minwidth=100, width=100, stretch=False)
        self.ptree.column('#1', minwidth=150, width=150, stretch=True)
        self.ptree.column('#2', minwidth=50, width=50, stretch=False)

        self.mf = tk.Frame(self.root, background="#d9d9d9")
        self.mf.grid(row=0, column=2, **optsGrid)

        self.mf.rowconfigure(0)
        self.mf.rowconfigure(1)
        self.mf.rowconfigure(2)
        self.mf.rowconfigure(3)
        self.mf.rowconfigure(4)
        self.mf.rowconfigure(5)
        self.mf.rowconfigure(6, weight = 1)
        self.mf.rowconfigure(7)
        self.mf.rowconfigure(8)
        self.mf.columnconfigure(0, weight = 1)
        self.mf.columnconfigure(1, weight = 1)
        self.mf.columnconfigure(2, weight = 1)
        self.mf.columnconfigure(3, weight = 1)


        self.l_db = tk.Label(self.mf, text='DB root:', background="#d9d9d9")
        self.l_db.grid(row=0, column=0, **optsGrid_e)
        self.l_db2 = tk.Label(self.mf, text=mod_globals.ddtroot, background="#d9d9d9")
        self.l_db2.grid(row=0, column=1, **optsGrid_w)

        self.l_pr = tk.Label(self.mf, text='Project:', background="#d9d9d9")
        self.l_pr.grid(row=1, column=0, **optsGrid_e)
        self.v_proj = tk.StringVar()
        self.v_proj.set("")
        self.e_proj = tk.Label(self.mf, textvariable=self.v_proj, background="#d9d9d9")
        #self.e_proj.config(state=tk.DISABLED)
        self.e_proj.grid(row=1, column=1, **optsGrid_w)

        self.l_af = tk.Label(self.mf, text='Addressing:', background="#d9d9d9")
        self.l_af.grid(row=2, column=0, **optsGrid_e)
        self.v_addr = tk.StringVar()
        self.v_addr.set("")
        self.e_addr = tk.Label(self.mf, textvariable=self.v_addr, background="#d9d9d9")
        #self.e_addr.config(state=tk.DISABLED)
        self.e_addr.grid(row=2, column=1, **optsGrid_w)

        self.l_pcan = tk.Label(self.mf, text='Primary CAN:', background="#d9d9d9")
        self.l_pcan.grid(row=3, column=0, **optsGrid_e)
        self.v_pcan = tk.StringVar()
        self.v_pcan.set("")
        self.e_pcan = tk.Label(self.mf, textvariable=self.v_pcan, background="#d9d9d9")
        #self.e_pcan.config(state=tk.DISABLED)
        self.e_pcan.grid(row=3, column=1, **optsGrid_w)

        self.l_mcan = tk.Label(self.mf, text='Secondary CAN:', background="#d9d9d9")
        self.l_mcan.grid(row=4, column=0, **optsGrid_e)
        self.v_mcan = tk.StringVar()
        self.v_mcan.set("")
        self.e_mcan = tk.Label(self.mf, textvariable=self.v_mcan, background="#d9d9d9")
        #self.e_mcan.config(state=tk.DISABLED)
        self.e_mcan.grid(row=4, column=1, **optsGrid_w)

        self.l_vi = tk.Label(self.mf, text='VIN or car name:', background="#d9d9d9")
        self.l_vi.grid(row=5, column=0, **optsGrid_e)
        self.v_vin = tk.StringVar()
        self.v_vin.set("")
        self.e_vin = tk.Entry(self.mf, textvariable=self.v_vin, **ent_style)
        self.e_vin.grid(row=5, column=1, columnspan=3, **optsGrid)

        ####################################################################################
        self.set_fr = tk.LabelFrame(self.mf, text="Settings", padx=5, background="#d9d9d9")
        self.set_fr.grid(row=0, rowspan=5, column=2, columnspan=4, **optsGrid)

        self.set_fr.rowconfigure(0)
        self.set_fr.rowconfigure(1)
        self.set_fr.rowconfigure(2)
        self.set_fr.columnconfigure(0, weight=1)
        self.set_fr.columnconfigure(1, weight=1)
        self.set_fr.columnconfigure(2, weight=1)

        self.port_lbl = tk.Label(self.set_fr, text='ELM:', background="#d9d9d9")
        self.port_lbl.grid(row=0, column=0, **optsGrid_e)

        self.portList = ttk.Combobox(self.set_fr)
        self.portList.grid(row=0, column=1, **optsGrid)
        self.portList.configure(values=self.var_portList)
        self.portList.configure(textvariable=self.var_port)
        self.portList.configure(takefocus="")

        self.speedList = ttk.Combobox(self.set_fr, width=6)
        self.speedList.grid(row=0, column=2, **optsGrid_w)
        self.speedList.configure(values=self.var_speedList)
        self.speedList.configure(textvariable=self.var_speed)
        self.speedList.configure(takefocus="")

        self.log_lbl = tk.Label(self.set_fr, text='Log:', background="#d9d9d9")
        self.log_lbl.grid(row=1, column=0, **optsGrid_e)

        self.logName = tk.Entry(self.set_fr, textvariable=self.var_logName, **ent_style)
        self.logName.grid(row=1, column=1, **optsGrid)

        self.logChk = tk.Checkbutton(self.set_fr, variable=self.var_log, background="#d9d9d9")
        self.logChk.grid(row=1, column=2, **optsGrid_w)

        self.dump_lbl = tk.Label(self.set_fr, text='Dump:', background="#d9d9d9")
        self.dump_lbl.grid(row=2, column=0, **optsGrid_e)

        self.dumpChk = tk.Checkbutton(self.set_fr, variable=self.var_dump, background="#d9d9d9")
        self.dumpChk.grid(row=2, column=1, **optsGrid_w)

        self.can2_lbl = tk.Label(self.set_fr, text='CAN2:', background="#d9d9d9")
        self.can2_lbl.grid(row=2, column=1, **optsGrid_e)

        self.can2Chk = tk.Checkbutton(self.set_fr, variable=self.var_can2, background="#d9d9d9")
        self.can2Chk.grid(row=2, column=2, **optsGrid_w)
        ####################################################################################

        self.btn_connect = tk.Button(self.mf, text="Connect selected ECU (ON-line)", command=self.ConnectBtnClick, **btn_style)
        self.btn_connect.grid(row=6, column=0, columnspan=2, **optsGrid)

        self.btn_connect = tk.Button(self.mf, text="Show selected ECU (OFF-line)", command=self.DemoBtnClick, **btn_style)
        self.btn_connect.grid(row=6, column=3, **optsGrid)

        self.btn_scan_all_car = tk.Button(self.mf, text="Scan all ECUs", command=self.ScanAllBtnClick, **btn_style)
        self.btn_scan_all_car.grid(row=7, column=0, **optsGrid)

        self.btn_scan_car = tk.Button(self.mf, text="Scan selected ECU", command=self.ScanSelectedBtnClick, **btn_style)
        self.btn_scan_car.grid(row=7, column=1, **optsGrid)

        self.btn_load_car = tk.Button(self.mf, text="Load car", command=self.LoadBtnClick, **btn_style)
        self.btn_load_car.grid(row=7, column=2, **optsGrid)

        self.btn_save_car = tk.Button(self.mf, text="Save car", command=self.SaveBtnClick, **btn_style)
        self.btn_save_car.grid(row=7, column=3, **optsGrid)

        self.progress = ttk.Progressbar(self.mf, mode="determinate")
        self.progress.grid(row=8, column=0, columnspan=4, **optsGrid)

        self.df = tk.Frame(self.root, background='#d9d9d9')
        self.df.grid(row=1, column=0, columnspan=3, **optsGrid )

        self.df.rowconfigure(0)  # not stretchable
        self.df.columnconfigure(0, weight=1)
        self.df.columnconfigure(1)

        self.ecutree = ttk.Treeview(self.df, columns = ['ISO8','XId','RId','Prot','Type','Name','XML','dump'], height=20)
        self.ecutree.grid(row=0, column=0, **optsGrid)

        self.vsb1 = ttk.Scrollbar(self.df, orient="vertical", command=self.ecutree.yview)
        self.vsb1.grid(row=0, column=1, **optsGrid)
        self.ecutree.configure(yscrollcommand=self.vsb1.set)

        self.ecutree.bind('<ButtonRelease-2>', self.EcuDoubleClick)
        self.ecutree.bind('<Double-Button-1>', self.EcuDoubleClick)

        self.ecutree.heading('#0', text='Addr')
        self.ecutree.heading('#1', text='ISO8')
        self.ecutree.heading('#2', text='XId')
        self.ecutree.heading('#3', text='RId')
        self.ecutree.heading('#4', text='Protocol')
        self.ecutree.heading('#5', text='Type')
        self.ecutree.heading('#6', text='Name')
        self.ecutree.heading('#7', text='XML')
        self.ecutree.heading('#8', text='dump')
        self.ecutree.column('#0', minwidth=40, width=40, stretch=False)
        self.ecutree.column('#1', minwidth=40, width=40, stretch=False)
        self.ecutree.column('#2', minwidth=40, width=40, stretch=False)
        self.ecutree.column('#3', minwidth=40, width=40, stretch=False)
        self.ecutree.column('#4', minwidth=80, width=80, stretch=False)
        self.ecutree.column('#5', minwidth=100, width=100, stretch=False)
        self.ecutree.column('#6', minwidth=150, width=150, stretch=False)
        self.ecutree.column('#7', minwidth=300, width=300, stretch=True)
        self.ecutree.column('#8', minwidth=150, width=150, stretch=True)

        self.pl = mod_ddt_utils.ddtProjects()
        self.fltBtnClick()  # show tree with apply clear filter

        self.LoadCarFile("./savedCAR_prev.csv")

        self.root.mainloop()

    def __del__(self):
        self.SaveBtnClick()
        self.saveSettings()

    def enableELM(self):

        # print self.elm
        if self.elm != None:
            try:
                self.elm.port.hdr.close()
                del(self.elm)
                self.elm = None
                gc.collect()
            except:
                pass

        self.applySettings()

        try:
            self.elm = ELM(mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log)
        except:
            result = tkMessageBox.askquestion("Warning", "ELM is not connected. Would you like to work OFF-line?", icon='warning')
            if result == 'yes':
                mod_globals.opt_demo = True
                self.elm = ELM(mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log)
            else:
                raise Exception('elm is not connected')
                return

        # change serial port baud rate
        if mod_globals.opt_speed < mod_globals.opt_rate and not mod_globals.opt_demo:
            self.elm.port.soft_boudrate(mod_globals.opt_rate)

    def LoadCarFile(self, filename):
        if not os.path.isfile(filename):
            return
        with open(filename, 'r') as fin:
            lines = fin.read().splitlines()
        fin.close()

        self.carecus = []
        for l in lines:
            l = l.strip()
            if len(l)==0 or l.startswith('#'):
                continue
            li = l.split(';')
            if li[0].lower()=='car':
                self.v_proj.set(li[1])
                self.v_addr.set(li[2])
                self.v_pcan.set(li[3])
                self.v_mcan.set(li[4])
                self.v_vin.set(li[5])
            else:
                ecu = {}
                ecu['undef'] = li[0]
                ecu['addr'] = li[1]
                ecu['iso8'] = li[2]
                ecu['xid'] = li[3]
                ecu['rid'] = li[4]
                ecu['prot'] = li[5]
                ecu['type'] = li[6]
                ecu['name'] = li[7]
                ecu['xml'] = li[8]
                ecu['dump'] = li[9]
                ecu['ses']  = li[10]
                self.carecus.append(ecu)

        self.renewEcuList()

    def LoadBtnClick(self):
        filename = tkFileDialog.askopenfilename(initialdir='./', title='Select file',
                                                filetypes=[('csv files', '*.csv')])
        self.LoadCarFile(filename)
        return

    def SaveBtnClick(self):
        filename = './savedCAR_'+self.v_vin.get()+'.csv'
        with open( filename, 'w') as fout:
            car = ['car',self.v_proj.get(), self.v_addr.get(), self.v_pcan.get(), self.v_mcan.get(), self.v_vin.get()]
            fout.write(';'.join(car)+'\n')
            for ecu in self.carecus:
                e = [ecu['undef'],
                     ecu['addr'],
                     ecu['iso8'],
                     ecu['xid'],
                     ecu['rid'],
                     ecu['prot'],
                     ecu['type'],
                     ecu['name'],
                     ecu['xml'],
                     ecu['dump'],
                     ecu['ses']]
                fout.write(unicode(';'.join(e)).encode("ascii", "ignore") + '\n')
        fout.close()

        copyfile(filename, "./savedCAR_prev.csv")

        return

    def setEcuAddress(self, ce, pro ):
        # define ecudata
        ecudata = {'idTx': ce['xid'],
                   'idRx': ce['rid'],
                   'slowInit': '',
                   'fastInit': '',
                   'ModelId': ce['addr'],
                   'ecuname': 'ddt_unknown',
                   }
        if pro == 'CAN':
            if ce['prot'] == 'CAN-250':
                ecudata['protocol'] = 'CAN_250'
                ecudata['brp'] = '01'
            else:
                ecudata['protocol'] = 'CAN_500'
                ecudata['brp'] = '0'

            ecudata['pin'] = 'can'
            self.elm.set_can_addr(ce['addr'], ecudata)

        if pro == 'KWP' or pro == 'ISO':
            if ce['prot'] == 'KWP-FAST':
                ecudata['protocol'] = 'KWP_Fast'
                ecudata['fastInit'] = ce['addr']
                ecudata['slowInit'] = ''
                mod_globals.opt_si = False
            elif ce['prot'] == 'ISO8' and ce['iso8'] != '':
                ecudata['protocol'] = 'KWP_Slow'
                ecudata['fastInit'] = ''
                ecudata['slowInit'] = ce['iso8']
                mod_globals.opt_si = True
            else:
                ecudata['protocol'] = 'KWP_Slow'
                ecudata['fastInit'] = ''
                ecudata['slowInit'] = ce['addr']
                mod_globals.opt_si = True

            ecudata['pin'] = 'iso'
            self.elm.set_iso_addr(ce['addr'], ecudata)

    def ScanAllBtnClick(self):

        # Enable ELM
        try:
            self.enableELM()
        except:
            return

        if self.elm==None or self.elm.port==0:
            tkMessageBox.showinfo("ERROR", "ELM is not connected. You may work only offline.")
            return


        # for all carecus find can ecus, then k-line ecus
        scansequence = ['CAN','KWP','ISO']
        vins = {}
        self.progress['maximum'] = len(self.carecus)+1
        progressValue = 1
        self.progress['value'] = progressValue
        for pro in scansequence:

            # init protocol
            if pro == 'CAN':
                self.elm.init_can()
            else:
                self.elm.init_iso()

            for ce in self.carecus:
                if pro in ce['prot'] or ce['prot']=='':

                    # set address
                    self.setEcuAddress(ce, pro)

                    progressValue = progressValue + 1
                    self.progress['value'] = progressValue
                    self.progress.update()

                    # get ID
                    (StartSession, DiagVersion, Supplier, Version, Soft, Std, VIN) = mod_scan_ecus.readECUIds(self.elm)

                    if DiagVersion=='' and DiagVersion=='' and Version=='' and Soft=='' and VIN=='':
                        continue

                    candlist = mod_ddt_ecu.ecuSearch(self.v_proj.get(), ce['addr'],
                                                     DiagVersion, Supplier, Soft, Version,
                                                     self.eculist, interactive = False)
                    ce['xml'] = candlist[0]
                    ce['ses'] = StartSession
                    ce['undef'] = '0'
                    tmp = self.getDumpListByXml(ce['xml'])
                    if len(tmp)>0:
                        ce['dump'] = tmp[-1]
                    else:
                        ce['dump'] = ''


                    # count most frequent VINs
                    if VIN!='':
                        if VIN not in vins.keys():
                            vins[VIN] = 1
                        else:
                            vins[VIN] = vins[VIN] + 1

                    self.renewEcuList()

        if self.v_vin.get()=='' and len(vins.keys()):
          self.v_vin.set(max(vins.iteritems(), key=operator.itemgetter(1))[0])

        self.progress['value'] = 0
        return

    def ScanSelectedBtnClick(self):
        # Enable ELM
        try:
            self.enableELM()
        except:
            return

        if self.elm==None or self.elm.port==0:
            tkMessageBox.showinfo("ERROR", "ELM is not connected. You may work only offline.")
            return

        try:
            item = self.ecutree.selection()[0]
            e = self.ecutree.item(item)['values'][8]
        except:
            pass

        ce = None
        for ce in self.carecus:
            if str(ce)==e:
                break

        self.currentEcu = self.carecus.index(ce)

        if ce==None:
            return

        #ce = self.getSelectedECU()

        # init protocol
        if 'CAN' in ce['prot'] and ce['xid']!='' and ce['rid']!='':
            pro = 'CAN'
        else:
            pro = 'KWP'

        if pro == 'CAN':
            self.elm.init_can()
        else:
            self.elm.init_iso()

        # set address
        self.setEcuAddress(ce, pro)

        # get ID
        (StartSession, DiagVersion, Supplier, Version, Soft, Std, VIN) = mod_scan_ecus.readECUIds(self.elm)

        if DiagVersion=='' and Supplier=='' and Version=='' and Soft=='':
            tkMessageBox.showinfo("INFO", "no response from this ECU")
            return

        candlist = mod_ddt_ecu.ecuSearch(self.v_proj.get(), ce['addr'],
                                         DiagVersion, Supplier, Soft, Version,
                                         self.eculist, interactive = False)
        ce['xml'] = candlist[0]
        ce['ses'] = StartSession
        ce['undef'] = '0'

        self.renewEcuList()

        return

    def ConnectBtnClick(self):
        ecu = self.getSelectedECU()
        if ecu==None or ecu['xml']=='':
            tkMessageBox.showinfo("INFO", "Selected ECU is undefined. Please scan it first.")
            return None

        mod_globals.opt_demo = False

        self.OpenECUScreens(ecu)

        return

    def getSelectedECU(self):
        try:
            item = self.ecutree.selection()[0]
            line = self.ecutree.item(item)['values']
        except:
            if len(self.ecutree.get_children(""))==0:
                tkMessageBox.showinfo("INFO", "Please select the project in the left list and then ECU in the bottom")
            else:
                tkMessageBox.showinfo("INFO", "Please select an ECU in the bottom list")
            return None

        ecu = ast.literal_eval(line[8])

        return ecu

    def OpenECUScreens(self, ce):

        decu = None

        # Enable ELM
        try:
            self.enableELM()
        except:
            return

        if not mod_globals.opt_demo and self.var_dump.get():
            mod_globals.opt_dump = True

        ce = self.getSelectedECU()

        # init protocol
        if 'CAN' in ce['prot'] and ce['xid']!='' and ce['rid']!='':
            pro = 'CAN'
        else:
            pro = 'KWP'

        #check elm timeout
        ct1 = time.time()

        if pro == 'CAN':
            self.elm.init_can()
        else:
            self.elm.init_iso()

        ct2 = time.time()

        if ct2-ct1 > 5:
            tkMessageBox.showinfo("ERROR", "ELM is not responding well.")
            return

        # set address
        self.setEcuAddress(ce, pro)

        self.elm.start_session(ce['ses'])

        # make or load ddt ecu
        decucashfile = "./cache/ddt_" + ce['xml'][:-4] + ".p"

        if os.path.isfile(decucashfile):  # if cache exists and no xml defined
            decu = pickle.load(open(decucashfile, "rb"))  # load it
        else:  # else
            decu = DDTECU(None)  # init class
            decu.loadXml('ecus/'+ce['xml'])
            if len(decu.ecufname) > 0:
                pickle.dump(decu, open(decucashfile, "wb"))  # and save cache

        decu.setELM(self.elm)  # re-define ELM

        if len(decu.ecufname) == 0:
            return

        if '/' in decu.ecufname:
            xfn = decu.ecufname[:-4].split('/')[-1]
        else:
            xfn = decu.ecufname[:-4].split('\\')[-1]

        dumpIs = False
        for root, dirs, files in os.walk("./dumps"):
            for f in files:
                if (xfn + '.') in f:
                    dumpIs = True
                    break

        #if not mod_globals.opt_demo and not dumpIs and not mod_globals.opt_dump:
        #    answer = raw_input('Save dump ? [y/n] : ')
        #    if 'N' in answer.upper():
        #        dumpIs = True

        if mod_globals.opt_demo:
            print "Loading dump"
            if len(ce['dump'])==0:
                decu.loadDump()
            else:
                decu.loadDump("./dumps/"+ce['dump'])
        elif mod_globals.opt_dump:
            ce['dump'] = self.guiSaveDump(decu)
            for ec in self.carecus:
                if ce['xml'][:-4] in ec['xml']:
                    ec['dump'] = ce['dump']
            self.renewEcuList()
            self.SaveBtnClick()

        # Load XML
        if not mod_db_manager.file_in_ddt(decu.ecufname):
            print "No such file: ", decu.ecufname
            return None

        ns = {'ns0': 'http://www-diag.renault.com/2002/ECU',
              'ns1': 'http://www-diag.renault.com/2002/screens'}

        tree = et.parse(mod_db_manager.get_file_from_ddt(decu.ecufname))
        xdoc = tree.getroot()

        # Show screen
        print "Show screen"
        scr = DDTScreen(decu.ecufname, xdoc, decu, top=True)

        del scr
        del decu

    def guiSaveDump(self,decu):
        ''' save responces from all 21xx, 22xxxx commands '''

        self.pdlg = tk.Toplevel()
        self.pdlg.option_add ('*Dialog.msg.font', 'Courier\ New 12')
        self.pdlg.geometry("256x100")
        self.pdlg.title("Saving dump")
        self.pdlg.configure(background="#d9d9d9")

        v_cmd = tk.StringVar()
        v_cmd.set("")
        e_cmd = tk.Label(self.pdlg, textvariable=v_cmd, background="#d9d9d9")
        e_cmd.pack(expand=1, fill=tk.X)

        v_cnt = tk.StringVar()
        v_cnt.set("")
        e_cnt = tk.Label(self.pdlg, textvariable=v_cnt, background="#d9d9d9")
        e_cnt.pack(expand=1, fill=tk.X)

        progress = ttk.Progressbar(self.pdlg, mode="determinate")
        progress.pack(expand=1, fill=tk.X)

        xmlname = decu.ecufname
        if xmlname.upper().endswith('.XML'):
            xmlname = xmlname[:-4]

        if '/' in xmlname:
            xmlname = xmlname.split('/')[-1]
        else:
            xmlname = xmlname.split('\\')[-1]

        dumpFileName = str(int(time.time())) + '_' + xmlname + '.txt'
        dumpPath = './dumps/' + dumpFileName
        df = open(dumpPath, 'wt')

        decu.elm.clear_cache()

        max = len(decu.requests.keys())

        progress['maximum'] = max
        progressValue = 1
        progress['value'] = progressValue

        im = ' from ' + str(max)
        i = 0
        for request in decu.requests.values():
            i = i + 1
            progressValue = progressValue + 1
            progress['value'] = progressValue
            progress.update()
            sys.stdout.flush()
            if request.SentBytes[:2] in mod_elm.AllowedList + ['17', '19']:
                if request.SentBytes[:2] == '19' and request.SentBytes[:2] != '1902':
                    continue
                v_cmd.set(request.SentBytes)
                e_cmd.update()
                v_cnt.set(str(i)+'/'+str(max))
                e_cnt.update()
                pos = chr(ord(request.SentBytes[0]) + 4) + request.SentBytes[1]
                rsp = decu.elm.request(request.SentBytes, pos, False)
                if ':' in rsp: continue
                df.write('%s:%s\n' % (request.SentBytes, rsp))

        df.close()
        self.pdlg.destroy()
        return dumpFileName

    def DemoBtnClick(self):

        ecu = self.getSelectedECU()
        if ecu==None or ecu['xml']=='':
            tkMessageBox.showinfo("INFO", "Selected ECU is undefined. Please scan it first.")
            return None

        mod_globals.opt_demo = True

        self.OpenECUScreens(ecu)

        return

    def fltBtnClick(self, ev=None):
        self.ptree.delete(*self.ptree.get_children())

        ptrn = self.filterText.get().strip().lower()

        for m in self.pl.plist:
            self.ptree.insert('','end',iid=m['name'], text=m['name'], open=True)
            for c in m['list']:
                if len(ptrn)==0 or ptrn in str(c).lower():
                    self.ptree.insert(m['name'], 'end', iid = c['code'], text = c['code'], values=[c['name'],c['segment'],c['addr']])

    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)

        # rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        # reverse sort next time
        tv.heading(col, command=lambda: \
            self.treeview_sort_column(tv, col, not reverse))

    def CarDoubleClick(self, event):
        try:
            item = self.ptree.selection()[0]
            line = self.ptree.item(item)['values']
            self.addr = mod_ddt_utils.ddtAddressing(line[2])
            self.v_proj.set(item)
            self.v_addr.set(line[2])
            self.v_vin.set('')
        except:
            pass

        tmpL = []
        self.carecus = []

        for e in self.addr.alist:
            if e['Address']==0:
                self.v_pcan.set(e['baudRate'])
                continue
            if e['Address']==255:
                self.v_mcan.set(e['baudRate'])
                continue

            if 'en' in e['longname'].keys():
                longname = e['longname']['en']
            else:
                longname = e['longname'].values()[0]

            if e['Address']:
                v_addr = hex(int(e['Address']))[2:].upper()
                if len(v_addr)==1:
                    v_addr = '0'+v_addr
            else:
                v_addr = ''
            if e['ISO8']:
                v_iso = hex(int(e['ISO8']))[2:].upper()
                if len(v_iso)==1:
                    v_addr = '0'+v_iso
            else:
                v_iso = ''
            if e['XId']:
                if len(e['XId'])>6:
                    v_XId = hex(0x80000000+int(e['XId']))[2:].upper()
                else:
                    v_XId = hex(int(e['XId']))[2:].upper()
            else:
                v_XId = ''
            if e['RId']:
                if len(e['RId'])>6:
                    v_RId = hex(0x80000000+int(e['RId']))[2:].upper()
                else:
                    v_RId = hex(int(e['RId']))[2:].upper()
            else:
                v_RId = ''

            if e['protocol']=='6' and (v_XId=='' or v_RId==''):
                continue #

            key = e['protocol'] + v_addr

            if key in tmpL:
                continue

            tmpL.append(key)

            v_prot = e['protocol']
            if e['protocol']=='1':
                v_prot = 'ISO8'
            elif e['protocol']=='2' or e['protocol']=='3':
                v_prot = 'KWP-SLOW'
            elif e['protocol']=='4' or e['protocol']=='5':
                v_prot = 'KWP-FAST'
            elif e['protocol']=='6' and self.v_pcan.get()=='250000':
                v_prot = 'CAN-250'
            elif e['protocol']=='6':
                v_prot = 'CAN-500'

            ecu = {}
            ecu['undef'] = '1'
            ecu['addr'] = v_addr
            ecu['iso8'] = v_iso
            ecu['xid'] = v_XId
            ecu['rid'] = v_RId
            ecu['prot'] = v_prot
            ecu['type'] = e['Name']
            ecu['name'] = longname
            ecu['xml'] = ''
            ecu['dump'] = ''
            ecu['ses'] = ''
            self.carecus.append(ecu)

        self.renewEcuList()

    def EcuDoubleClick(self, event):

        self.currentEcu = None

        try:
            item = self.ecutree.selection()[0]
            e = self.ecutree.item(item)['values'][8]
        except:
            pass

        ecu = None
        for ecu in self.carecus:
            if str(ecu)==e:
                break

        self.currentEcu = self.carecus.index(ecu)

        if ecu==None:
            return

        self.ecudlg = tk.Toplevel()
        self.ecudlg.option_add ('*Dialog.msg.font', 'Courier\ New 12')
        #ecudlg.geometry("256x256")
        self.ecudlg.title("Ecu settings")
        self.ecudlg.configure(background="#d9d9d9")

        optsGrid = {'ipadx': 0, 'ipady': 0, 'sticky': 'nswe'}
        optsGrid_w = {'ipadx': 0, 'ipady': 0, 'sticky': 'w'}
        optsGrid_e = {'ipadx': 0, 'ipady': 0, 'sticky': 'e'}
        ent_style = { 'background':"#FFFFFF",
                      'foreground':"#000000",
                      'highlightbackground':"#d9d9d9"}
        btn_style = { 'activebackground':"#d9d9d9",
                      'activeforeground':"#000000",
                      'background':"#d9d9d9",
                      'foreground':"#000000",
                      'highlightbackground':"#d9d9d9"}

        l_type = tk.Label(self.ecudlg, text='Type:', background="#d9d9d9")
        l_type.grid(row=0, column=0, **optsGrid_e)
        self.dv_type = tk.StringVar()
        self.dv_type.set(ecu['type'])
        e_type = tk.Entry(self.ecudlg, textvariable=self.dv_type, width=10,  **ent_style)
        e_type.grid(row=0, column=1, **optsGrid)

        l_name = tk.Label(self.ecudlg, text='Name:', background="#d9d9d9")
        l_name.grid(row=1, column=0, **optsGrid_e)
        self.dv_name = tk.StringVar()
        self.dv_name.set(ecu['name'])
        e_name = tk.Entry(self.ecudlg, textvariable=self.dv_name, width=10,  **ent_style)
        e_name.grid(row=1, column=1, **optsGrid)

        l_xid = tk.Label(self.ecudlg, text='Xid:', background="#d9d9d9")
        l_xid.grid(row=2, column=0, **optsGrid_e)
        self.dv_xid = tk.StringVar()
        self.dv_xid.set(ecu['xid'])
        e_xid = tk.Entry(self.ecudlg, textvariable=self.dv_xid, width=10,  **ent_style)
        e_xid.grid(row=2, column=1, **optsGrid)

        l_rid = tk.Label(self.ecudlg, text='Rid:', background="#d9d9d9")
        l_rid.grid(row=3, column=0, **optsGrid_e)
        self.dv_rid = tk.StringVar()
        self.dv_rid.set(ecu['rid'])
        e_rid = tk.Entry(self.ecudlg, textvariable=self.dv_rid, width=10,  **ent_style)
        e_rid.grid(row=3, column=1, **optsGrid)

        l_addr = tk.Label(self.ecudlg, text='Functional address:', background="#d9d9d9")
        l_addr.grid(row=4, column=0, **optsGrid_e)
        self.dv_addr = tk.StringVar()
        self.dv_addr.set(ecu['addr'])
        e_addr = tk.Entry(self.ecudlg, textvariable=self.dv_addr, width=10,  **ent_style)
        e_addr.grid(row=4, column=1, **optsGrid)

        l_iso = tk.Label(self.ecudlg, text='ISO address:', background="#d9d9d9")
        l_iso.grid(row=5, column=0, **optsGrid_e)
        self.dv_iso = tk.StringVar()
        self.dv_iso.set(ecu['iso8'])
        e_iso = tk.Entry(self.ecudlg, textvariable=self.dv_iso, width=10,  **ent_style)
        e_iso.grid(row=5, column=1, **optsGrid)

        l_ses = tk.Label(self.ecudlg, text='Session open cmd:', background="#d9d9d9")
        l_ses.grid(row=6, column=0, **optsGrid_e)
        self.dv_ses = tk.StringVar()
        self.dv_ses.set(ecu['ses'])
        e_ses = tk.Entry(self.ecudlg, textvariable=self.dv_ses, width=10,  **ent_style)
        e_ses.grid(row=6, column=1, **optsGrid)

        v_protList = ['ISO8', 'KWP-SLOW', 'KWP-FAST', 'CAN-250', 'CAN-500']
        l_pro = tk.Label(self.ecudlg, text='BUS type:', background="#d9d9d9")
        l_pro.grid(row=7, column=0, **optsGrid_e)
        self.dv_pro = tk.StringVar()
        self.dv_pro.set(ecu['prot'])
        c_pro = ttk.Combobox(self.ecudlg)
        c_pro.configure(values=v_protList)
        c_pro.configure(textvariable=self.dv_pro)
        c_pro.configure(takefocus="")
        c_pro.grid(row=7, column=1, **optsGrid)

        self.getXmlListByProj()
        l_xml = tk.Label(self.ecudlg, text='Recommended XML:', background="#d9d9d9")
        l_xml.grid(row=8, column=0, **optsGrid_e)
        self.dv_xml = tk.StringVar()
        self.dv_xml.set(ecu['xml'])
        c_xml = ttk.Combobox(self.ecudlg, width=30)
        c_xml.configure(values=self.v_xmlList)
        c_xml.configure(textvariable=self.dv_xml)
        c_xml.configure(takefocus="")
        c_xml.grid(row=8, column=1, **optsGrid_w)
        #b_xml = tk.Button(self.ecudlg, text="XML file", command=self.xmlBtnClick, **btn_style)
        #b_xml.grid(row=8, column=2, **optsGrid)

        allxmllist = []
        for l in sorted(mod_db_manager.get_file_list_from_ddt('ecus/*')):
            allxmllist.append( os.path.basename(l) )
        l2_xml = tk.Label(self.ecudlg, text='ALL XML:', background="#d9d9d9")
        l2_xml.grid(row=9, column=0, **optsGrid_e)
        a_xml = ttk.Combobox(self.ecudlg, width=30)
        a_xml.configure(values=allxmllist)
        a_xml.configure(textvariable=self.dv_xml)
        a_xml.configure(takefocus="")
        a_xml.grid(row=9, column=1, **optsGrid_w)


        self.getDumpListByXml()
        l_dump = tk.Label(self.ecudlg, text='Dump:', background="#d9d9d9")
        l_dump.grid(row=10, column=0, **optsGrid_e)
        self.dv_dump = tk.StringVar()
        self.dv_dump.set(ecu['dump'])
        c_dump = ttk.Combobox(self.ecudlg, width=30)
        c_dump.configure(values=self.v_dumpList)
        c_dump.configure(textvariable=self.dv_dump)
        c_dump.configure(takefocus="")
        c_dump.grid(row=10, column=1, **optsGrid_w)
        b_dump = tk.Button(self.ecudlg, text="Dump file", command=self.dumpBtnClick, **btn_style)
        b_dump.grid(row=10, column=2, **optsGrid)

        b_save = tk.Button(self.ecudlg, text="Save", command=self.ecuSaveBtnClick, **btn_style)
        b_save.grid(row=11, column=1, **optsGrid)

        b_canc = tk.Button(self.ecudlg, text="Cancel", command=self.ecuCancelBtnClick, **btn_style)
        b_canc.grid(row=11, column=2, **optsGrid)

    def renewEcuList(self):
        self.ecutree.delete(*self.ecutree.get_children())
        for ecu in mod_ddt_utils.multikeysort( self.carecus, ['undef','addr']):
            columns = (ecu['iso8'], ecu['xid'], ecu['rid'], ecu['prot'], ecu['type'], ecu['name'], ecu['xml'], ecu['dump'], ecu)
            if ecu['undef']=='0':
                self.ecutree.insert('', 'end', text=ecu['addr'], values=columns, tag='t1')
            else:
                self.ecutree.insert('', 'end', text=ecu['addr'], values=columns, tag='')
        self.ecutree.tag_configure('t1', background = "#fefcef")
        self.ecutree.update()

    def applySettings(self):
        mod_globals.opt_port = self.var_port.get().split(';')[0]
        mod_globals.opt_rate = int(self.var_speed.get())
        mod_globals.opt_can2 = self.var_can2.get()
        if self.var_log.get():
            mod_globals.opt_log = self.var_logName.get()
        else:
            mod_globals.opt_log = ""
        mod_globals.opt_cfc0 = True

    def xmlBtnClick(self):
        filename = tkFileDialog.askopenfilename(initialdir=mod_globals.ddtroot+'/ecus/', title='Select file',
                                                filetypes=[('xml files', '*.xml')])
        if '/' in filename:
            xfn = filename.split('/')[-1]
        else:
            xfn = filename.split('\\')[-1]
        self.dv_xml.set(xfn)
        return

    def dumpBtnClick(self):
        filename = tkFileDialog.askopenfilename(initialdir='./dumps/', title='Select file',
                                                filetypes=[('txt files', '*.txt')])
        if '/' in filename:
            xfn = filename.split('/')[-1]
        else:
            xfn = filename.split('\\')[-1]
        self.dv_dump.set(xfn)
        return

    def ecuSaveBtnClick(self):
        if self.currentEcu==None:
            return
        self.carecus[self.currentEcu]['type'] = self.dv_type.get()
        self.carecus[self.currentEcu]['name'] = self.dv_name.get()
        self.carecus[self.currentEcu]['xid'] = self.dv_xid.get()
        self.carecus[self.currentEcu]['rid'] = self.dv_rid.get()
        self.carecus[self.currentEcu]['addr'] = self.dv_addr.get()
        self.carecus[self.currentEcu]['iso8'] = self.dv_iso.get()
        self.carecus[self.currentEcu]['prot'] = self.dv_pro.get()
        self.carecus[self.currentEcu]['ses'] = self.dv_ses.get()
        self.carecus[self.currentEcu]['xml'] = self.dv_xml.get()
        self.carecus[self.currentEcu]['dump'] = self.dv_dump.get()
        if self.dv_xml.get()!='':
            self.carecus[self.currentEcu]['undef'] = '0'
        else:
            self.carecus[self.currentEcu]['undef'] = '1'
        self.ecudlg.destroy()
        self.renewEcuList()
        return

    def ecuCancelBtnClick(self):
        self.ecudlg.destroy()
        return

    def getXmlListByProj(self):
        self.v_xmlList = []
        try:
            for t in self.eculist[self.dv_addr.get()]['targets']:
                if self.v_proj.get().upper() in self.eculist[self.dv_addr.get()]['targets'][t]['Projects']:
                    self.v_xmlList.append(t)
        except:
            pass

    def getDumpListByXml(self, xmlname=None):

        if xmlname==None:
            self.v_dumpList = []
            xml = self.dv_xml.get()[:-4]
            for root, dirs, files in os.walk("./dumps"):
                for f in files:
                    if (xml + '.') in f:
                        self.v_dumpList.append(f)
        else:
            xmlname = xmlname[:-4]
            flist = []
            for root, dirs, files in os.walk("./dumps"):
                for f in files:
                    if (xmlname + '.') in f:
                        flist.append(f)

            if len(flist) == 0: return []
            flist.sort()
            return flist

    def saveSettings(self):
        self.save.port = self.var_port.get().split(';')[0]
        self.save.speed = self.var_speed.get()
        self.save.log = self.var_log.get()
        self.save.logName = self.var_logName.get()
        self.save.cfc = self.var_cfc.get()
        self.save.dump = self.var_dump.get()
        self.save.save()

    def loadSettings(self):

        self.var_cfc.set(self.save.cfc)
        self.var_dump.set(self.save.dump)
        self.var_port.set(self.save.port)
        self.var_speed.set(self.save.speed)
        self.var_log.set(self.save.log)
        self.var_logName.set(self.save.logName)

        self.var_speedList = ['38400', '115200', '230400', '500000', ]
        self.var_portList = mod_ddt_utils.getPortList()

        if len(self.var_port.get()) == 0:
            for p in self.var_portList:
                self.var_port.set(p)
                if 'OBD' in p: break

def main():
    '''Main function'''

    mod_utils.chkDirTree()
    mod_db_manager.find_DBs()

    lau = DDTLauncher()

    print "Done"


if __name__ == '__main__':
    main()
