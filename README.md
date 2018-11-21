# PYREN
pyren is program for geting diagnostic data from Renault cars by ELM327 adapter. It works in two modes and with two types of databases accordingly.
Compatible with Windows, Linux,  MacOS and Android(only CLIP mode under Android)

## CLIP mode
You may use this mode when you have installed original CLIP software but don't have CLIP hardware

This mode allows you:
* Choose screens languages
* Scan and connect to any ECU of your car
* Read diagnostic data from any ECU
* Read DTC codes from ECUs and get their user friendly descriptions compliant with documentation
* Clear DTC 
* Change configuration (depends on ECU)
* Execute equipment tests (depends on ECU)

## DDT mode
You may use this mode when you have DDT2000 database. It may be run standalone or from CLIP mode. In case of running from CLIP mode it allows to translate some parameters descriptions to choosen language.

This mode allows you:
* Get full control under all ECUs parameters (be very careful in expert mode)
* Save dump of ECU configuration. It may allows you to revert configuration back in case of trouble after configuring
* Compare configurations
* Rollback configuration

## Included tools
* **doc_maker.py** - build diagnostic documentation for your car (require BVMEXTRACTION folder and extracted DocDB_xx.7ze)
* **bus_monitor.py** - catch, parse and shows the content of system frames on your CAN bus.
* **mod_optfile.py** - for exploring CLIP database
* **mod_term.py** - simple terminal
* **mod_ecu.py** - shows list of all parameters, commands and DTCs. Build "PID" CSV file for "Torque PRO" 

# Installation

## Dependencies
* **Python 2.7.xx**
* **ELM327** adapter with FlowControl support (original one or chinese v1.5)
    * **ELM327-USB** - preferred for Windows, Linux and MacOS
    * **ELM327-BT** - not compatible with Android 7.0 and above, use ELM327-WiFi
* **CLIP database** required for CLIP mode, not included (not included, you must own it)
* **DDT2000 database** required for DDT mode, not included (not included, you must own it)

## Installation on Windows

Check that you have CLIP database installed 
```
cd c:\CLIP\Data\GenAppli\
dir 
```
This directory should contains at least the next subdirectories
*EcuRenault
*Location
*Vehicles
*BVMEXTRACTION (required for doc_maker.py)

Install pyren
```
cd c:\CLIP\Data\GenAppli\
git clone git@gitlab.com:py_ren/pyren.git
```
or just download it

https://gitlab.com/py_ren/pyren/-/archive/master/pyren-master.zip

and extract next to directories EcuRenault, Location, Vehicles

You have to get the next directory tree
```
<any work directory>
|- BVMEXTRACTION            #(need for doc_maker)
|- DocDB_xx                 #(need for doc_maker where xx=language) 
|- EcuRenault               #(for CLIP mode)
|- Location                 #(for CLIP mode)
|- Vehicles                 #(for CLIP mode)
|- ecus                     #(for DDT mode)
|- graphics                 #(for DDT mode optional)
|- pyren                    #(pyren)
|   |- pyren.py
...    ...
|   |- <other modules>
|- _pyren_launcher.py       #(universal launcher)
```

## Installation on MacOS and Linux

For running under MacOS or Linux you need just to copy the same directory tree as in Windows installation above

## Installation on Android

1. Install SL4A and Py4A. (https://github.com/kuri65536/python-for-android/blob/master/README.md)
2. Copy DB folders and the pyren into sl4a/scripts. You have to get the next direcotry tree

```
sl4a/scripts
|- EcuRenault           
|- Location             
|- Vehicles             
|- pyren             
|   |- pyren.py
...    ...
|   |- <other modules>
|- _pyren_launcher.py   
```


# User guide

**BE VERY CAREFUL. ONLY YOU RESPONSIBLE FOR ALL YOU ARE DOING WITH YOUR CAR**

## Running from universal launcher

Universal launcher **_pyren_launcher.py** is compatible with any OS. Run it under Windows, MacOS, Linux or Android

## Running from command line

Firs run pyren without options

```
$cd c:\CLIP\Data\GenAppli\pyren
$python.exe ./pyren.py 
usage: pyren.py [-h] [-v] [-p PORT] [-s SPEED] [-r RATE] [-L LANG] [-m CAR]
                [-vv] [-e ECUID] [--si] [--cfc] [--n1c] [--csv] [--csv_only]
                [--csv_human] [--usr_key USR_KEY] [--log LOGFILE] [--scan]
                [--demo] [--dump] [--dev DEV] [--exp] [--can2]

pyRen - python program for diagnostic Renault cars

optional arguments:
  -h, --help         show this help message and exit
  -v, --version      show program's version number and exit
  -p PORT            ELM327 com port name
  -s SPEED           com port speed configured on ELM
                     {38400[default],57600,115200,230400,500000} DEPRECATED
  -r RATE            com port rate during diagnostic session
                     {38400[default],57600,115200,230400,500000}
  -L LANG            language option {RU[default],GB,FR,IT,...}
  -m CAR             number of car model
  -vv, --verbose     show parameter explanations
  -e ECUID           index of ECU, or comma separeted list for DEMO MODE
  --si               try SlowInit first
  --cfc              turn off automatic FC and do it by script
  --n1c              turn off L1 cache
  --csv              save data in csv format
  --csv_only         data doesnt show on screen for speed up
  --csv_human        data saves to csv in readable format
  --usr_key USR_KEY  add user events to log
  --log LOGFILE      log file name
  --scan             scan ECUs even if savedEcus.p file exists
  --demo             for debuging purpose. Work without car and ELM
  --dump             dump responces from all 21xx and 22xxxx requests
  --dev DEV          swith to Development Session for commands from DevList,
                     you should define alternative command for opening the
                     session, like a 1086
  --exp              swith to Expert mode (allow to use buttons in DDT)
  --can2             CAN network connected to pin 13 and pin 12

Available COM ports:
COM3:              
	desc: n/a 
	hwid: n/a

$

```

it shows the list of available options and COM ports

Run pyren with a mandatory option {-p PORT} 

```
$cd c:\CLIP\Data\GenAppli\pyren
$python.exe pyren.py -p COM3
``` 

For the first start you will be prompted to choose a model of car

```
$python.exe pyren.py -p COM3
Opening ELM
Loading ECUs list

1  - B90 SANDERO
2  - J77 MODUS
3  - XDXX MASTER ph2
4  - X95 MEGANEIII/SCENICIII
5  - X85 CLIO III
6  - X24 MASTER PROP.
7  - X81X ESPACE IV
8  - X65 CLIO V6 ph2
9  - X74X LAGUNA II
10 - X70 MAST.PRO.ph2
11 - X44 TWINGO II
12 - X81 P2 ESPACEIV ph2/3/4
13 - XFD TALISMAN/SM6
14 - XFA SCENIC IV
15 - XFF MEGANE IV SEDAN
16 - X79 DUSTER ph2
17 - XHA CAPTUR/KAPTUR BR/IN/RU
18 - XZJ KOLEOS II CN/QM6 CN
19 - XZG KOLEOS II/QM6
20 - XFE KADJAR
N  - <next page>
Choose model :
```

Type the number according your model and press {Enter}. For example, if your car is SANDERO then you have to type '1' and press <Enter>

```
$python.exe pyren.py -p COM3
Opening ELM
Loading ECUs list

1  - B90 SANDERO
2  - J77 MODUS
3  - XDXX MASTER ph2
4  - X95 MEGANEIII/SCENICIII
5  - X85 CLIO III
6  - X24 MASTER PROP.
7  - X81X ESPACE IV
8  - X65 CLIO V6 ph2
9  - X74X LAGUNA II
10 - X70 MAST.PRO.ph2
11 - X44 TWINGO II
12 - X81 P2 ESPACEIV ph2/3/4
13 - XFD TALISMAN/SM6
14 - XFA SCENIC IV
15 - XFF MEGANE IV SEDAN
16 - X79 DUSTER ph2
17 - XHA CAPTUR/KAPTUR BR/IN/RU
18 - XZJ KOLEOS II CN/QM6 CN
19 - XZG KOLEOS II/QM6
20 - XFE KADJAR
N  - <next page>
Choose model : 1 <Enter>
```
Type 'N' and {Enter} for open next page of list

Then pyren starts ECU scanning

```
Choose model :1
Loading data for : B90 SANDERO ../Vehicles/TCOM_139.xml   - 62 ecus loaded
Scanning:53/62 Detected: 4      
```

List of all ecus will be saved in file **savedEcus.p** for not to scan them every time. For connecting to a new car or rescan your car, use option --scan or just delete file savedEcus.p

Also I suggest you to use option **--log** and **--dump** every time you start the pyren.

After first connection to ECU with **--dump** option you will be able to run the pyren offline in demo mode

 ```
$cd c:\CLIP\Data\GenAppli\pyren
$python.exe pyren.py -pp --demo
``` 

(As so **-p** is a mandatory option you may define any value for demo)


