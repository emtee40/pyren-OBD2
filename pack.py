#!/usr/bin/python
import argparse
import glob
import os
import sys
import zipfile


def zipdir(dirname, zip):
    print("Folder process %s" % dirname)
    for root, dirs, files in os.walk(dirname, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            if ".pyc" in filename or ".DS_Store" in filename:  # or ".pyo" in filename:
                continue
            print("Adding source file %s" % filename)
            zip.write(filename)


def pack():
    if not os.path.exists("./Output"):
        os.mkdir("./Output")
    default_file = "pyren.zip"
    if sys.platform[:3] == "win":
        default_file = "pyren_windows.zip"
    else:
        print "Please add python in required sources for works."
        exit(-1)
    # elif sys.platform[:3] == "dar":
    #     default_file = "pyren_macos.zip"
    # elif sys.platform[:3] == "lin":
    #     default_file = "pyren_linux.zip"
    zip = zipfile.ZipFile("./Output/" + default_file, mode="w", compression=zipfile.ZIP_DEFLATED, allowZip64=True)
    files = glob.glob("*.py")
    for file in files:
        print("Adding source file %s" % file)
        zip.write(file)
    if sys.platform[:3] == "win":
        zip.write("./PYREN.BAT")
    # else:
    #     zip.write("./pyren.sh")
    ## Unused or almost...
    # zipdir("./MTCSAVE", zip)          #(auto create)
    # zipdir("./BVMEXTRACTION", zip)    #(need for doc_maker)
    # zipdir("./DocDB_xx", zip)         #(need for doc_maker where xx=language)
    ##
    ## DEPENDS...
    # dir_path = os.path.dirname(os.path.realpath(__file__))
    # os.chdir("/")
    # zipdir("./Python27", zip)
    # os.chdir(dir_path)
    # zipdir("./pyren", zip)
    # zipdir("./EcuDacia", zip)
    # zipdir("./EcuRenault", zip)
    # zipdir("./EcuRsm", zip)
    # zipdir("./Location", zip)
    # zipdir("./NML", zip)
    # zipdir("./Params", zip)
    # zipdir("./Vehicles", zip)
    zip.close()


def genddt2000():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists("/DDT2000data"):
        print ("DDT2000data not found in ROOT /DDT2000data")
        exit(-1)
    default_file = "DDT2000data.zip"
    zip = zipfile.ZipFile("./pyren/" + default_file, mode="w", compression=zipfile.ZIP_DEFLATED, allowZip64=True)
    os.chdir("/DDT2000data")
    if os.path.exists("./ecus"):
        zipdir("./ecus", zip)
    if os.path.exists("./images"):
        zipdir("./images", zip)
    if os.path.exists("./graphics"):
        zipdir("./graphics", zip)
    if os.path.exists("./FlashingTimeAnalysis"):
        zipdir("./FlashingTimeAnalysis", zip)
    if os.path.exists("./failures"):
        zipdir("./failures", zip)
    if os.path.exists("./EDT"):
        zipdir("./EDT", zip)
    if os.path.exists("./vehicles"):
        zipdir("./vehicles", zip)
    if os.path.isfile("./parameters.xml"):
        zip.write("./parameters.xml")
    if os.path.isfile("./default.htm"):
        zip.write("./default.htm")
    os.chdir(dir_path)
    zip.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pack', action="store_true", default=None,
                        help="Pack this as zip for runs PYREN.BAT or pyren.sh")
    parser.add_argument('--gen_ddt_zip', action="store_true", default=None, help="Convert existant DDT2000data to zip")
    args = parser.parse_args()
    if args.pack:
        pack()
    if args.gen_ddt_zip:
        genddt2000()
