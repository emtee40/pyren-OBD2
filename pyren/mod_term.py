#!/usr/bin/env python

import sys, os, re
import mod_globals
import mod_elm

try:
    import readline
except:
    pass

os.chdir (os.path.dirname (os.path.realpath (sys.argv[0])))

macro = {}
var = {}
stack = []

auto_macro = ""

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
    dynamicly loaded macro should have .txt extension and plased in ./macro directory
    """

    if mf=='' :
        for root, dirs, files in os.walk("./macro"):
            for mfile in files:
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
          l = re.sub('\\'+vu,var[vu], l)
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

def main():
    
    global macro
    global var
    
    init_macro()
    init_var()
    load_macro()
    
    optParser()
    
    # disable CAN auto-formatting
    mod_globals.opt_cfc0 = True
    
    print 'Opening ELM'
    elm = mod_elm.ELM( mod_globals.opt_port, mod_globals.opt_speed, True )
    elm.currentaddress = '7A'
    elm.currentprotocol = 'can'

    if auto_macro!='':
      if auto_macro in macro.keys():
        play_macro( auto_macro, elm )
      else:
        print 'Error: unknown macro mane:', auto_macro
    
    while True:
        l = raw_input(var['$addr']+':'+var['$txa']+':'+var['$prompt'] + '#').lower()
        
        l = l.strip()
        
        if l in ['q', 'quit', 'e', 'exit', 'end']:
            break
        if l in ['h', 'help', '?']:
            print_help ()
            continue
        if l in macro.keys():
            play_macro( l, elm )
            continue
        m = re.search('\$\S+\s*=\s*\S+', l)
        if m:
          #variable definition
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




