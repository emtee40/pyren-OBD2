# pyren
pyren is a program for getting diagnostic data from Renault cars by ELM327 adapter. It works in two modes and with two types of databases accordingly.
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

Getting started video
https://www.youtube.com/watch?v=DazsvlnLCoA

## Supported cars with CLIP DB v202

| id  | ISO   | CAN1  | CAN2  | Vehicle               | Platform | PyRen | DocDB |
|-----|-------|-------|-------|-----------------------|----------|-------|-------|
| 005 | 7-15  | ----  | ----  | MEGANE/SCENIC         | X64      | no    | no    |
| 008 | 7-15  | 6-14  | ----  | CLIO II               | X65      | yes*  | no    |
| 010 | 7-15  | ----  | ----  | LAGUNA                | X56      | no    | no    |
| 013 | 7-15  | 6-14  | ----  | KANGOO                | X76      | yes*  | no    |
| 026 | 7-15  | ----  | ----  | MASTER                | X70      | no    | no    |
| 034 | 7-15  | 6-14  | ----  | TWINGO ph2            | X06      | yes*  | no    |
| 035 | 7-15  | ----  | ----  | LAGUNA ph2            | X56      | no    | no    |
| 054 | 7-15  | ----  | ----  | ESPACE                | X66      | no    | no    |
| 064 | 7-15  | ----  | ----  | CLIO V6               | X65      | no    | no    |
| 066 | 7-15  | ----  | ----  | TRAFIC II             | X83      | no    | no    |
| 067 | 7-15  | 6-14  | ----  | CLIO II ph2/3/4       | X65      | yes*  | no    |
| 069 | 7-15  | ----  | ----  | AVANTIME              | X66      | no    | no    |
| 073 | 7-15  | 6-14  | ----  | KANGOO MUX            | X76      | yes*  | no    |
| 077 | 7-15  | 6-14  | ----  | THALIA/SYMBOL         | X65      | yes*  | no    |
| 086 | 7-15  | 6-14  | 13-12 | MEGANE II             | X84      | yes   | no    |
| 088 | 7-15  | ----  | ----  | CLIO V6 ph2           | X65      | no    | no    |
| 107 | 7-15  | ----  | ----  | MASTER PRO            | X24      | no    | no    |
| 108 | 7-15  | 6-14  | 13-12 | SCENIC II             | X84      | yes   | no    |
| 110 | 7-15  | ----  | ----  | MASTER ph2            | XDX      | no    | no    |
| 111 | 7-15  | 6-14  | 13-12 | MODUS                 | J77      | yes   | no    |
| 113 | 7-15  | 6-14  | 13-12 | CLIO III              | X85      | yes   | no    |
| 114 | 7-15  | ----  | ----  | MASTER PRO ph2        | X70      | no    | no    |
| 116 | 7-15  | 6-14  | ----  | LAGUNA II             | X74      | yes   | no    |
| 117 | 7-15  | 6-14  | 13-12 | ESPACE IV             | X81      | yes   | no    |
| 118 | 7-15  | 6-14  | 13-12 | VEL SATIS             | X73      | yes   | no    |
| 119 | 7-15  | 6-14  | 13-12 | VEL SATIS ph2         | X73      | yes   | no    |
| 121 | 7-15  | 6-14  | 13-12 | LAGUNA II ph2         | X74      | yes   | no    |
| 122 | 7-15  | 6-14  | ----  | SAMSUNG SM7           | ---      | yes** | no    |
| 123 | 7-15  | 6-14  | ----  | SAMSUNG SM5 05MY      | ---      | yes** | no    |
| 124 | 7-15  | ----  | ----  | CLIO II ph2/3         | X65      | yes   | no    |
| 125 | 7-15  | ----  | ----  | SAMSUNG SM3           | ---      | yes** | no    |
| 126 | 7-15  | 6-14  | ----  | SAMSUNG SM3 06MY      | ---      | yes** | no    |
| 127 | 7-15  | ----  | ----  | SAMSUNG SM5           | ---      | yes** | no    |
| 128 | 7-15  | 6-14  | 13-12 | TWINGO II             | X44      | yes   | no    |
| 129 | 7-15  | 6-14  | 13-12 | ESPACE IV ph2/3/4     | X81      | yes   | no    |
| 130 | 7-15  | 6-14  | 13-12 | TRAFIC II ph2/3       | X83      | yes   | no    |
| 131 | 7-15  | 6-14  | 13-12 | MASTER ph3            | X70      | yes   | no    |
| 132 | ----  | 6-14  | 13-12 | LAGUNA III            | X91      | yes   | yes   |
| 133 | 7-15  | 6-14  | 13-12 | MASTER PRO ph3        | X24      | yes   | no    |
| 134 | 7-15  | 6-14  | 13-12 | KOLEOS/QM5            | H45      | yes   | no    |
| 135 | 7-15  | 6-14  | 13-12 | KANGOO II             | X61      | yes   | no    |
| 136 | 7-15  | 6-14  | 13-12 | LOGAN                 | X90      | yes   | no    |
| 137 | 7-15  | 6-14  | ----  | SAMSUNG SM5 07MY      | ---      | yes** | no    |
| 138 | ----  | 6-14  | 13-12 | MEGANE III/SCENIC III | X95      | yes   | yes   |
| 139 | 7-15  | 6-14  | 13-12 | SANDERO               | B90      | yes   | no    |
| 140 | 7-15  | 6-14  | ----  | SAMSUNG SM7 07MY      | ---      | yes   | no    |
| 141 | 7-15  | 6-14  | ----  | THALIA/SYMBOL II      | L35      | yes   | no    |
| 142 | ----  | 6-14  | 13-12 | FLUENCE/MEGANE        | X38      | yes   | yes   |
| 143 | ----  | 6-14  | 13-12 | LATITUDE              | X43      | yes   | yes   |
| 144 | 7-15  | 6-14  | 13-12 | MASTER III            | X62      | yes   | yes   |
| 145 | 7-15  | 6-14  | 13-12 | WIND                  | W33      | yes   | no    |
| 146 | 7-15  | 6-14  | 13-12 | DUSTER                | X79      | yes   | no    |
| 147 | 7-15  | 6-14  | 13-12 | KANGOO ZE ph2         | X61      | yes   | yes   |
| 148 | ----  | 6-14  | 13-12 | SAMSUNG SM7 L47       | X47      | yes   | yes   |
| 149 | ----  | 6-14  | 13-12 | LODGY                 | X92      | yes   | yes   |
| 150 | ----  | 6-14  | 13-12 | DOKKER/KANGOO         | X67      | yes   | yes   |
| 151 | ----  | 6-14  | 13-12 | LOGAN II/SANDERO II   | X52      | yes   | yes   |
| 152 | 7-15  | 6-14  | ----  | TWIZY                 | X09      | yes   | no    |
| 154 | ----  | 6-14  | 13-12 | ZOE                   | X10      | yes   | yes   |
| 155 | ----  | 6-14  | 13-12 | CLIO IV               | X98      | yes   | yes   |
| 156 | ----  | 6-14  | 13-12 | CAPTUR                | X87      | yes   | yes   |
| 157 | 7-15  | 6-14  | ----  | CLIO II ph6           | X65      | yes   | no    |
| 158 | 7-15  | 6-14  | 13-12 | TRAFIC III            | X82      | yes   | yes   |
| 159 | ----  | 6-14  | 13-12 | DUSTER ph2            | X79      | yes   | yes   |
| 160 | ----  | 6-14  | 13-12 | TWINGO III            | X07      | yes   | yes   |
| 161 | ----  | 6-14  | 13-12 | ESPACE V              | XFC      | yes   | yes   |
| 162 | 7-15  | 6-14  | ----  | KANGOO VLL            | X76      | yes   | no    |
| 163 | ----  | 6-14  | 13-12 | KWID                  | XBA      | yes   | yes   |
| 164 | ----  | 6-14  | 13-12 | KADJAR                | XFE      | yes   | yes   |
| 165 | ----  | 6-14  | 13-12 | KAPTUR                | XHA      | yes   | yes   |
| 166 | ----  | 6-14  | 13-12 | TALISMAN              | XFD      | yes   | yes   |
| 167 | ----  | 6-14  | 13-12 | SCENIC IV             | XFA      | yes   | yes   |
| 168 | ----  | 6-14  | 13-12 | MEGANE IV             | XFB      | yes   | yes   |
| 169 | ----  | 6-14  | 13-12 | KADJAR CN             | XZH      | yes   | yes   |
| 170 | ----  | 6-14  | 13-12 | KOLEOS II             | XZG      | yes   | yes   |
| 171 | ----  | 6-14  | 13-12 | KOLEOS II CN          | XZJ      | yes   | yes   |
| 173 | ----  | 6-14  | 13-12 | MEGANE IV SEDAN       | XFF      | yes   | yes   |
| 174 | 7-15  | 6-14  | ----  | ALASKAN               | D23      | yes   | no    |
| 175 | ----  | 6-14  | 13-12 | KWID BR               | XBB      | yes   | yes   |
| 176 | ----  | 6-14  | 13-12 | ALPINE A110           | XEF      | yes   | yes   |
| 177 | ----  | 6-14  | 13-12 | DUSTER ph3            | XJD      | yes   | yes   |
| 178 | ----  | 6-14  | ----  | CLIO V                | XJA      | yes   | yes   |
| 179 | ----  | 6-14  | 13-12 | ARKANA                | XJC      | yes   | yes   |
| 180 | ----  | 6-14  | 13-12 | TRIBER                | XBC      | yes   | yes   |
| 181 | ----  | 6-14  | ----  | CAPTUR II             | XJB      | yes   | yes   |
| 182 | ----  | 6-14  | ----  | CAPTUR II CN          | XJE      | yes   | yes   |
| 183 | ----  | 6-14  | ----  | MEGANE IV ph2         | XFB      | yes   | yes   |
| 184 | ----  | 6-14  | ----  | ESPACE V ph2          | XFC      | yes   | yes   |
| 185 | ----  | 6-14  | ----  | TALISMAN ph2          | XFD      | yes   | yes   |
| 186 | ----  | 6-14  | ----  | NOUVELLE ZOE          | X10      | yes   | yes   |
| 187 | ----  | 6-14  | ----  | ARKANA CN             | XJH      | yes   | yes   |
| 188 | ----  | 6-14  | ----  | SAMSUNG XM3           | XJL      | yes   | yes   |
| 189 | ----  | 6-14  | 13-12 | CITY K-ZE             | XBG      | yes   | yes   |
| 190 | ----  | 6-14  | 13-12 | NEW KANGOO LS         | XJK      | yes   | yes   |
| 191 | ----  | 6-14  | ----  | NEW SANDERO/LOGAN     | XJF      | yes   | yes   |
| 192 | ----  | 6-14  | ----  | MEGANE IV SEDAN ph2   | XFF      | yes   | yes   |

&ast; Only Siemens Sirius 32N supported

&ast;&ast; ISO2 Network pin 13 (K), pin 12 (L)

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
* EcuRenault
* Location
* Vehicles

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
|- _pyren_launcher.py       #(universal launcher)
|- BVMEXTRACTION            #(need for doc_maker)
|- DocDB_xx                 #(need for doc_maker where xx=language) 
|- EcuRenault               #(for CLIP mode)
|- Location                 #(for CLIP mode)
|- Vehicles                 #(for CLIP mode)
|- DDT2000data              #(for DDT mode)
|   |- ecus                 #(for DDT mode)
|   |- graphics             #(for DDT mode)
|   |- vehicles             #(for DDT mode)
|
|- pyren                    #(pyren)
|   |- pyren.py
...    ...
|   |- <other modules>
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
                [-vv] [-e ECUID] [-e CAR] [--si] [--cfc] [--n1c] [--csv] 
                [--csv_only] [--csv_human] [--usr_key USR_KEY] [--log LOGFILE] 
                [--scan] [--demo] [--dump] [--dev DEV] [--exp] [--can2]

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
  -e CAR             number of car model for DEMO MODE
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
  --can2             CAN network connected to pin 13 (H) and pin 12 (L)

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


