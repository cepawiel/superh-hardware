# Snapgear SG530 / Secure Computing SME530

## Photos
![PCB Top](top1.jpg)
![PCB Top](top2.jpg)
![Ethernet ICs](ethernet.jpg)
![Flash & Reset IC](flash_reset.jpg)
![Close CPU](cpu_close.jpg)
![Photo of E10A attached to SG530](e10a.jpg)


## Disable Hardware Watchdog
This board features a [TI TPS3823](https://www.ti.com/lit/ds/symlink/tps3823.pdf)
near the flash IC labled `U3`. The watchdog timer is connected to an SH4 bus
control line so it can be reset just by doing a memory access that uses the
proper CSn line. Unfortunately this causes issues when attempting to use a JTAG
debugger. This can be worked around by lifting pin 4 which disables the watchdog.
