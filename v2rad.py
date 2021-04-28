"""Timer translator

This script will receive times for a TH 990 and translate them
to a RA display. Display expects time in fffssm format.
Times above 10 Min are not supported by our test RA display
This software works well with com0com on Windows.
Run the command with no options to list available COM ports
Run the command with an input com port and an output com port
to process data and forward it to the display

Usage:
    v2rad.py
    v2rad.py COM COMDISPLAY [options]

Options:
    -h, --help                    Show this screen
    --version                     Show version
    -b BAUD --baud=BAUD           Serial speed [default: 9600]
    -s STOP --stopbits=STOP       Serial stopbits [default: 1]
    -e BYTES --bytsize=BYTES      Serial bytesize [default: 8]
    -p PARITY --parity PARITY     Serial parity [default: N]
    -t TIMEOUT --timeout TIMEOUT  Serial timeout [default: 3]

"""

import re
import serial
from docopt import docopt
from serial.tools.list_ports import comports

# Setup Regex for incoming times
searchStr = r".*?L0\tA\s*(.*)\t\r\n"

def listPorts():
    '''
    List all COM ports or Device Paths
    Print the list to the console
    '''
    print("Available COM Ports:")
    ports = comports()
    for port, desc, hwid in sorted(ports):
            print(f"{port}: {desc} [{hwid}]")

def setupSerial(args, comPort):
    '''
    Setup the serial connection paremeters
    Input is a dictionary of command line arguments
    Returns a serial object
    '''
    ser = serial.Serial()
    ser.port = comPort
    ser.baudrate = int(args.get("--baud", 9600))
    ser.stopbits= int(args.get("--stopbits", 1))
    ser.bytesize= int(args.get("--bytezise", 8))
    ser.parity= args.get("--parity", 'N')
    ser.timeout= int(args.get("--timeout", 8))
    ser.xonxoff=0
    ser.rtscts=0
    return ser

def processTimesLoop(ser, serDisplay):
    print("Waiting For Data...")
    print("Press <CTRL> + C twice to stop")
    while True:
        line = ser.readline()
        strLine = line.decode("utf-8")
        if strLine:
            searchObj = re.search(searchStr, strLine)
            try:
                if searchObj.group(1):
                    strTime = str(searchObj.group(1)).zfill(7)
                    minInt = int(strTime[0])
                    displayTime = strTime[-6:-3] + strTime[-3:]
                    print(f"Processing Time {displayTime}")
                    if minInt == 0:
                        byteTime = f'{displayTime[::-1]}'.encode()
                        serDisplay.write(b'\x80' + byteTime + b'\r')
                    else:
                        print("Times over 10 min not supported by display, skipping")
                        print("Waiting For Data...")
            except AttributeError:
                print("Issue processing line:", strLine)
        line = None
        strLine = None

if __name__ == '__main__':
    arguments = docopt(__doc__, version='1.0')
    if not arguments['COM']:
        # List ports if none is given
        listPorts()
    else:
        ser = setupSerial(arguments, arguments['COM'])
        serDisplay = setupSerial(arguments, arguments['COMDISPLAY'])
        # Attempt to open the serial device
        # Exit if that is not successful
        try:
            ser.open()
            serDisplay.open()
            print("Ports Opened")
        except serial.SerialException as e:
            print(f"Could not open serial port {ser.name}: {e}")
            sys.exit(1)
        # Recieve and process data
        processTimesLoop(ser, serDisplay)