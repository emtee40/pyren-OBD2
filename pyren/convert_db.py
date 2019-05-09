#!/usr/bin/python

import glob
import os
import pickle
import sys
import zipfile
from StringIO import StringIO

from  mod_optfile import *

if __name__ == "__main__":
    zipoutput = StringIO ()
    
    if len (sys.argv) < 2:
        print "Usage : convert_db.py [path/to/GenAppli]"
        exit ()
    
    inputpath = sys.argv[1]
    ecudir = os.path.join (inputpath, "EcuRenault")
    vehicledir = os.path.join (inputpath, "Vehicles")
    locationdir = os.path.join (inputpath, "Location")
    
    ecufiles = glob.glob (os.path.join (ecudir, "*.xml"))
    fbsessionfiles = glob.glob (os.path.join (ecudir, "Sessions", "FB*.xml"))
    fbsessionfiles += glob.glob (os.path.join (ecudir, "Sessions", "FG*.xml"))
    fgsessionfiles = glob.glob (os.path.join (ecudir, "Sessions", "SG*.xml"))
    vehiclesfiles = glob.glob (os.path.join (vehicledir, "*.xml"))
    locationsfiles = glob.glob (os.path.join (locationdir, "*.bqm"))
    scnerariosfiles = glob.glob (os.path.join (ecudir, "Scenarios", "*.xml"))
    
    with zipfile.ZipFile (zipoutput, mode='w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for vf in scnerariosfiles:
            print "Processing file ", vf
            f = open (vf, "r")
            data = f.read ()
            zf.writestr (os.path.join ("EcuRenault", "Scenarios", os.path.basename (vf)), str (data))
        
        for vf in vehiclesfiles:
            print "Processing file ", vf
            f = open (vf, "r")
            data = f.read ()
            zf.writestr (os.path.join ("Vehicles", os.path.basename (vf)), str (data))
        
        for vf in ecufiles:
            print "Processing file ", vf
            f = open (vf, "r")
            data = f.read ()
            zf.writestr (os.path.join ("EcuRenault", os.path.basename (vf)), str (data))
        
        for vf in fbsessionfiles:
            print "Processing file ", vf
            f = open (vf, "r")
            data = f.read ()
            zf.writestr (os.path.join ("EcuRenault", "Sessions", os.path.basename (vf)), str (data))
        
        for vf in locationsfiles:
            print "Processing file ", vf
            try:
                optf = optfile (vf)
            except:
                print "Skipping file ", vf
                continue
            data = pickle.dumps (optf.dict)
            zf.writestr (os.path.join ("Location",
                                       os.path.basename (vf).replace (".bqm", ".p")), str (data))
        
        for vf in fgsessionfiles:
            print "Processing file ", vf
            try:
                optf = optfile (vf)
            except:
                print "Skipping file ", vf
                continue
            data = pickle.dumps (optf.dict)
            zf.writestr (os.path.join ("EcuRenault", "Sessions",
                                       os.path.basename (vf).replace ("FG", "UG").replace (".xml", ".p")), str (data))
    
    with open ("pyrendata.zip", "wb") as zf:
        zf.write (zipoutput.getvalue ())
