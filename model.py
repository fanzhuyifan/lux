import pickle
import os
import copy
from pathlib import Path

class BrightnessModel():
    def __init__(self, minB, maxB):
        """
        :param minB: float between 0 and 100, minimum brightness
        :param maxB: float between 0 and 100, maximum brightness
        """
        self.minB = minB
        self.maxB = maxB
    def load(self, file):
        return os.path.exists(file)
    def save(self, file):
        Path(file).parent.mkdir(parents=True, exist_ok=True)
    def saveIfNecessary(self, file):
        raise NotImplementedError
    def addObservation(self, screen, backlight):
        """
        :param screen: float between 0 and 1, screen brightness
        :param backlight: float between 0 and 100, backlight brightness
        """
        raise NotImplementedError
    def predict(self, screen):
        """
        :param screen: float between 0 and 1, screen brightness
        :return: float between 0 and 100, backlight brightness
        """
        raise NotImplementedError
    def clip(self, brightness):
        return round(max(self.minB, min(self.maxB, brightness)))

class SimpleModel(BrightnessModel):
    def __init__(self, minB, maxB, maxObs=10):
        super().__init__(minB, maxB)
        self._observations = []
        self._lastSave = None
        self._i = 0
        assert(maxObs > 0)
        self.maxObs = maxObs

    def addObservation(self, screen, backlight):
        self._observations = self.filterInconsistent(screen, backlight, self._observations)
        if len(self._observations) == self.maxObs:
            # remove item with smallest _i
            iSmallest = min(
                self._observations, 
                key=lambda x: x[-1]
            )[-1]
            self._observations = [
                obs for obs in self._observations
                if obs[-1] > iSmallest
            ]
        self._observations.append((screen, backlight, self._i))
        self._i += 1
    
    @staticmethod
    def filterInconsistent(screen, backlight, observations):
        return [
            (s, b, i) for s, b, i in observations
            if (s > screen and b < backlight) or (s < screen and b > backlight)
        ]

    def predict(self, screen):
        assert(len(self._observations) > 0)
        if len(self._observations) == 1:
            return self._observations[0][1]
        # find screenL, screenR, backL, backR
        # such that screenL <= screen <= screenR, and screenL is maximized, and screenR is minimized
        # and backL and backR are the corresponding backlights
        screenL = screenR = backL = backR = None
        try:
            screenL, backL, _ = max(
                filter(
                    lambda x: x[0] <= screen,
                    self._observations,
                ), 
                key=lambda x: x[0])
        except ValueError:
            pass
        try:
            screenR, backR, _ = min(
                filter(
                    lambda x: x[0] >= screen,
                    self._observations,
                ), 
                key=lambda x: x[0])
        except ValueError:
            pass
        if screenL is None:
            screenL, backL, _ = min(
                filter(
                    lambda x: x[0] > screenR,
                    self._observations,
                ), 
                key=lambda x: x[0])
        elif screenR is None:
            screenR, backR, _ = max(
                filter(
                    lambda x: x[0] < screenL,
                    self._observations,
                ), 
                key=lambda x: x[0])

        # now we have screenL, screenR, backL, backR
        # we want to find the linear interpolation between backL and backR
        # that corresponds to screen
        if screenL == screenR:
            assert(backL == backR)
            return backL
        return self.clip(
            backL + (backR - backL) * (screen - screenL) / (screenR - screenL)
        )
    
    def load(self, file):
        if not super().load(file):
            return False
        with open(file, "rb") as f:
            self._observations = pickle.load(f)
        self._lastSave = self._observations
        return True
    
    def save(self, file):
        super().save(file)
        with open(file, "wb") as f:
            pickle.dump(self._observations, f)
        self._lastSave = self._observations
        
    
    def saveIfNecessary(self, file):
        if self._lastSave != self._observations:
            self.save(file)

