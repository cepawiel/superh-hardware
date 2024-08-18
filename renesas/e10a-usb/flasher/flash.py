#!/usr/bin/python3

# To put E10A-USB into programing mode set SW1=0
# Manuals all strongly suggest changing this switch while plugged in will
# cause damage. The device should show up as 0x045B:0x000D in programing
# mode and 0x045B:0x0013 when SW1=1 & programed with an E10A-USB FW. 

# Required Files from HEW/E10A-USB Installation Directory:
#   uGen2215u.cde, Genm2215U.cde, Genw2215u.cde:
#       Don't know exactly what each of these do indivually, but they were 
#       sent over the USB bus in the order listed. Each FW Updater tool
#       includes a copy, but they are all an exact byte match.
#   
#   E1adp.mot:    
#       This is the E10A-USB firmware in srec format. 
#
#
#
# Usage:
#   If pointing to FW update folder, this will search the path for the necessary
#   files to flash the device.
#       flash.py -p <e10a/path/to/setup>/SetupTool
#
#   To specify specific firmware file
#       flash.py -f <path/to/firmwares>/E1adp.mot
#
#   By default the script will search the working directory as well as the
#   directory where the script is stored for the required files. So feel free
#   to copy the script into the folder or just `cd` into the folder and run
#   the script from its stored location.
#

import bincopy
import argparse
import usb.core
import usb.util
import os

class E10AFlasher:
    EP_OUT = 0x01
    EP_IN  = 0x82

    def __init__(self, uGen2215u: bytearray, Genm2215U: bytearray, Genw2215u: bytearray):
        self.uGen = uGen2215u
        self.Genm = Genm2215U
        self.Genw = Genw2215u

        self.dev = usb.core.find(idVendor=0x045B, idProduct=0x000D)

        if self.dev is None:
            raise ValueError('Device not found: unplug E10A-USB, move SW1 to 0, and replug')

        self.dev.set_configuration()
        print(self.dev)

    def tx(self, data : bytearray, checksum=False):
        print("Writing {} bytes".format(len(data)))
        data = bytes(data)
        if checksum:
            data = self.append_checksum(data)
        self.dev.write(self.EP_OUT, data, 1000)

    def rx(self, count : int):
        print("Reading {} bytes".format(count))
        return self.dev.read(self.EP_IN, count, 1000)

    def rx_expect(self, expect: bytearray):
        read = self.rx(len(expect))
        if expect == read:
            raise ValueError("Expected {}, Got {}", expect, read)
        
    def append_checksum(self, packet: bytearray):
        checksum = 0x100 - (sum(packet) & 0xFF)
        # print(hex(checksum))
        return packet + checksum.to_bytes(1, byteorder='big')

    def load_kernels(self):
        print("Writing Flash Write Kernel")
        self.tx([0x55])
        self.rx_expect([0xAA])
        self.tx([0x06, 0x40, 0x01, 0x01])
        self.rx_expect([0xAA])
        self.tx([0x08])
        self.tx([0x82])
        self.rx_expect([0xAA])

        # load inital program
        self.tx(self.uGen, checksum=True)
        self.rx_expect([0xAA])
        
        self.tx([0x3A])
        self.rx_expect([0x11])
        self.tx([0x3A])
        self.rx_expect([0x06])
        self.tx([0x10, 0x04, 0x30, 0x31, 0x32, 0x36], checksum=True)
        self.rx_expect([0x06])
        self.tx([0x11, 0x01, 0x00], checksum=True)
        self.rx_expect([0x06])
        self.tx([0x3F,0x07, 0x06, 0x40, 0x06, 0x40, 0x01, 0x01, 0x01], checksum=True)
        self.rx_expect([0x06])
        self.tx([0x06])
        self.rx_expect([0x06])
        self.tx([0x27])
        # for some reason trying to recv this all at once fails
        # perhaps something to do with how its queued - USB stuff?
        self.rx_expect([0x37, 0x02])
        self.rx_expect([0x04, 0x00])
        self.rx_expect([0xC3])
        self.tx([0x40])
        self.rx_expect([0x06])

        # 2nd program
        k2 = 0x000006A2.to_bytes(4, byteorder='big') + self.Genm
        self.tx(k2, checksum=True)

        self.rx_expect([0x06])
        self.tx([0x4D])
        self.rx_expect([0x06])
        self.tx([0x43])
        self.rx_expect([0x06])

        # 3rd program
        k3 = 0x0000059B.to_bytes(4, byteorder='big') + self.Genw
        self.tx(k3, checksum=True)
        self.rx_expect([0x06])

        self.tx([0x4F])
        self.rx_expect([0x5F, 0x02, 0x03, 0x00, 0x9C])

    def write_firmware(self, fw: bytearray):
        print("Writing Firmware!")
        print("{} bytes".format(len(fw)))

        for address in range(0, len(fw), 1024):
            chunk = fw[address: address + 1024]
            print("Writing {} bytes at 0x{:X}".format(len(chunk), address))

            if len(chunk) < 1024:
                print("\tPadding with 0xFF to 1024")
                while len(chunk) < 1024:
                    chunk += 0xFF.to_bytes(1, byteorder='big')
                print("\tNew Size: {}".format(len(chunk)))

            if chunk.count(0xFF) == 1024:
                print("\tBlank Section, skipping")
                continue

            cmd = 0x50.to_bytes(1, byteorder='big')        
            address_bytes = address.to_bytes(4, byteorder='big')

            packet = cmd + address_bytes + chunk

            self.tx(packet, checksum=True)
            self.rx_expect([0x06])

        # Finish Writing
        self.tx(bytes([0x50, 0xFF, 0xFF, 0xFF, 0xFF]), checksum=True)

def load_file(path):
    ext = os.path.splitext(path)[1]
    if ext == '.cde':
        with open(path, "rb") as fd:
            return fd.read()
    elif ext == '.mot':
        f = bincopy.BinFile(path)
        return f.as_binary()
    else:
        print("Unknown file format for {}".format(path))
        return None

def search_load_file(name, search_path=[]):
    for dir in search_path:
        path = os.path.join(dir, name)
        if os.path.isfile(path):
            print("Found {} in {}".format(name, dir))
            return load_file(path)
    print("Unable to locate {} in search path".format(name))
    return None

def dir_path(s):
    if os.path.isdir(s):
        return s
    else:
        raise NotADirectoryError(s)
    
def file_path(s):
    if os.path.isfile(s):
        return s
    else:
        raise FileNotFoundError(s)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', type=dir_path)
    parser.add_argument('--uGen2215u', type=file_path)
    parser.add_argument('--Genm2215U', type=file_path)
    parser.add_argument('--Genw2215u', type=file_path)
    parser.add_argument('-f', '--firmware', type=file_path)

    args = parser.parse_args()

    # search current directory
    # 
    search_path = [os.getcwd(), os.path.dirname(__file__)]



    if args.path is not None:
        search_path.append(args.path)
    print(search_path)

    uGen2215u = load_file(args.uGen2215u) if args.uGen2215u is not None else search_load_file("uGen2215u.cde", search_path)
    Genm2215U = load_file(args.Genm2215U) if args.Genm2215U is not None else search_load_file("Genm2215U.cde", search_path)
    Genw2215u = load_file(args.Genw2215u) if args.Genw2215u is not None else search_load_file("Genw2215u.cde", search_path)
    firmware = load_file(args.firmware) if args.firmware is not None else search_load_file("E1adp.mot", search_path)

    flasher = E10AFlasher(uGen2215u, Genm2215U, Genw2215u)

    flasher.load_kernels()
    flasher.write_firmware(firmware)

    print("Done!")
    print("Final Steps:")
    print("\t1. Unplug Device")
    print("\t2. Move SW1 to 1")
    print("\t3. Reconnect E10A-USB")

    exit(0)









