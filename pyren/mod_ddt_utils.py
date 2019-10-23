#!/usr/bin/env python

import os
import xml.etree.ElementTree as et
import mod_globals
import mod_db_manager

from operator import itemgetter
from copy import deepcopy

if mod_globals.os != 'android':
    import serial

try:
    import cPickle as pickle
except:
    import pickle

def searchddtroot():
    if not os.path.exists('../DDT2000data/ecus'):
        mod_globals.ddtroot = '..'
    else:
        mod_globals.ddtroot = '../DDT2000data'
    return

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
        if not os.path.isfile("../settings.p"):
            self.save()

        f = open('../settings.p', 'rb')
        tmp_dict = pickle.load(f)
        f.close()
        self.__dict__.update(tmp_dict)

    def save(self):
        f = open('../settings.p', 'wb')
        pickle.dump(self.__dict__, f)
        f.close()

def multikeysort(items, columns):
    comparers = [ ((itemgetter(col[1:].strip()), -1) if col.startswith('-') else (itemgetter(col.strip()), 1)) for col in columns]
    def comparer(left, right):
        for fn, mult in comparers:
            result = cmp(fn(left), fn(right))
            if result:
                return mult * result
        else:
            return 0
    return sorted(items, cmp=comparer)

def getPortList():
    ret = []
    iterator = sorted(list(serial.tools.list_ports.comports()))
    for port, desc, hwid in iterator:
        try:
            de = unicode(desc.encode("ascii", "ignore"))
            ret.append(port + u';' + de)
        except:
            ret.append(port + ';')
    if '192.168.0.10:35000;WiFi' not in ret:
        ret.append('192.168.0.10:35000;WiFi')
    return ret

def loadECUlist():

    # make or load eculist
    print "Loading eculist"
    eculistcache = os.path.join(mod_globals.cache_dir, "ddt_eculist.p")

    if os.path.isfile(eculistcache):  # if cache exists
        eculist = pickle.load(open(eculistcache, "rb"))  # load it #dbaccess
    else:

        # open xml
        eculistfilename = 'ecus/eculist.xml'
        #if not os.path.isfile(eculistfilename):
        if not mod_db_manager.file_in_ddt(eculistfilename):
            print "No such file: "+eculistfilename
            return None

        ns = {'ns0': 'http://www-diag.renault.com/2002/ECU',
              'ns1': 'http://www-diag.renault.com/2002/screens'}

        tree = et.parse(mod_db_manager.get_file_from_ddt(eculistfilename))
        root = tree.getroot()

        eculist = {}
        functions = root.findall("Function")
        if len(functions):
            for function in functions:
                Address = hex(int(function.attrib["Address"])).replace("0x", "").zfill(2).upper()
                eculist[Address] = {}
                FuncName = function.attrib["Name"]
                targets = function.findall("Target")
                eculist[Address]["FuncName"] = FuncName
                eculist[Address]["targets"] = {}
                if len(targets):
                    for target in targets:
                        href = target.attrib["href"]
                        eculist[Address]["targets"][href] = {}
                        pjc = target.findall("Projects")
                        if len(pjc) > 0:
                            pjcl = [elem.tag.upper() for elem in pjc[0].iter()][1:]
                        else:
                            pjcl = []
                        eculist[Address]["targets"][href]['Projects'] = pjcl
                        ail = []
                        ais = target.findall("ns0:AutoIdents", ns)
                        if len(ais)==0:
                            ais = target.findall("AutoIdents")
                        if len(ais):
                            for ai in ais:
                                AutoIdents = ai.findall("ns0:AutoIdent", ns)
                                if len(AutoIdents)==0:
                                    AutoIdents = ai.findall("AutoIdent")
                                if len(AutoIdents):
                                    for AutoIdent in AutoIdents:
                                        air = {}
                                        air['DiagVersion'] = AutoIdent.attrib["DiagVersion"].strip()
                                        air['Supplier'] = AutoIdent.attrib["Supplier"].strip()
                                        air['Soft'] = AutoIdent.attrib["Soft"].strip()
                                        air['Version'] = AutoIdent.attrib["Version"].strip()
                                        ail.append(air)
                        eculist[Address]["targets"][href]['AutoIdents'] = ail
        pickle.dump(eculist, open(eculistcache, "wb"))  # and save cache #dbaccess

    return eculist


class ddtProjects():
    def __init__(self):
        self.proj_path = 'vehicles/projects.xml'

        self.plist = []

        if not mod_db_manager.file_in_ddt(self.proj_path):
            return

        tree = et.parse(mod_db_manager.get_file_from_ddt(self.proj_path))
        root = tree.getroot()

        DefaultAddressing = root.findall('DefaultAddressing')
        if DefaultAddressing:
            defaddrsheme = DefaultAddressing[0].text

        Manufacturer = root.findall('Manufacturer')
        if Manufacturer:
            for ma in Manufacturer:
                name = ma.findall('name')
                if name:
                    ma_name = ma[0].text
                else:
                    ma_name = 'Unknown'

                pl_ma = {}
                pl_ma['name'] = ma_name
                pl_ma['list'] = []

                project = ma.findall('project')
                if project:
                    for pr in project:
                        cartype = {}
                        addressing = pr.findall('addressing')
                        if addressing:
                            cartype['addr'] = addressing[0].text
                        else:
                            cartype['addr'] = defaddrsheme


                        if 'code' in pr.attrib:
                            cartype['code'] = pr.attrib['code']
                        else:
                            cartype['code'] = ''

                        if 'name' in pr.attrib:
                            cartype['name'] = pr.attrib['name']
                        else:
                            cartype['name'] = ''

                        if 'segment' in pr.attrib:
                            cartype['segment'] = pr.attrib['segment']
                        else:
                            cartype['segment'] = ''

                        pl_ma['list'].append(cartype)

                self.plist.append(pl_ma)

class ddtAddressing():
    def __init__(self, filename ):
        self.addr_path = 'vehicles/' + filename

        self.alist = []

        if not mod_db_manager.file_in_ddt(self.addr_path):
            return

        tree = et.parse(mod_db_manager.get_file_from_ddt(self.addr_path))
        root = tree.getroot()

        ns = {'ns0': 'DiagnosticAddressingSchema.xml',
              'ns1': 'http://www.w3.org/XML/1998/namespace'}

        Function = root.findall('ns0:Function', ns)
        if Function:
            for fu in Function:
                fun = {}
                fun['Address'] = int(fu.attrib['Address'])
                fun['Name'] = fu.attrib['Name']

                baudRate = fu.findall('ns0:baudRate',ns)
                if baudRate:
                    fun['baudRate'] = baudRate[0].text
                else:
                    fun['baudRate'] = '0'

                Names = fu.findall('ns0:Name',ns)
                fun['longname'] = {}
                if Names:
                    for Name in Names:
                        fun['longname'][Name.attrib.values()[0]] = Name.text

                XId = fu.findall('ns0:XId',ns)
                fun['XId'] = ''
                if XId:
                    fun['XId'] = XId[0].text

                RId = fu.findall('ns0:RId',ns)
                fun['RId'] = ''
                if XId:
                    fun['RId'] = RId[0].text

                RId = fu.findall('ns0:RId',ns)
                fun['RId'] = ''
                if XId:
                    fun['RId'] = RId[0].text

                ISO8 = fu.findall('ns0:ISO8',ns)
                fun['ISO8'] = ''
                if ISO8:
                    fun['ISO8'] = ISO8[0].text

                protocolList = fu.findall('ns0:ProtocolList',ns)
                if protocolList:
                    protocols = protocolList[0].findall('ns0:Protocol',ns)
                    for proto in protocols:
                        fun['protocol'] = proto.attrib['Code']
                        self.alist.append(fun)
                        tmp = deepcopy(fun)
                        fun = tmp

                else:
                    fun['protocol'] = ''
                    self.alist.append(fun)

                fun['xml'] = ''
