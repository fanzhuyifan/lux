import pyscreeze
from PIL import ImageStat
import tempfile, os
from runcmd import run_cmd

class BrightnessController():
    @staticmethod
    def get():
        raise NotImplementedError
    @staticmethod
    def set(new_level, time):
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

class ScreenBrightnessGetter():
    def __init__(self):
        self._tempdir = tempfile.TemporaryDirectory()
        self._tempfile = os.path.join(self._tempdir.name, "screenshot.png")
    def get(self):
        if os.path.exists(self._tempfile): 
            os.remove(self._tempfile)
        return ImageStat.Stat(pyscreeze.screenshot(self._tempfile).convert('L')).rms[0]
