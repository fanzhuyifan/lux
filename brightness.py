import PIL.Image
import pyscreeze
import PIL
from PIL import ImageStat
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication
import dbus
import tempfile
import os
from runcmd import run_cmd

class BrightnessController():
    def get(self):
        raise NotImplementedError

    def set(self, new_level, time):
        """
        :param new_level: float between 0 and 100
        :param time: int in milliseconds
        """
        raise NotImplementedError

class Xbacklight(BrightnessController):
    @staticmethod
    def get():
        return float(run_cmd("xbacklight -get"))
    @staticmethod
    def set(new_level, time):
        run_cmd(f"xbacklight -set {new_level} -time {int(time)}")


class KWinBacklight(BrightnessController):
    NO_OSD_FLAG = 0x1
    def __init__(self, screenName):
        self._screenName = screenName

    def get(self):
        # Establish a session bus connection
        session_bus = dbus.SessionBus()

        brightness_service = 'local.org_kde_powerdevil'
        brightness_path = f'/org/kde/ScreenBrightness/{self._screenName}'
        brightness_interface = 'org.kde.ScreenBrightness.Display'
        brightness_object = session_bus.get_object(
            brightness_service, brightness_path)
        return dbus.Interface(
            brightness_object, 'org.freedesktop.DBus.Properties'
        ).Get(brightness_interface, 'Brightness') / 100
    
    def set(self, newlevel, time):
        # Establish a session bus connection
        session_bus = dbus.SessionBus()

        brightness_service = 'local.org_kde_powerdevil'
        brightness_path = f'/org/kde/ScreenBrightness/{self._screenName}'
        brightness_interface = 'org.kde.ScreenBrightness.Display'
        brightness_object = session_bus.get_object(
            brightness_service, brightness_path)
        brightness_method = dbus.Interface(
            brightness_object, brightness_interface).get_dbus_method('SetBrightness')
        brightness_method(int(newlevel * 100), KWinBacklight.NO_OSD_FLAG)

class ScreenBrightnessGetter():
    def get(self):
        raise NotImplementedError


class PyScreezeScreenBrightness(ScreenBrightnessGetter):
    def __init__(self):
        self._tempdir = tempfile.TemporaryDirectory()
        self._tempfile = os.path.join(self._tempdir.name, "screenshot.png")
    def get(self):
        if os.path.exists(self._tempfile): 
            os.remove(self._tempfile)
        return ImageStat.Stat(pyscreeze.screenshot(self._tempfile).convert('L')).rms[0]


class AutoClosePipe2(object):
    def __init__(self, flags):
        self.r, self.w = os.pipe2(flags)
    def __enter__(self):
        return self.r, self.w
    def __exit__(self, exc_type, exc_value, traceback):
        os.close(self.r)
        os.close(self.w)

class KWinScreenBrightness(ScreenBrightnessGetter):
    def __init__(self, screenName):
        self._screenName = screenName

    def get(self):
        # Establish a session bus connection
        session_bus = dbus.SessionBus()

        # Access the KWin ScreenShot2 interface
        screenshot_service = 'org.kde.KWin.ScreenShot2'
        screenshot_path = '/org/kde/KWin/ScreenShot2'
        screenshot_interface = 'org.kde.KWin.ScreenShot2'
        screenshot_object = session_bus.get_object(
            screenshot_service, screenshot_path)
        screenshot_method = dbus.Interface(
            screenshot_object, screenshot_interface).get_dbus_method('CaptureScreen')

        # Define options for the screenshot
        options = {
            'include-cursor': False,  # Include the cursor in the screenshot
            'native-resolution': False  # Capture at native resolution
        }

        # Create a temporary file to store the screenshot
        with AutoClosePipe2(os.O_CLOEXEC) as (r, w):
            os.set_blocking(r, True)

            # Create a Unix file descriptor for D-Bus
            unix_fd = dbus.types.UnixFd(w)

            # Call the CaptureScreen method
            result = screenshot_method(self._screenName, options, unix_fd)

            # Process the result
            image_type = result.get('type')
            if image_type != 'raw':
                raise ValueError(f"Unsupported image type: {image_type}")

            width = result.get('width')
            height = result.get('height')
            stride = result.get('stride')
            image_format = result.get('format')
            screen = result.get('screen')
            scale = result.get('scale')

            raw_data = bytearray()
            totalBytes = width * height * 4
            while len(raw_data) < totalBytes:
                raw_data += os.read(r, totalBytes - len(raw_data))

            if image_format == 5:  # QImage::Format_ARGB32
                mode = 'RGBA'
                arg = 'BGRA'
            else:
                raise ValueError(f"Unsupported image format: {image_format}")

            image = PIL.Image.frombytes(
                mode, (width, height), raw_data, 'raw', arg)

            return ImageStat.Stat(image.convert('L')).rms[0]


def getScreens():

    app = QApplication([])  # Create a QApplication instance

    screens = QGuiApplication.screens()
    return sorted([screen.name() for screen in screens])
