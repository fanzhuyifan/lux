import pyautogui
from PIL import ImageStat
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

def getScreenBrightness():
    return ImageStat.Stat(pyautogui.screenshot().convert('L')).rms[0]