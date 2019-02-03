#!/usr/bin/env python
# -*- coding: utf-8 -*-
# qpy:2
# qpy:kivy

##################################
#                                #
#                                #
#    Version: 2.0 (02-Feb-2019)  #
#    Author: Shr-Lnm             #
#                                #
#                                #
##################################


import os
from os import listdir
from os.path import isdir
from os.path import isfile
import sys

try:
    import cPickle as pickle
except:
    import pickle

osname = os.name

if osname == 'nt':
    import pip

    try:
        import serial
    except ImportError:
        pip.main(['install', 'pyserial'])
try:
    import androidhelper as android

    osname = 'android'
except:
    try:
        import android

        osname = 'android'
    except:
        pass

jnius_mode = False

if osname == 'android':
    try:
        from jnius import autoclass

        jnius_mode = True

    except ImportError:
        try:
            import pip
        except ImportError:
            pass
        # pip.main(['install', 'pyjnius-u4-qpython'])

    if jnius_mode:
        try:
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
            BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
            UUID = autoclass('java.util.UUID')
        except:
            print "Error while using jnius"
            sys.exit()


def getPathList():
    return ['./' + f for f in listdir('.') if isdir('./' + f) \
            and f.lower().startswith('pyren') \
            and isfile('./' + f + '/pyren.py')]


def getLangList():
    return [f[10:-4] for f in listdir('./Location') if f.lower().startswith('diagoncan_')]


def getPortList():
    ret = []
    if os.name != 'android':
        if jnius_mode:
            try:
                paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
                for device in paired_devices:
                    desc = device.getName()
                    de = unicode(desc.encode("ascii", "ignore"))
                    ret.append(u'BT;' + de)
            except:
                ret.append(u'BT;')
            return ret

        iterator = sorted(list(list_ports.comports()))
        for port, desc, hwid in iterator:
            try:
                de = unicode(desc.encode("ascii", "ignore"))
                ret.append(port + u';' + de)
            except:
                ret.append(port + ';')
        if '192.168.0.10:35000;WiFi' not in ret:
            ret.append('192.168.0.10:35000;WiFi')
    else:
        ret = ['BT', '192.168.0.10:35000']
    return ret


class settings():
    path = ''
    port = ''
    lang = 'RU'
    speed = '38400'
    logName = 'log.txt'
    log = False
    cfc = False
    n1c = False
    si = False
    dump = False
    can2 = False
    options = ''

    def __init__(self):
        self.load()

    def __del__(self):
        pass

    def load(self):
        if not os.path.isfile("./settings.p"):
            self.save()

        f = open('./settings.p', 'rb')
        tmp_dict = pickle.load(f)
        f.close()
        self.__dict__.update(tmp_dict)

    def save(self):
        f = open('./settings.p', 'wb')
        pickle.dump(self.__dict__, f)
        f.close()


def run(s, cmd):
    fullpath = os.path.dirname(os.path.realpath(sys.argv[0])) + s.path[1:]
    os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

    sys.path.insert(0, fullpath)

    if cmd == 'pyren' or cmd == 'scan' or cmd == 'demo':
        cmdr = __import__('pyren')
    elif cmd == 'check':
        cmdr = __import__('cmdr_chkelm')
    elif cmd == 'mon':
        cmdr = __import__('bus_monitor')
    elif cmd == 'ddt':
        cmdr = __import__('mod_ddt')
    elif cmd == 'term':
        cmdr = __import__('mod_term')

    if s.port.lower() == 'bt' or s.port == '': s.port = 'bt'
    sys.argv.append('-p' + s.port)
    if cmd == 'demo':
        sys.argv.append('--demo')
    if cmd == 'scan' and cmd != 'term':
        sys.argv.append('--scan')
    if s.log:
        sys.argv.append('--log=' + s.logName)
    if s.speed != '38400':
        sys.argv.append('-r' + s.speed)
    if s.lang != '' and cmd != 'term' and cmd != 'ddt':
        sys.argv.append('-L' + s.lang)
    if s.cfc:
        sys.argv.append('--cfc')
    if s.n1c:
        sys.argv.append('--n1c')
    if s.si:
        sys.argv.append('--si')
    if s.dump and cmd != 'term':
        sys.argv.append('--dump')
    if s.can2 and cmd != 'term':
        sys.argv.append('--can2')
    if s.options != '':
        sys.argv = sys.argv + s.options.split()
    if cmd == 'term':
        sys.argv.append('--dialog')
        #sys.argv.append('--demo')
    if cmd == 'ddt':
        sys.argv.append('--demo')
    os.chdir(s.path)
    cmdr.main()
    sys.exit()


if osname != 'android':
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        print "\n\n\n\tPleas install additional modules"
        print "\t\t>sudo easy_install pyserial"
        sys.exit()
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


    class desktopGUI(tk.Frame):

        save = None

        def guiDestroy(self):
            self.root.eval('::ttk::CancelRepeat')
            self.root.destroy()

        def cmd_Mon(self):
            self.saveSettings()
            self.guiDestroy()
            run(self.save, 'mon')

        def cmd_Check(self):
            self.saveSettings()
            self.guiDestroy()
            run(self.save, 'check')

        def cmd_Demo(self):
            self.saveSettings()
            self.guiDestroy()
            run(self.save, 'demo')

        def cmd_Scan(self):
            self.saveSettings()
            self.guiDestroy()
            run(self.save, 'scan')

        def cmd_Start(self):
            self.saveSettings()
            self.guiDestroy()
            run(self.save, 'pyren')

        def cmd_DDT(self):
            self.saveSettings()
            self.guiDestroy()
            run(self.save, 'ddt')

        def cmd_term(self):
            self.saveSettings()
            self.guiDestroy()
            run(self.save, 'term')

        def saveSettings(self):
            if len(self.var_entryPath.get()) > 0:
                self.save.path = self.var_entryPath.get()
            else:
                self.save.path = self.var_path.get()
            self.save.port = self.var_port.get().split(';')[0]
            self.save.lang = self.var_lang.get()
            self.save.speed = self.var_speed.get()
            self.save.log = self.var_log.get()
            self.save.logName = self.var_logName.get()
            self.save.cfc = self.var_cfc.get()
            self.save.n1c = self.var_n1c.get()
            self.save.si = self.var_si.get()
            self.save.dump = self.var_dump.get()
            self.save.can2 = self.var_can2.get()
            self.save.options = self.var_otherOptions.get()
            self.save.save()

        def loadSettings(self):

            self.var_si.set(self.save.si)
            self.var_cfc.set(self.save.cfc)
            self.var_n1c.set(self.save.n1c)
            self.var_can2.set(self.save.can2)
            self.var_dump.set(self.save.dump)
            self.var_lang.set(self.save.lang)
            self.var_path.set(self.save.path)
            self.var_port.set(self.save.port)
            self.var_speed.set(self.save.speed)
            self.var_entryPath.set('')
            self.var_otherOptions.set(self.save.options)
            self.var_log.set(self.save.log)
            self.var_logName.set(self.save.logName)

            self.var_speedList = ['38400', '115200', '230400', '500000', ]
            self.var_langList = getLangList()
            self.var_pathList = getPathList()
            self.var_portList = getPortList()

            if len(self.var_path.get()) == 0:
                self.var_path.set(self.var_pathList[0])

            if len(self.var_lang.get()) == 0:
                ll = self.var_langList
                if 'RU' in ll:
                    self.var_lang.set('RU')
                elif 'GB' in ll:
                    self.var_lang.set('GB')
                else:
                    self.var_lang.set(ll[0])

            if len(self.var_port.get()) == 0:
                for p in self.var_portList:
                    self.var_port.set(p)
                    if 'OBD' in p: break

        def __init__(self):
            self.save = settings()
            self.root = tk.Tk()
            self.root.option_add('*Dialog.msg.font', 'Courier New 12')
            self.root.geometry("500x500")
            tk.Frame.__init__(self, self.root)

            self.var_can2 = tk.BooleanVar()
            self.var_dump = tk.BooleanVar()
            self.var_log = tk.BooleanVar()

            self.var_cfc = tk.BooleanVar()
            self.var_n1c = tk.BooleanVar()
            self.var_si = tk.BooleanVar()

            self.var_langList = []
            self.var_pathList = []
            self.var_portList = []
            self.var_speedList = []

            self.var_lang = tk.StringVar()
            self.var_path = tk.StringVar()
            self.var_port = tk.StringVar()
            self.var_speed = tk.StringVar()

            self.var_logName = tk.StringVar()
            self.var_entryPath = tk.StringVar()
            self.var_otherOptions = tk.StringVar()

            self.loadSettings()

            self.root.title("Pyren Launcher")
            self.style = ttk.Style()
            self.style.theme_use('classic')

            if sys.platform == "win32": self.style.theme_use('winnative')
            self.style.configure('.', background='#d9d9d9')
            self.style.configure('.', foreground='#000000')
            self.style.configure('.', font="TkDefaultFont")
            self.style.map('.', background=[('selected', '#d9d9d9'), ('active', '#d9d9d9')])

            self.root.geometry("500x420+0+28")
            self.root.title("Pyren launcher")
            self.root.configure(background="#d9d9d9")
            self.root.configure(highlightbackground="#d9d9d9")
            self.root.configure(highlightcolor="black")

            self.lPathSelector = tk.LabelFrame(self.root)
            self.lPathSelector.place(relx=0.02, rely=0.0, relheight=0.27, relwidth=0.46)
            self.lPathSelector.configure(relief=tk.GROOVE)
            self.lPathSelector.configure(foreground="black")
            self.lPathSelector.configure(text='''Version''')
            self.lPathSelector.configure(background="#d9d9d9")
            self.lPathSelector.configure(highlightbackground="#d9d9d9")
            self.lPathSelector.configure(highlightcolor="black")
            self.lPathSelector.configure(width=230)

            self.lPortSelector = tk.LabelFrame(self.root)
            self.lPortSelector.place(relx=0.5, rely=0.0, relheight=0.27, relwidth=0.48)
            self.lPortSelector.configure(relief=tk.GROOVE)
            self.lPortSelector.configure(foreground="black")
            self.lPortSelector.configure(text='''Port''')
            self.lPortSelector.configure(background="#d9d9d9")
            self.lPortSelector.configure(highlightbackground="#d9d9d9")
            self.lPortSelector.configure(highlightcolor="black")
            self.lPortSelector.configure(width=240)

            self.lPortSpeed = tk.LabelFrame(self.root)
            self.lPortSpeed.place(relx=0.52, rely=0.12, relheight=0.13, relwidth=0.44)
            self.lPortSpeed.configure(relief=tk.GROOVE)
            self.lPortSpeed.configure(foreground="black")
            self.lPortSpeed.configure(text='''Port Speed (only for USB-ELM)''')
            self.lPortSpeed.configure(background="#d9d9d9")
            self.lPortSpeed.configure(highlightbackground="#d9d9d9")
            self.lPortSpeed.configure(highlightcolor="black")
            self.lPortSpeed.configure(width=220)

            self.lOtherPath = tk.LabelFrame(self.root)
            self.lOtherPath.place(relx=0.04, rely=0.12, relheight=0.13, relwidth=0.42)
            self.lOtherPath.configure(relief=tk.GROOVE)
            self.lOtherPath.configure(foreground="black")
            self.lOtherPath.configure(text='''Other path to script''')
            self.lOtherPath.configure(background="#d9d9d9")
            self.lOtherPath.configure(highlightbackground="#d9d9d9")
            self.lOtherPath.configure(highlightcolor="black")
            self.lOtherPath.configure(width=210)

            self.lDBLanguage = tk.LabelFrame(self.root)
            self.lDBLanguage.place(relx=0.02, rely=0.29, relheight=0.13, relwidth=0.3)
            self.lDBLanguage.configure(relief=tk.GROOVE)
            self.lDBLanguage.configure(foreground="black")
            self.lDBLanguage.configure(text='''DB Language''')
            self.lDBLanguage.configure(background="#d9d9d9")
            self.lDBLanguage.configure(highlightbackground="#d9d9d9")
            self.lDBLanguage.configure(highlightcolor="black")
            self.lDBLanguage.configure(width=100)

            self.lOptions = tk.LabelFrame(self.root)
            self.lOptions.place(relx=0.02, rely=0.69, relheight=0.13, relwidth=0.96)
            self.lOptions.configure(relief=tk.GROOVE)
            self.lOptions.configure(foreground="black")
            self.lOptions.configure(text='''Other options''')
            self.lOptions.configure(background="#d9d9d9")
            self.lOptions.configure(highlightbackground="#d9d9d9")
            self.lOptions.configure(highlightcolor="black")
            self.lOptions.configure(width=480)

            self.lLog = tk.LabelFrame(self.root)
            self.lLog.place(relx=0.34, rely=0.29, relheight=0.13, relwidth=0.36)
            self.lLog.configure(relief=tk.GROOVE)
            self.lLog.configure(foreground="black")
            self.lLog.configure(text='''Log''')
            self.lLog.configure(background="#d9d9d9")
            self.lLog.configure(highlightbackground="#d9d9d9")
            self.lLog.configure(highlightcolor="black")
            self.lLog.configure(width=230)

            self.lCAN = tk.LabelFrame(self.root)
            self.lCAN.place(relx=0.02, rely=0.43, relheight=0.25, relwidth=0.46)
            self.lCAN.configure(relief=tk.GROOVE)
            self.lCAN.configure(foreground="black")
            self.lCAN.configure(text='''CAN''')
            self.lCAN.configure(background="#d9d9d9")
            self.lCAN.configure(highlightbackground="#d9d9d9")
            self.lCAN.configure(highlightcolor="black")
            self.lCAN.configure(width=230)

            self.lKWP = tk.LabelFrame(self.root)
            self.lKWP.place(relx=0.5, rely=0.43, relheight=0.25, relwidth=0.48)
            self.lKWP.configure(relief=tk.GROOVE)
            self.lKWP.configure(foreground="black")
            self.lKWP.configure(text='''K-Line''')
            self.lKWP.configure(background="#d9d9d9")
            self.lKWP.configure(highlightbackground="#d9d9d9")
            self.lKWP.configure(highlightcolor="black")
            self.lKWP.configure(width=240)

            self.mCFC = tk.Message(self.root)
            self.mCFC.place(relx=0.08, rely=0.5, relheight=0.06, relwidth=0.1)
            self.mCFC.configure(background="#d9d9d9")
            self.mCFC.configure(foreground="#000000")
            self.mCFC.configure(highlightbackground="#d9d9d9")
            self.mCFC.configure(highlightcolor="black")
            self.mCFC.configure(text='''--cfc''')
            self.mCFC.configure(width=40)

            self.mN1C = tk.Message(self.root)
            self.mN1C.place(relx=0.08, rely=0.57, relheight=0.06, relwidth=0.1)
            self.mN1C.configure(background="#d9d9d9")
            self.mN1C.configure(foreground="#000000")
            self.mN1C.configure(highlightbackground="#d9d9d9")
            self.mN1C.configure(highlightcolor="black")
            self.mN1C.configure(text='''--n1c''')
            self.mN1C.configure(width=40)

            self.mSI = tk.Message(self.root)
            self.mSI.place(relx=0.56, rely=0.50, relheight=0.07, relwidth=0.1)
            self.mSI.configure(background="#d9d9d9")
            self.mSI.configure(foreground="#000000")
            self.mSI.configure(highlightbackground="#d9d9d9")
            self.mSI.configure(highlightcolor="black")
            self.mSI.configure(text='''--si''')
            self.mSI.configure(width=40)

            self.mCAN = tk.Message(self.root)
            self.mCAN.place(relx=0.18, rely=0.48, relheight=0.18, relwidth=0.28)
            self.mCAN.configure(background="#d9d9d9")
            self.mCAN.configure(foreground="#000000")
            self.mCAN.configure(highlightbackground="#d9d9d9")
            self.mCAN.configure(highlightcolor="black")
            self.mCAN.configure(
                text='''These options should be enabled for some fake chinese ELM. Any of them decrease data rate.''')
            self.mCAN.configure(width=142)

            self.mKWP = tk.Message(self.root)
            self.mKWP.place(relx=0.64, rely=0.48, relheight=0.13, relwidth=0.3)
            self.mKWP.configure(background="#d9d9d9")
            self.mKWP.configure(foreground="#000000")
            self.mKWP.configure(highlightbackground="#d9d9d9")
            self.mKWP.configure(highlightcolor="black")
            self.mKWP.configure(text='''Try Slow Init before Fast Init. It may helps with old ECUs''')
            self.mKWP.configure(width=152)

            self.otherPath = tk.Entry(self.root)
            self.otherPath.place(relx=0.06, rely=0.17, relheight=0.06, relwidth=0.38)
            self.otherPath.configure(background="white")
            self.otherPath.configure(font="TkFixedFont")
            self.otherPath.configure(foreground="#000000")
            self.otherPath.configure(highlightbackground="#d9d9d9")
            self.otherPath.configure(highlightcolor="black")
            self.otherPath.configure(insertbackground="black")
            self.otherPath.configure(selectbackground="#c4c4c4")
            self.otherPath.configure(selectforeground="black")
            self.otherPath.configure(textvariable=self.var_entryPath)

            self.logName = tk.Entry(self.root)
            self.logName.place(relx=0.42, rely=0.33, relheight=0.06, relwidth=0.26)
            self.logName.configure(background="white")
            self.logName.configure(font="TkFixedFont")
            self.logName.configure(foreground="#000000")
            self.logName.configure(highlightbackground="#d9d9d9")
            self.logName.configure(highlightcolor="black")
            self.logName.configure(insertbackground="black")
            self.logName.configure(selectbackground="#c4c4c4")
            self.logName.configure(selectforeground="black")
            self.logName.configure(textvariable=self.var_logName)

            self.cbLog = tk.Checkbutton(self.root)
            self.cbLog.place(relx=0.36, rely=0.33, relheight=0.07, relwidth=0.06)
            self.cbLog.configure(activebackground="#d9d9d9")
            self.cbLog.configure(activeforeground="#000000")
            self.cbLog.configure(background="#d9d9d9")
            self.cbLog.configure(foreground="#000000")
            self.cbLog.configure(highlightbackground="#d9d9d9")
            self.cbLog.configure(highlightcolor="black")
            self.cbLog.configure(justify=tk.LEFT)
            self.cbLog.configure(variable=self.var_log)
            # self.cbLog.configure(variable=self.che40)

            self.cbCFC = tk.Checkbutton(self.lCAN)
            self.cbCFC.place(relx=0.04, rely=0.17, relheight=0.29, relwidth=0.13)
            self.cbCFC.configure(activebackground="#d9d9d9")
            self.cbCFC.configure(activeforeground="#000000")
            self.cbCFC.configure(background="#d9d9d9")
            self.cbCFC.configure(foreground="#000000")
            self.cbCFC.configure(highlightbackground="#d9d9d9")
            self.cbCFC.configure(highlightcolor="black")
            self.cbCFC.configure(justify=tk.LEFT)
            self.cbCFC.configure(variable=self.var_cfc)
            # self.cbCFC.configure(variable=self.che43)

            self.cbN1C = tk.Checkbutton(self.lCAN)
            self.cbN1C.place(relx=0.04, rely=0.48, relheight=0.29, relwidth=0.13)
            self.cbN1C.configure(activebackground="#d9d9d9")
            self.cbN1C.configure(activeforeground="#000000")
            self.cbN1C.configure(background="#d9d9d9")
            self.cbN1C.configure(foreground="#000000")
            self.cbN1C.configure(highlightbackground="#d9d9d9")
            self.cbN1C.configure(highlightcolor="black")
            self.cbN1C.configure(justify=tk.LEFT)
            self.cbN1C.configure(variable=self.var_n1c)
            # self.cbN1C.configure(variable=self.che44)

            self.cbSI = tk.Checkbutton(self.lKWP)
            self.cbSI.place(relx=0.04, rely=0.18, relheight=0.29, relwidth=0.13)
            self.cbSI.configure(activebackground="#d9d9d9")
            self.cbSI.configure(activeforeground="#000000")
            self.cbSI.configure(background="#d9d9d9")
            self.cbSI.configure(foreground="#000000")
            self.cbSI.configure(highlightbackground="#d9d9d9")
            self.cbSI.configure(highlightcolor="black")
            self.cbSI.configure(justify=tk.LEFT)
            self.cbSI.configure(variable=self.var_si)
            # self.cbSI.configure(variable=self.che45)

            self.lDump = tk.LabelFrame(self.root)
            self.lDump.place(relx=0.72, rely=0.29, relheight=0.13, relwidth=0.12)
            self.lDump.configure(relief=tk.GROOVE)
            self.lDump.configure(foreground="black")
            self.lDump.configure(text='''Dump''')
            self.lDump.configure(background="#d9d9d9")
            self.lDump.configure(highlightbackground="#d9d9d9")
            self.lDump.configure(highlightcolor="black")
            self.lDump.configure(width=60)

            self.lCAN2 = tk.LabelFrame(self.root)
            self.lCAN2.place(relx=0.86, rely=0.29, relheight=0.13, relwidth=0.12)
            self.lCAN2.configure(relief=tk.GROOVE)
            self.lCAN2.configure(foreground="black")
            self.lCAN2.configure(text='''CAN 2''')
            self.lCAN2.configure(background="#d9d9d9")
            self.lCAN2.configure(highlightbackground="#d9d9d9")
            self.lCAN2.configure(highlightcolor="black")
            self.lCAN2.configure(width=60)

            self.cbDump = tk.Checkbutton(self.lDump)
            self.cbDump.place(relx=0.17, rely=0.18, relheight=0.55, relwidth=0.5)
            self.cbDump.configure(activebackground="#d9d9d9")
            self.cbDump.configure(activeforeground="#000000")
            self.cbDump.configure(background="#d9d9d9")
            self.cbDump.configure(foreground="#000000")
            self.cbDump.configure(highlightbackground="#d9d9d9")
            self.cbDump.configure(highlightcolor="black")
            self.cbDump.configure(variable=self.var_dump)
            # self.cbDump.configure(variable=self.che41)
            self.cbDump.configure(width=34)

            self.cbCAN2 = tk.Checkbutton(self.lCAN2)
            self.cbCAN2.place(relx=0.17, rely=0.18, relheight=0.55, relwidth=0.5)
            self.cbCAN2.configure(activebackground="#d9d9d9")
            self.cbCAN2.configure(activeforeground="#000000")
            self.cbCAN2.configure(background="#d9d9d9")
            self.cbCAN2.configure(foreground="#000000")
            self.cbCAN2.configure(highlightbackground="#d9d9d9")
            self.cbCAN2.configure(highlightcolor="black")
            self.cbCAN2.configure(variable=self.var_can2)
            # self.cbCAN2.configure(variable=self.che42)
            self.cbCAN2.configure(width=34)

            self.Options = tk.Entry(self.root)
            self.Options.place(relx=0.04, rely=0.74, relheight=0.06, relwidth=0.92)
            self.Options.configure(background="white")
            self.Options.configure(font="TkFixedFont")
            self.Options.configure(foreground="#000000")
            self.Options.configure(highlightbackground="#d9d9d9")
            self.Options.configure(highlightcolor="black")
            self.Options.configure(insertbackground="black")
            self.Options.configure(selectbackground="#c4c4c4")
            self.Options.configure(selectforeground="black")
            self.Options.configure(textvariable=self.var_otherOptions)

            self.btnStart = tk.Button(self.root)
            self.btnStart.place(relx=0.01, rely=0.88, height=22, width=100)
            self.btnStart.configure(activebackground="#d9d9d9")
            self.btnStart.configure(activeforeground="#000000")
            self.btnStart.configure(background="#d9d9d9")
            self.btnStart.configure(command=self.cmd_Start)
            self.btnStart.configure(foreground="#000000")
            self.btnStart.configure(highlightbackground="#d9d9d9")
            self.btnStart.configure(highlightcolor="black")
            self.btnStart.configure(text='''Start pyren''')
            self.btnStart.configure(width=70)

            #self.btnDDT = tk.Button(self.root)
            #self.btnDDT.place(relx=0.01, rely=0.91, height=22, width=100)
            #self.btnDDT.configure(activebackground="#d9d9d9")
            #self.btnDDT.configure(activeforeground="#000000")
            #self.btnDDT.configure(background="#d9d9d9")
            #self.btnDDT.configure(command=self.cmd_DDT)
            #self.btnDDT.configure(foreground="#000000")
            #self.btnDDT.configure(highlightbackground="#d9d9d9")
            #self.btnDDT.configure(highlightcolor="black")
            #self.btnDDT.configure(text='''Start DDT''')
            #self.btnDDT.configure(width=70)

            self.btnScan = tk.Button(self.root)
            self.btnScan.place(relx=0.21, rely=0.88, height=22, width=100)
            self.btnScan.configure(activebackground="#d9d9d9")
            self.btnScan.configure(activeforeground="#000000")
            self.btnScan.configure(background="#d9d9d9")
            self.btnScan.configure(command=self.cmd_Scan)
            self.btnScan.configure(foreground="#000000")
            self.btnScan.configure(highlightbackground="#d9d9d9")
            self.btnScan.configure(highlightcolor="black")
            self.btnScan.configure(text='''Scan''')
            self.btnScan.configure(width=70)

            self.btnDemo = tk.Button(self.root)
            self.btnDemo.place(relx=0.41, rely=0.88, height=22, width=100)
            self.btnDemo.configure(activebackground="#d9d9d9")
            self.btnDemo.configure(activeforeground="#000000")
            self.btnDemo.configure(background="#d9d9d9")
            self.btnDemo.configure(command=self.cmd_Demo)
            self.btnDemo.configure(foreground="#000000")
            self.btnDemo.configure(highlightbackground="#d9d9d9")
            self.btnDemo.configure(highlightcolor="black")
            self.btnDemo.configure(text='''Demo''')
            self.btnDemo.configure(width=82)

            self.btnCheck = tk.Button(self.root)
            self.btnCheck.place(relx=0.61, rely=0.88, height=22, width=100)
            self.btnCheck.configure(activebackground="#d9d9d9")
            self.btnCheck.configure(activeforeground="#000000")
            self.btnCheck.configure(background="#d9d9d9")
            self.btnCheck.configure(command=self.cmd_Check)
            self.btnCheck.configure(foreground="#000000")
            self.btnCheck.configure(highlightbackground="#d9d9d9")
            self.btnCheck.configure(highlightcolor="black")
            self.btnCheck.configure(text='''Check ELM''')

            self.btnMon = tk.Button(self.root)
            self.btnMon.place(relx=0.81, rely=0.84, height=22, width=90)
            self.btnMon.configure(activebackground="#d9d9d9")
            self.btnMon.configure(activeforeground="#000000")
            self.btnMon.configure(background="#d9d9d9")
            self.btnMon.configure(command=self.cmd_Mon)
            self.btnMon.configure(foreground="#000000")
            self.btnMon.configure(highlightbackground="#d9d9d9")
            self.btnMon.configure(highlightcolor="black")
            self.btnMon.configure(text='''Monitor''')

            self.btnMac = tk.Button(self.root)
            self.btnMac.place(relx=0.81, rely=0.91, height=22, width=90)
            self.btnMac.configure(activebackground="#d9d9d9")
            self.btnMac.configure(activeforeground="#000000")
            self.btnMac.configure(background="#d9d9d9")
            self.btnMac.configure(command=self.cmd_term)
            self.btnMac.configure(foreground="#000000")
            self.btnMac.configure(highlightbackground="#d9d9d9")
            self.btnMac.configure(highlightcolor="black")
            self.btnMac.configure(text='''Macro''')

            self.pathList = ttk.Combobox(self.root)
            self.pathList.place(relx=0.04, rely=0.05, relheight=0.06, relwidth=0.41)
            self.pathList.configure(values=['./pyren09a', './pyren09a'])
            self.pathList.configure(values=self.var_pathList)
            self.pathList.configure(textvariable=self.var_path)
            self.pathList.configure(takefocus="")

            self.portList = ttk.Combobox(self.root)
            self.portList.place(relx=0.52, rely=0.05, relheight=0.06, relwidth=0.43)
            self.portList.configure(values=self.var_portList)
            self.portList.configure(textvariable=self.var_port)
            self.portList.configure(takefocus="")

            self.speedList = ttk.Combobox(self.root)
            self.speedList.place(relx=0.54, rely=0.17, relheight=0.06, relwidth=0.41)
            self.speedList.configure(values=self.var_speedList)
            self.speedList.configure(textvariable=self.var_speed)
            self.speedList.configure(takefocus="")

            self.langList = ttk.Combobox(self.root)
            self.langList.place(relx=0.04, rely=0.33, relheight=0.06, relwidth=0.25)
            self.langList.configure(values=self.var_langList)
            self.langList.configure(textvariable=self.var_lang)
            self.langList.configure(takefocus="")

            self.root.focus_force()
            self.root.focus_set()
            self.root.mainloop()

        def __del__(self):
            pass


    def main():
        gui = desktopGUI()


    if __name__ == '__main__':
        os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
        main()

else:
    class androidGUI():

        save = None
        pl = []
        ll = []

        def cmd_Mon(self):
            self.saveSettings()
            self.droid.fullDismiss()
            run(self.save, 'mon')

        def cmd_Check(self):
            self.saveSettings()
            self.droid.fullDismiss()
            run(self.save, 'check')

        def cmd_Demo(self):
            self.saveSettings()
            self.droid.fullDismiss()
            run(self.save, 'demo')

        def cmd_Scan(self):
            self.saveSettings()
            self.droid.fullDismiss()
            run(self.save, 'scan')

        def cmd_Start(self):
            self.saveSettings()
            self.droid.fullDismiss()
            run(self.save, 'pyren')

        def saveSettings(self):
            self.save.path = self.pl[int(self.droid.fullQueryDetail("sp_version").result['selectedItemPosition'])]
            self.save.lang = self.ll[int(self.droid.fullQueryDetail("sp_language").result['selectedItemPosition'])]

            if self.droid.fullQueryDetail("rb_bt").result['checked'] == 'false':
                self.save.port = self.droid.fullQueryDetail("in_wifi").result['text']
            else:
                self.save.port = 'BT'

            self.save.speed = '38400'

            self.save.logName = self.droid.fullQueryDetail("in_logname").result['text']

            if self.droid.fullQueryDetail("cb_log").result['checked'] == 'false':
                self.save.log = False
            else:
                self.save.log = True

            if self.droid.fullQueryDetail("cb_cfc").result['checked'] == 'false':
                self.save.cfc = False
            else:
                self.save.cfc = True

            if self.droid.fullQueryDetail("cb_n1c").result['checked'] == 'false':
                self.save.n1c = False
            else:
                self.save.n1c = True

            if self.droid.fullQueryDetail("cb_si").result['checked'] == 'false':
                self.save.si = False
            else:
                self.save.si = True

            if self.droid.fullQueryDetail("cb_dump").result['checked'] == 'false':
                self.save.dump = False
            else:
                self.save.dump = True

            if self.droid.fullQueryDetail("cb_can2").result['checked'] == 'false':
                self.save.can2 = False
            else:
                self.save.can2 = True

            self.save.options = self.droid.fullQueryDetail("in_options").result['text']

            self.save.save()

        def loadSettings(self):

            pl = getPathList()
            if self.save.path in pl: pl.insert(0, pl.pop(pl.index(self.save.path)))
            self.droid.fullSetList("sp_version", pl)
            self.pl = pl

            ll = getLangList()
            if self.save.lang in ll: ll.insert(0, ll.pop(ll.index(self.save.lang)))
            self.droid.fullSetList("sp_language", ll)
            self.ll = ll

            if self.save.port == '':
                self.save.port = "192.168.0.10:35000"
            if self.save.port.lower() == 'bt':
                self.droid.fullSetProperty("rb_bt", "checked", "true")
                self.droid.fullSetProperty("rb_wifi", "checked", "false")
                self.droid.fullSetProperty("in_wifi", "text", "192.168.0.10:35000")
            else:
                self.droid.fullSetProperty("rb_bt", "checked", "false")
                self.droid.fullSetProperty("rb_wifi", "checked", "true")
                self.droid.fullSetProperty("in_wifi", "text", self.save.port)

            self.droid.fullSetProperty("in_logname", "text", self.save.logName)
            if self.save.log:
                self.droid.fullSetProperty("cb_log", "checked", "true")
            else:
                self.droid.fullSetProperty("cb_log", "checked", "false")

            if self.save.cfc:
                self.droid.fullSetProperty("cb_cfc", "checked", "true")
            else:
                self.droid.fullSetProperty("cb_cfc", "checked", "false")

            if self.save.n1c:
                self.droid.fullSetProperty("cb_n1c", "checked", "true")
            else:
                self.droid.fullSetProperty("cb_n1c", "checked", "false")

            if self.save.si:
                self.droid.fullSetProperty("cb_si", "checked", "true")
            else:
                self.droid.fullSetProperty("cb_si", "checked", "false")

            if self.save.dump:
                self.droid.fullSetProperty("cb_dump", "checked", "true")
            else:
                self.droid.fullSetProperty("cb_dump", "checked", "false")

            if self.save.can2:
                self.droid.fullSetProperty("cb_can2", "checked", "true")
            else:
                self.droid.fullSetProperty("cb_can2", "checked", "false")

            self.droid.fullSetProperty("in_options", "text", self.save.options)

        lay = '''<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content" >

    <ScrollView
        android:layout_width="fill_parent"
        android:layout_height="fill_parent" >
        
        <RelativeLayout
            android:id="@+id/launcher"
            xmlns:android="http://schemas.android.com/apk/res/android"
            android:layout_width="fill_parent"
            android:layout_height="wrap_content">
        
            <TextView
                android:id="@+id/tx_Versions"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentTop="true"
                android:text="Version"/>
            <Spinner
                android:id="@+id/sp_version"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/tx_Versions" />
            <TextView
                android:id="@+id/tx_language"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/sp_version"
                android:text="DB language" />
            <Spinner
                android:id="@+id/sp_language"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_language"/>
            <TextView
                android:id="@+id/tx_elm"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/sp_language"
                android:text="ELM327" />
            <RadioGroup
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:orientation="horizontal"
                android:layout_below="@id/tx_elm"
                android:id="@+id/radioGroup">
                <RadioButton
                    android:id="@id/rb_bt"
                    android:layout_width="wrap_content"
                    android:layout_height="match_parent"
                    android:checked="true"
                    android:text="BT" />
                <RadioButton
                    android:id="@id/rb_wifi"
                    android:layout_width="wrap_content"
                    android:layout_height="wrap_content"
                    android:checked="false"
                    android:text="WiFi" />
            </RadioGroup>
            <EditText
                android:id="@+id/in_wifi"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_alignParentRight="true"
                android:layout_below="@id/tx_elm"
                android:layout_toRightOf="@id/radioGroup"
                android:layout_marginLeft="20dp"
                android:ems="10"
                android:text="192.168.0.10:35000" />
            <TextView
                android:id="@+id/tx_log"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/radioGroup"
                android:text="Log" />
            <CheckBox
                android:id="@+id/cb_log"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_log"
                android:layout_marginLeft="20dp"
                android:layout_marginRight="20dp"
                android:layout_toRightOf="@+id/tx_log"/>
            <EditText
                android:id="@+id/in_logname"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_log"
                android:layout_toRightOf="@+id/cb_log"
                android:ems="10"
                android:text="log.txt" />
            <TextView
                android:id="@+id/tx_can"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/in_logname"
                android:text="CAN parameters" />
            <CheckBox
                android:id="@+id/cb_cfc"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_can"
                android:layout_alignLeft="@id/in_logname"
                android:text="--cfc" />
            <CheckBox
                android:id="@+id/cb_n1c"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignBottom="@id/cb_cfc"
                android:layout_toRightOf="@id/cb_cfc"
                android:layout_marginLeft="40dp"
                android:text="--n1c" />
            <TextView
                android:id="@+id/tx_iso"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/cb_cfc"
                android:layout_alignParentLeft="true"
                android:text="K-line parameters" />
            <CheckBox
                android:id="@+id/cb_si"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_iso"
                android:layout_alignLeft="@id/cb_cfc"
                android:text="--si (Prefer SlowInit)" />
            <TextView
                android:id="@+id/tx_options"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/cb_si"
                android:layout_alignParentLeft="true"
                android:text="Other options" />    
            <CheckBox
                android:id="@+id/cb_dump"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_options"
                android:layout_toRightOf="@id/tx_options"
                android:text="Dump" />
            <CheckBox
                android:id="@+id/cb_can2"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_toRightOf="@id/cb_dump"
                android:layout_alignBottom="@id/cb_dump"
                android:layout_marginLeft="60dp"
                android:text="CAN2" />    
             <EditText
                android:id="@+id/in_options"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_below="@+id/cb_dump"
                android:layout_centerHorizontal="true"
                android:ems="10"
                android:inputType="textPersonName" />
            <Button
                android:id="@+id/bt_start"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@id/in_options"
                android:text="Start" />
            <Button
                android:id="@+id/bt_scan"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_toRightOf="@id/bt_start"
                android:layout_below="@id/in_options"
                android:text="Scan" />
            <Button
                android:id="@+id/bt_demo"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/in_options"
                android:layout_toRightOf="@id/bt_scan"
                android:text="Demo" />
            <Button
                android:id="@+id/bt_check"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/bt_start"
                android:layout_alignParentRight="true"
                android:text="ChkELM" />
            <Button
                android:id="@+id/bt_mon"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_below="@id/bt_start"
                android:layout_toLeftOf="@id/bt_check"
                android:text="Monitor" />
        </RelativeLayout>
    
    </ScrollView>

</RelativeLayout>'''

        def eventloop(self):
            while True:
                event = self.droid.eventWait(50).result
                if event == None: continue
                if event["name"] == "click":
                    id = event["data"]["id"]
                    if id == "bt_start":
                        self.cmd_Start()
                    elif id == "bt_scan":
                        self.cmd_Scan()
                    elif id == "bt_demo":
                        self.cmd_Demo()
                    elif id == "bt_check":
                        self.cmd_Check()
                    elif id == "bt_mon":
                        self.cmd_Mon()

        def __init__(self):
            self.save = settings()
            try:
                self.droid = android.Android()
                self.droid.fullShow(self.lay)
                self.loadSettings()
                self.eventloop()
            finally:
                self.droid.fullDismiss()

        def __del__(self):
            self.droid.fullDismiss()


    def main():
        gui = androidGUI()


    if __name__ == '__main__':
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        # os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))
        main()
