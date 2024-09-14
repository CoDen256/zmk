from pynput.keyboard import Key, Listener

import time


def current_milli_time():
    return round(time.time() * 1000)


pressed = [current_milli_time()]
time.sleep(1)


def on_press(key):
    if key == Key.space: key = "space"
    cur = current_milli_time()
    pressed.append(current_milli_time())
    print('{0} press   - {1} ~ {2} ms'.format(
        cur, key, cur - pressed[-2]))


def on_release(key):
    if key == Key.space: key = "space"
    cur = current_milli_time()
    # pressed.append(current_milli_time())
    print('{0} release - {1} ~ {2} ms'.format(
        cur, key, cur - pressed[-2]))
    if key == Key.esc:
        # Stop listenerfddaaaseseta
        return False


# Collect events until releasedqqqqwqwwwwwwwwwqw
with Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()
