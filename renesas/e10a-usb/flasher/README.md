# E10A-USB Flasher
Quick python tool for updating the firmware on the E10A-USB using the USB flash programing mode built into the ROM. Works well for recovering a bricked device since the bootloader is in ROM. Requires `Genm2215U.cde`, `Genw2215u.cde`, and `uGen2215u.cde` files which can be found in `C:\Program Files (x86)\Renesas\Hew\Tools\Renesas\DebugComp\Platform\E10A-USB\SH-4\SH-4\SetupTool` (for SH-4) along with the firmware binary `E1adp.mot` when HEW is installed with the E10A-USB drivers.

## Warning
While its hard to brick this device since the bootloader is in ROM, I don't believe this is a foolproof process and I'm not responsible for any damages to your device. The datasheet for the `H8S/2215` also states a minimum of 100 programing cycles on the flash, so I'd try to avoid too many erase/write cycles.

## Notes
- SW1 controls the programing mode of the H8S/2215, 0=program, 1=normal operation
  - Pretty much everything says don't change this while power is applied to the device to avoid damage.
  - USB ID of `045B:000D` represents programing mode
  - USB E10A-USB uses USB ID of `045B:0013` when operating normally

## Prereqs
```bash
sudo apt-get install python3-bincopy python3-usb
```

## Example
Pass path to SetupTool directory with required files
```bash
python3 flash.py -p <e10a/path/to/setup>/SetupTool
```

Alternatively copy required files to this directory and optionally pass a firmware path
```bash
python3 flash.py # Flashes `E1adp.mot` found in search paths
# or
python3 flash.py -f <path/to>/E1adp.mot # Flashes specified file
```

Recommend looking over python script and H8S/2215 Manual for additonal information on programing the onboard flash.

## Troubleshooting
 - Occasionally HEW seems unhappy with the device after flashing. Guessing something to do with some fields that should be modified when flashing the binary (Serial Number, etc). Reflashing the device with the official tool located in the `**/SetupTool` seems to make HEW happy so good enough for me.
