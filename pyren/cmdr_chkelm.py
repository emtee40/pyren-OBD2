#!/usr/bin/env python

import sys, os
import time
    
import mod_globals
import pyren

cmdb = '''
#v1.0 ;AC P; ATZ                   ; Z                  ; reset all
#v1.0 ;AC P; ATE1                  ; E0, E1             ; Echo off, or on*
#v1.0 ;AC P; ATL0                  ; L0, L1             ; Linefeeds off, or on
#v1.0 ;AC  ; ATI                   ; I                  ; print the version ID
#v1.0 ;AC  ; AT@1                  ; @1                 ; display the device description 
#v1.0 ;AC P; ATAL                  ; AL                 ; Allow Long (>7 byte) messages
#v1.0 ;AC  ; ATBD                  ; BD                 ; perform a Buffer Dump
#V1.0 ;ACH ; ATSP4                 ; SP h               ; Set Protocol to h and save it
#v1.0 ;AC  ; ATBI                  ; BI                 ; Bypass the Initialization sequence
#v1.0 ;AC P; ATCAF0                ; CAF0, CAF1         ; Automatic Formatting off, or on*
#v1.0 ;AC  ; ATCFC1                ; CFC0, CFC1         ; Flow Controls off, or on*
#v1.0 ;AC  ; ATCP 01               ; CP hh              ; set CAN Priority to hh (29 bit)
#v1.0 ;AC  ; ATCS                  ; CS                 ; show the CAN Status counts 
#v1.0 ;AC  ; ATCV 1250             ; CV dddd            ; Calibrate the Voltage to dd.dd volts
#v1.0 ;AC  ; ATD                   ; D                  ; set all to Defaults
#v1.0 ;AC  ; ATDP                  ; DP                 ; Describe the current Protocol
#v1.0 ;AC  ; ATDPN                 ; DPN                ; Describe the Protocol by Number
#v1.0 ;AC P; ATH0                  ; H0, H1             ; Headers off*, or on
#v1.0 ;AC  ; ATI                   ; I                  ; print the version ID
#v1.0 ;AC P; ATIB 10               ; IB 10              ; set the ISO Baud rate to 10400*
#v1.0 ;AC  ; ATIB 96               ; IB 96              ; set the ISO Baud rate to 9600      
#v1.0 ;AC  ; ATL1                  ; L0, L1             ; Linefeeds off, or on
#v1.0 ;AC  ; ATM0                  ; M0, M1             ; Memory off, or on
#v1.0 ;AC  ; ATCM 00000000         ; CM hhhhhhhh        ; set the ID Mask to hhhhhhhh
#v1.0 ;AC  ; ATCF 00000000         ; CF hhhhhhhh        ; set the ID Filter to hhhhhhhh
#v1.0 ;AC  ; ATCM 000              ; CM hhh             ; set the ID Mask to hhh
#v1.0 ;AC  ; ATCF 000              ; CF hhh             ; set the ID Filter to hhh
#v1.0 ; C  ; ATMA                  ; MA                 ; Monitor All
#v1.0 ; C  ; ATMR 01               ; MR hh              ; Monitor for Receiver = hh
#v1.0 ; C  ; ATMT 01               ; MT hh              ; Monitor for Transmitter = hh
#v1.0 ;AC  ; ATNL                  ; NL                 ; Normal Length messages*
#v1.0 ;AC  ; ATPC                  ; PC                 ; Protocol Close
#v1.0 ;AC  ; ATR1                  ; R0, R1             ; Responses off, or on*
#v1.0 ;AC  ; ATRV                  ; RV                 ; Read the input Voltage
#v1.0 ;ACH ; ATSP7                 ; SP h               ; Set Protocol to h and save it
#v1.0 ;ACH ; ATSH 00000000         ; SH wwxxyyzz        ; Set Header to wwxxyyzz
#v1.0 ;AC  ; ATSH 001122           ; SH xxyyzz          ; Set Header to xxyyzz
#v1.0 ;AC P; ATSH 012              ; SH xyz             ; Set Header to xyz
#v1.0 ;AC  ; ATSP A6               ; SP Ah              ; Set Protocol to Auto, h and save it
#v1.0 ;AC  ; ATSP 6                ; SP h               ; Set Protocol to h and save it
#v1.0 ;AC P; ATST FF               ; ST hh              ; Set Timeout to hh x 4 msec
#v1.0 ;AC P; ATSW 96               ; SW 00              ; Stop sending Wakeup messages
#v1.0 ;AC P; ATSW 34               ; SW hh              ; Set Wakeup interval to hh x 20 msec
#v1.0 ;AC  ; ATTP A6               ; TP Ah              ; Try Protocol h with Auto search
#v1.0 ;AC  ; ATTP 6                ; TP h               ; Try Protocol h
#v1.0 ;AC P; ATWM 817AF13E         ; WM [1 - 6 bytes]   ; set the Wakeup Message
#v1.0 ;AC P; ATWS                  ; WS                 ; Warm Start (quick software reset)
#v1.1 ;AC P; ATFC SD 300000        ; FC SD [1 - 5 bytes]; FC, Set Data to [...]
#v1.1 ;AC P; ATFC SH 012           ; FC SH hhh          ; FC, Set the Header to hhh
#v1.1 ;AC P; ATFC SH 00112233      ; FC SH hhhhhhhh     ; Set the Header to hhhhhhhh 
#v1.1 ;AC P; ATFC SM 1             ; FC SM h            ; Flow Control, Set the Mode to h
#v1.1 ;AC  ; ATPP FF OFF           ; PP FF OFF          ; all Prog Parameters disabled
#v1.1 ;AC  ; ATPP FF ON            ; PP FF ON           ; all Prog Parameters enabled
#v1.1 ;    ;                       ; PP xx OFF          ; disable Prog Parameter xx
#v1.1 ;    ;                       ; PP xx ON           ; enable Prog Parameter xx 
#v1.1 ;    ;                       ; PP xx SV yy        ; for PP xx, Set the Value to yy
#v1.1 ;AC  ; ATPPS                 ; PPS                ; print a PP Summary
#v1.2 ;AC  ; ATAR                  ; AR                 ; Automatically Receive
#v1.2 ;AC 0; ATAT1                 ; AT0, 1, 2          ; Adaptive Timing off, auto1*, auto2
#v1.2 ;    ;                       ; BRD hh             ; try Baud Rate Divisor hh
#v1.2 ;    ;                       ; BRT hh             ; set Baud Rate Timeout
#v1.2 ;ACH ; ATSPA                 ; SP h               ; Set Protocol to h and save it
#v1.2 ; C  ; ATDM1                 ; DM1                ; monitor for DM1 messages
#v1.2 ; C  ; ATIFR H               ; IFR H, S           ; IFR value from Header* or Source
#v1.2 ; C  ; ATIFR0                ; IFR0, 1, 2         ; IFRs off, auto*, or on
#v1.2 ;AC  ; ATIIA 01              ; IIA hh             ; set ISO (slow) Init Address to hh
#v1.2 ;AC  ; ATKW0                 ; KW0, KW1           ; Key Word checking off, or on*
#v1.2 ; C  ; ATMP 0123             ; MP hhhh            ; Monitor for PGN 0hhhh
#v1.2 ; C  ; ATMP 0123 4           ; MP hhhh n          ; and get n messages
#v1.2 ; C  ; ATMP 012345           ; MP hhhhhh          ; Monitor for PGN hhhhhh
#v1.2 ; C  ; ATMP 012345 6         ; MP hhhhhh n        ; and get n messages
#v1.2 ;AC  ; ATSR 01               ; SR hh              ; Set the Receive address to hh
#v1.3 ;    ; AT@2                  ; @2                 ; display the device identifier
#v1.3 ;AC P; ATCRA 012             ; CRA hhh            ; set CAN Receive Address to hhh
#v1.3 ;AC  ; ATCRA 01234567        ; CRA hhhhhhhh       ; set the Rx Address to hhhhhhhh
#v1.3 ;AC  ; ATD0                  ; D0, D1             ; display of the DLC off*, or on
#v1.3 ;AC  ; ATFE                  ; FE                 ; Forget Events
#v1.3 ;AC  ; ATJE                  ; JE                 ; use J1939 Elm data format*
#v1.3 ;AC  ; ATJS                  ; JS                 ; use J1939 SAE data format
#v1.3 ;AC  ; ATKW                  ; KW                 ; display the Key Words
#v1.3 ;AC  ; ATRA 01               ; RA hh              ; set the Receive Address to hh
#v1.3 ;ACH ; ATSP6                 ; SP h               ; Set Protocol to h and save it
#v1.3 ;ACH ; ATRTR                 ; RTR                ; send an RTR message
#v1.3 ;AC  ; ATS1                  ; S0, S1             ; printing of aces off, or on* 
#v1.3 ;AC  ; ATSP 00               ; SP 00              ; Erase stored protocol
#v1.3 ;AC  ; ATV0                  ; V0, V1             ; use of Variable DLC off*, or on
#v1.4 ;AC  ; ATCEA                 ; CEA                ; turn off CAN Extended Addressing 
#v1.4 ;AC  ; ATCEA 01              ; CEA hh             ; use CAN Extended Address hh
#v1.4 ;AC  ; ATCV 0000             ; CV 0000            ; restore CV value to factory setting
#v1.4 ;AC  ; ATIB 48               ; IB 48              ; set the ISO Baud rate to 4800
#v1.4 ;AC  ; ATIGN                 ; IGN                ; read the IgnMon input level
#v1.4 ;    ;                       ; LP                 ; go to Low Power mode
#v1.4 ;AC  ; ATPB 01 23            ; PB xx yy           ; Protocol B options and baud rate
#v1.4 ;AC  ; ATRD                  ; RD                 ; Read the stored Data
#v1.4 ;AC  ; ATSD 01               ; SD hh              ; Save Data byte hh
#v1.4 ;ACH ; ATSP4                 ; SP h               ; Set Protocol to h and save it
#v1.4 ;AC P; ATSI                  ; SI                 ; perform a Slow (5 baud) Initiation
#v1.4 ;ACH ; ATZ                   ; Z                  ; reset all
#v1.4 ;ACH ; ATSP5                 ; SP h               ; Set Protocol to h and save it
#v1.4 ;AC P; ATFI                  ; FI                 ; perform a Fast Initiation
#v1.4 ;ACH ; ATZ                   ; Z                  ; reset all
#v1.4 ;AC  ; ATSS                  ; SS                 ; use Standard Search order (J1978)
#v1.4 ;AC  ; ATTA 12               ; TA hh              ; set Tester Address to hh
#v1.4 ;ACH ; ATSPA                 ; SP h               ; Set Protocol to h and save it
#v1.4 ;AC  ; ATCSM1                ; CSM0, CSM1         ; Silent Monitoring off, or on* 
#v1.4 ;AC  ; ATJHF1                ; JHF0, JHF1         ; Header Formatting off, or on*
#v1.4 ;AC  ; ATJTM1                ; JTM1               ; set Timer Multiplier to 1*
#v1.4 ;AC  ; ATJTM5                ; JTM5               ; set Timer Multiplier to 5
#v1.4b;AC  ; ATCRA                 ; CRA                ; reset the Receive Address filters
#v2.0 ;AC  ; ATAMC                 ; AMC                ; display Activity Monitor Count
#v2.0 ;AC  ; ATAMT 20              ; AMT hh             ; set the Activity Mon Timeout to hh
#v2.1 ;AC  ; ATCTM1                ; CTM1               ; set Timer Multiplier to 1*
#v2.1 ;AC  ; ATCTM5                ; CTM5               ; set Timer Multiplier to 5
#v2.1 ;ACH ; ATZ                   ; Z                  ; reset all
'''
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

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
    from serial.tools  import list_ports
  except ImportError:
    sys.exit()
    
from mod_elm       import ELM

def main():
  
  pyren.optParser()
  
  good = 0
  total= 0
  pycom= 0
  vers = ''
  res  = ''
  
  print 'Opening ELM'
  elm = ELM( mod_globals.opt_port, mod_globals.opt_speed, mod_globals.opt_log )
  elm.portTimeout = 5
  
  for st in cmdb.split('#'):
    cm = st.split(';')

    if len(cm)>1:
      if mod_globals.os == 'android' and 'A' not in cm[1].upper(): continue
      if mod_globals.os != 'android' and 'C' not in cm[1].upper(): continue
      
      if len(cm[2].strip()):
        
        res = elm.send_raw(cm[2])
        
        #print res
        
        if 'H' in cm[1].upper(): continue
        total += 1
        
        if '?' in res:
          chre = '[FAIL]'
          if 'P' in cm[1].upper(): pycom += 1
        elif 'TIME' in res:
          chre = '[TIMEOUT]'
        else:
          chre = '[OK]'
          good += 1
          vers = cm[0]
        
        print "%5s %10s %6s"%(cm[0], cm[2], chre)
        sys.stdout.flush
        
  if pycom>0:
    res = '\n\n\nUncompatible adapter on ARM core \n pyren would not work with it \n\n\n'
  res = res + '\n\n\nResult: '+str(good)+' from '+str(total)+'\n Max version:'+vers+'\n\n\n\n\n\n\n'
  
  elm.lastMessage = res

if __name__ == '__main__':  
  main()


