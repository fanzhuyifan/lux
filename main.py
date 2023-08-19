import argparse, time, os
import brightness, model
from runcmd import run_cmd

def parseArgs():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Automatically adjust the brightness of screen based on content",
    )
    parser.add_argument(
        "--sleep-interval", 
        type=float,
        default=0.5,
        help="Time to sleep between backlight brightness checks in seconds",
    )
    parser.add_argument(
        "--transition-time",
        type=float,
        default=500,
        help="Time to transition between brightness levels in milliseconds",
    )
    parser.add_argument(
        "--min-brightness",
        type=float,
        default=1, 
        help="Minimum brightness",
    )
    parser.add_argument(
        "--max-brightness",
        type=float,
        default=100, 
        help="Maximum brightness",
    )
    parser.add_argument(
        "--file",
        type=str,
        default=os.path.expanduser("~/.config/lux/model.pickle"), 
        help="Location to save the model",
    )
    return parser.parse_args()

def main():
    args = parseArgs()

    controller = brightness.Xbacklight()
    brightnessModel = model.SimpleModel(
        minB=args.min_brightness,
        maxB=args.max_brightness,
    )

    lastScreen = brightness.getScreenBrightness()
    lastBacklight = controller.get()
    brightnessModel.addObservation(lastScreen, lastBacklight)
    brightnessModel.load(args.file)
    while True:
        time.sleep(args.sleep_interval)
        screen = brightness.getScreenBrightness()
        backlight = controller.get()

        if backlight != lastBacklight:
            brightnessModel.addObservation(screen, backlight)
            brightnessModel.saveIfNecessary(args.file)
        else:
            newBacklight = brightnessModel.predict(screen)
            controller.set(newBacklight, args.transition_time)
            time.sleep(max(0, args.transition_time / 1000 - args.sleep_interval))
            backlight = newBacklight

        lastScreen = screen
        lastBacklight = backlight
    pass

if __name__ == "__main__":
    main()