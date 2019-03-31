#!/usr/bin/env python

import sys, os, re
import time
import mod_globals
import mod_elm
import mod_utils

try:
    import readline
except:
    pass

os.chdir (os.path.dirname (os.path.realpath (sys.argv[0])))

macro = {}
var = {}
stack = []

auto_macro = ""
auto_dia = False

mod_globals.os = os.name

if mod_globals.os == 'nt':
    import pip

    try:
        import serial
    except ImportError:
        pip.main(['install', 'pyserial'])

    try:
        import colorama
    except ImportError:
        pip.main(['install', 'colorama'])
        try:
            import colorama
        except ImportError:
            print "\n\n\n\t\t\tGive me access to the Internet for download modules\n\n\n"
            sys.exit()
    colorama.init()
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
    except ImportError:
        print "\n\n\n\tPleas install additional modules"
        print "\t\t>sudo easy_install pyserial"
        sys.exit()


def init_macro():
    global macro
    macro = {}
    
def init_var(): 
    global var
    var = {}    
    #predefined variables
    var['$addr'] = '7A'
    var['$txa'] = '7E0'
    var['$rxa'] = '7E8'
    var['$prompt'] = 'ELM'

def pars_macro( file ):
    
    global macro
    global var
    
    print 'openning file:', file
    f = open( file, 'rt' )
    lines = f.readlines()
    f.close()
    
    macroname = ''
    macrostrings = []
    line_num = 0
    for l in lines:
      line_num += 1
      l = l.split('#')[0] # remove comments
      l = l.strip()
      if l == '': continue
      if '{' in l:
        if macroname=='':
          literals =  l.split('{')
          macroname = literals[0].strip()
          macroname = macroname.replace(' ', '_').replace('\t', '_')
          macrostrings = []
          if len(literals)>1 and literals[1]!='' :
            macrostrings.append(literals[1])
          continue
        else:
          print 'Error: empty macro name in line:', line_num
          macro = {}
          var = {}
          return
      if '}' in l:
        if macroname!='':
          literals =  l.split('}')
          cmd = literals[0].strip()
          if cmd!='':
            macrostrings.append(cmd)
          macro[macroname] = macrostrings
          macroname = ''
          macrostrings = []
          continue
        else:
          print 'Error: unexpected end of macro in line:', line_num
          macro = {}
          var = {}
          return
      m = re.search('\$\S+\s*=\s*\S+', l)
      if m and macroname=='':
        #variable definition
        r = m.group(0).replace(' ', '').replace('\t', '')
        rl = r.split('=')
        var[rl[0]]=rl[1]
      else:
        macrostrings.append(l)

def load_macro( mf='' ):
    """
    dynamically loaded macro should have .txt extension and placed in ./macro directory
    """

    if mf=='' :
        for root, dirs, files in os.walk("./macro"):
            for mfile in files:
                if mfile.endswith('.txt'):
                    full_path = os.path.join("./macro/", mfile)
                    pars_macro(full_path)
    else:
        pars_macro(mf) 
        
def play_macro( mname, elm ):
    global macro
    global var
    global stack
    
    if mname in stack:
      print 'Error: recursion prohibited:', mname
      return
    else:
      stack.append(mname)
      
    for l in macro[mname]:
      #find veriable definition
      m = re.search('\$\S+\s*=\s*\S+', l)
      if m: 
        r = m.group(0).replace(' ', '').replace('\t', '')
        rl = r.split('=')
        var[rl[0]]=rl[1]
        if rl[0]=='$addr':
          if var['$addr'].upper() in mod_elm.dnat.keys():
            var['$txa'] = mod_elm.dnat[var['$addr'].upper()]
            var['$rxa'] = mod_elm.snat[var['$addr'].upper()]
            elm.currentaddress = var['$addr'].upper()
        continue
    
      #find veriable usage
      m = re.search('\$\S+', l)
      while m:
        vu = m.group(0)
        if vu in var.keys():
          l = re.sub("\\"+vu,var[vu], l)
        else:
          print 'Error: unknown variable',vu,'in',mname
          return
        m = re.search('\$\S+', l)
      
      if l in macro.keys():
        play_macro( l, elm )
        continue
        
      print elm.cmd(l)
    
    stack.remove(mname)

def print_help():
    """
    [h]elp                 - this help
    [q]uit, [e]xit, end    - exit from terminal
    wait|sleep x           - wait x seconds
    """
    global var
    global macro
    
    print print_help.__doc__

    print 'Variables:'
    for v in var.keys():
      print '  '+v+' = '+var[v]
    print
    print 'Macros:'
    for m in macro.keys():
      print '  '+m
    print
    

def optParser():
  '''Parsing of command line parameters. User should define at least com port name'''
  
  import argparse
  
  global auto_macro
  global auto_dia

  parser = argparse.ArgumentParser(
    #usage = "%prog -p <port> [options]",
    version="pyRen terminal Version 0.9.k",
    description = "pyRen terminal"
  )
  
  parser.add_argument('-p',
      help="ELM327 com port name",
      dest="port",
      default="")

  parser.add_argument("-r",
      help="com port rate during diagnostic session {38400[default],57600,115200,230400,500000}",
      dest="rate",
      default="38400",)

  parser.add_argument("-m",
      help="macro file name",
      dest="macro",
      default="",)

  parser.add_argument("--log",
      help="log file name",
      dest="logfile",
      default="")

  parser.add_argument("--demo",
      help="for debuging purpose. Work without car and ELM",
      dest="demo",
      default=False,
      action="store_true")

  parser.add_argument("--si",
      help="try SlowInit first",
      dest="si",
      default=False,
      action="store_true")

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

  parser.add_argument("--dialog",
      help="show dialog for selecting macro",
      dest="dia",
      default=False,
      action="store_true")

  options = parser.parse_args()
  
  if not options.port and mod_globals.os != 'android':
    parser.print_help()
    iterator = sorted(list(list_ports.comports()))
    print ""
    print "Available COM ports:"
    for port, desc, hwid in iterator:
      print "%-30s \n\tdesc: %s \n\thwid: %s" % (port,desc.decode("windows-1251"),hwid)
    print ""
    exit(2)
  else:
    mod_globals.opt_port      = options.port
    mod_globals.opt_rate      = int(options.rate)
    mod_globals.opt_speed     = int(options.rate)
    auto_macro                = options.macro
    mod_globals.opt_log       = options.logfile
    mod_globals.opt_demo      = options.demo
    mod_globals.opt_si        = options.si
    mod_globals.opt_cfc0      = options.cfc
    mod_globals.opt_n1c       = options.n1c
    auto_dia                  = options.dia


class FileChooser():
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
                android:id="@+id/tx_folder"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentTop="true"
                android:layout_marginTop="20dp"
                android:text="Folder"/>
            <Spinner
                android:id="@+id/sp_folder"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_below="@+id/tx_folder"/>

            <TextView
                android:id="@+id/tx_macro"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_marginTop="20dp"
                android:layout_below="@+id/sp_folder"
                android:text="Macro" />
            <Spinner
                android:id="@+id/sp_macro"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_below="@id/tx_macro"/>

            <Button
                android:id="@+id/bt_exit"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_alignParentLeft="true"
                android:layout_marginTop="50dp"
                android:layout_below="@id/sp_macro"
                android:text="Exit" />

            <Button
                android:id="@+id/bt_start"
                android:layout_width="wrap_content"
                android:layout_height="wrap_content"
                android:layout_marginTop="50dp"
                android:layout_marginLeft="100dp"
                android:layout_below="@id/sp_macro"
                android:layout_toRightOf="@id/bt_exit"
                android:text="Start" />

        </RelativeLayout>

    </ScrollView>

</RelativeLayout>'''
    droid  = None
    folderList = []
    macroList = []

    def newFolderSelected(self):
        self.macroList = []
        fo = self.folder
        self.macroList = [f for f in os.listdir(fo) if os.path.isfile(fo + f) and f.lower().endswith('.cmd')]
        self.droid.fullSetList("sp_macro", self.macroList)

    def eventloop(self):
        while True:
            sf = self.folderList[int(self.droid.fullQueryDetail("sp_folder").result['selectedItemPosition'])]
            if sf != self.folder:
                self.folder = sf
                self.newFolderSelected()
            event = self.droid.eventWait(50).result
            if event == None: continue
            if event["name"] == "click":
                id = event["data"]["id"]
                if id == "bt_start":
                    ma = self.macroList[int(self.droid.fullQueryDetail("sp_macro").result['selectedItemPosition'])]
                    return sf + ma
                if id == "bt_exit":
                    sys.exit()

    def __init__(self):
        fo = './macro/'
        self.folderList = [fo + f + '/' for f in os.listdir(fo) if os.path.isdir(fo + f)]
        self.folder = fo

    def choose(self):
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
                # Python2
                import Tkinter as tk
                import ttk
                import tkFileDialog as filedialog
            except ImportError:
                # Python3
                import tkinter as tk
                import tkinter.ttk as ttk
                import tkFileDialog as filedialog

            root = tk.Tk()
            root.withdraw()

            my_filetypes = [('command files', '.cmd')]

            fname = filedialog.askopenfilename(parent=root,
                                            initialdir="./macro",
                                            title="Please select a file:",
                                            filetypes=my_filetypes)

            return fname

        else:
            try:
                self.droid = android.Android()
                self.droid.fullShow(self.lay)
                self.folderList.insert(0,'./macro/')
                self.droid.fullSetList("sp_folder", self.folderList)
                return self.eventloop()
            finally:
                self.droid.fullDismiss()


def main():

    global auto_macro
    global auto_dia
    global macro
    global var

    mod_utils.chkDirTree()

    init_macro()
    init_var()
    load_macro()
    
    optParser()

    #debug
    #mod_globals.opt_demo = True

    # disable CAN auto-formatting
    mod_globals.opt_cfc0 = True
    
    print 'Opening ELM'
    elm = mod_elm.ELM( mod_globals.opt_port, mod_globals.opt_speed, True )
    elm.currentaddress = '7A'
    elm.currentprotocol = 'can'

    cmd_lines = []
    cmd_ref = 0

    if auto_dia:
        fname = FileChooser().choose()
        if len(fname)>0:
            f = open(fname, 'rt')
            cmd_lines = f.readlines()
            f.close()

    if auto_macro != '':
      if auto_macro in macro.keys():
        play_macro( auto_macro, elm )
      else:
        print 'Error: unknown macro mane:', auto_macro


    while True:
        print var['$addr']+':'+var['$txa']+':'+var['$prompt'] + '#',
        if len(cmd_lines)==0:
            l = raw_input().lower()
        else:
            if cmd_ref<len(cmd_lines):
                l = cmd_lines[cmd_ref].strip()
                cmd_ref += 1
            else:
                l = "exit"
            print l

        if '#' in l:
            l = l.split('#')[0]

        l = l.strip()

        if len(l)==0:
            continue

        if l in ['q', 'quit', 'e', 'exit', 'end']:
            break

        if l in ['h', 'help', '?']:
            print_help ()
            continue

        l_parts = l.split()
        if len(l_parts)>0 and l_parts[0] in ['wait','sleep']:
            try:
                time.sleep(int(l_parts[1]))
                continue
            except:
                pass

        if l in macro.keys():
            play_macro( l, elm )
            continue

        m = re.search('\$\S+\s*=\s*\S+', l)
        if m:
          # variable definition
          r = m.group(0).replace(' ', '').replace('\t', '')
          rl = r.split('=')
          var[rl[0]]=rl[1]
          if rl[0]=='$addr':
            if var['$addr'].upper() in mod_elm.dnat.keys():
              var['$txa'] = mod_elm.dnat[var['$addr'].upper()]
              var['$rxa'] = mod_elm.snat[var['$addr'].upper()]
              elm.currentaddress = var['$addr'].upper()
          continue

        print elm.cmd(l)

if __name__ == '__main__':
  main()




