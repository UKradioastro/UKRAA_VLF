<div align=center>
<img src="images/UKRAA_Logo_Black.svg" width=**400** height=**400**/>
</div>


# Python code for the UKRAA PicoMagnetometer
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](/LICENSE)
[![Python 3](https://img.shields.io/badge/Python-3-blue.svg?logo=python)](https://www.python.org/)
[![Shell Script](https://img.shields.io/badge/Shell-Script-4EAA25.svg?logo=gnu-bash)](https://www.gnu.org/software/bash/)
[![GNUplot](https://img.shields.io/badge/GNUplot-5.4-4F4F4F.svg)](https://www.gnuplot.info/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4%2F5-red.svg?logo=raspberrypi)](https://www.raspberrypi.org/)
[![Made for Raspberry Pi](https://img.shields.io/badge/Made%20for-Raspberry%20Pi-A22846.svg?logo=raspberrypi)](https://www.raspberrypi.com/)

Set of Python, gnuplot and shell scripts to run on a RPi4/5 to record, process and present data from the UKRAA VLF.

This software was written to suit a specific set-up; feel free to use as you see fit.

Instructions for initial setting up of a Raspberry Pi4/5 are included in the **docs** folder.

---

&nbsp;
<!-- =============================================================================== --> 
## Contents

- [Using the code](#using-the-code) 
- [Getting the software onto your RPi](#getting-the-software-onto-your-RPi)
- [Installing the software onto your RPi](#installing-the-software-onto-your-RPi)
- [What does the code do](#what-does-the-code-do)
- [Updating the software](#updating-the-software)
- [Publishing a release](#publishing-a-release)
- [License](#license)
- [Contact us](#contact-us)

&nbsp;

---

&nbsp;
<!-- =============================================================================== --> 
## Using the code

The installer uses the account that invoked `sudo`; the username does not have to be **pi**. Clone into `~/UKRAA_VLF` as that account, then run the installer with `sudo`. Do not run it from a root login unless you set `VLF_FILE_OWNER` to the account that owns the checkout. Moving an existing installation to another account is not supported.

The collector defaults to **0x68**, configured in **config/aerial.ini**. After installing the software, you can run **ConfigureAerial.py** to select a different path and record the aerial identity.


**GetDataRaw.py** is run as a service.

Other scripts (Python and gnuplot) are run from **cron** using shell scripts.

[Back to Contents...](#contents)

&nbsp;

---

&nbsp;<!-- =============================================================================== --> 