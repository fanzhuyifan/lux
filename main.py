import argparse, time, os
import brightness, model
import traceback

def parseArgs():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Automatically adjust the brightness of screen based on content",
    )
    parser.add_argument(
        "--sleep-interval", 
        type=float,
        default=1,
        help="Time to sleep between backlight brightness checks in seconds",
    )
    parser.add_argument(
        "--transition-time",
        type=float,
        default=500,
        help="Time to transition between brightness levels in milliseconds",
    )
    parser.add_argument(
        "--change-threshold",
        type=float,
        default=10,
        help="Threshold for changing brightness",
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
        "--save-path",
        type=str,
        default=os.path.expanduser("~/.config/lux/"), 
        help="Location to save the model",
    )
    return parser.parse_args()

def main():
    args = parseArgs()

    brightnessModels = dict()
    lastScreenBacklight = dict()

    while True:
        time.sleep(args.sleep_interval)
        screens = brightness.getScreens()
        for i, screen in enumerate(screens):
            if screen not in brightnessModels:
                brightnessModels[screen] = model.SimpleModel(
                    args.min_brightness, args.max_brightness)
                brightnessModels[screen].load(
                    os.path.join(args.save_path, f"model_{screen}.pkl"))
            try:
                screenBrightness = brightness.KWinScreenBrightness(
                    screen).get()
                screenBacklight = brightness.KWinBacklight(f'display{i}').get()
                if screen not in lastScreenBacklight or screenBacklight != lastScreenBacklight[screen]:
                    brightnessModels[screen].addObservation(
                        screenBrightness, screenBacklight)
                    brightnessModels[screen].saveIfNecessary(
                        os.path.join(args.save_path, f"model_{screen}.pkl"))
                    print(f"Adding observation: {screen} {screenBrightness}, {screenBacklight}")
                else:
                    newBackLight = brightnessModels[screen].predict(screenBrightness)
                    if abs(newBackLight - screenBacklight) > args.change_threshold:
                        print(f"Predicted brightness: {screen} {newBackLight} from {screenBacklight} based on {screenBrightness}")
                        brightness.KWinBacklight(f'display{i}').set(
                            newBackLight, args.transition_time)
                        screenBacklight = newBackLight

                lastScreenBacklight[screen] = screenBacklight
            except Exception as e:
                print(f"Exception: {e}")
                traceback.print_exc()
                continue


if __name__ == "__main__":
    main()