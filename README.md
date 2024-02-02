# lux
A tool that automatically adjusts display brightness based on screen content on linux.
## Install
### Dependencies
See `requirements.txt` for python dependencies.

Non-python dependencies:
- scrot
- xbacklight (acpilight)
- gnome (gnome-screenshot)

## Usage
Run `python main.py` and adjust your screen brightness as you see fit.
The program will remember your choices and make future adjustments based on screen brightness.
Run `python main.py -h` for a complete list of options.

## Algorithm
The program stores all brightness adjustments made by the user, along with the average screen brightness at the time of the adjustment.
Adjustments that conflict with the newest adjustment are removed (conflict means having higher display backlight when the screen is brighter, or having lower display backlight when the screen is dimmer).
As the program detects changes in screen brightness, it will adjust the display backlight to be a linear interpolation between the two closest adjustments.
