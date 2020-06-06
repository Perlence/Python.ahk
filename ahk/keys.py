from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from typing import Optional

import _ahk  # noqa

from .exceptions import Error

__all__ = [
    "Hotkey", "get_key_state", "hotkey", "hotkey_context", "remap_key",
    "key_wait_pressed", "key_wait_released", "send", "send_mode", "send_level",
]


def get_key_state(key_name, mode=None):
    return _ahk.call("GetKeyState", key_name, mode)


def hotkey(key_name,
           func=None,
           buffer: Optional[bool] = None,
           priority: Optional[int] = None,
           max_threads: Optional[int] = None,
           input_level: Optional[int] = None):

    if key_name == "":
        raise Error("invalid key name")

    if func is None:
        # Return the decorator.
        return partial(hotkey, key_name, buffer=buffer, priority=priority,
                       max_threads=max_threads, input_level=input_level)

    if not callable(func):
        raise TypeError(f"object {func!r} must be callable")

    # TODO: Handle case when func == "AltTab" or other substitutes.
    # TODO: Hotkey command may set ErrorLevel. Raise an exception.

    hk = Hotkey(key_name)
    _ahk.call("Hotkey", key_name, func)
    hk.set_options(buffer=buffer, priority=priority, max_threads=max_threads,
                   input_level=input_level)
    return hk


@contextmanager
def hotkey_context():
    # TODO: Implement `Hotkey, If` commands.
    raise NotImplementedError()


@dataclass
class Hotkey:
    key_name: str

    def enable(self):
        _ahk.call("Hotkey", self.key_name, "On")

    def disable(self):
        _ahk.call("Hotkey", self.key_name, "Off")

    def toggle(self):
        _ahk.call("Hotkey", self.key_name, "Toggle")

    def set_options(self, buffer=None, priority=None, max_threads=None,
                    input_level=None):
        options = []
        if buffer is False:
            options.append("B0")
        elif buffer is True:
            options.append("B")
        if priority is not None:
            options.append(f'P{priority}')
        if max_threads is not None:
            options.append(f"T{max_threads}")
        if input_level is not None:
            options.append(f"I{input_level}")
        option_str = "".join(options)
        if option_str:
            _ahk.call("Hotkey", self.key_name, "", option_str)


def key_wait_pressed(key_name, logical_state=False, timeout=None) -> bool:
    return _key_wait(key_name, down=True, logical_state=logical_state, timeout=timeout)


def key_wait_released(key_name, logical_state=False, timeout=None) -> bool:
    return _key_wait(key_name, down=False, logical_state=logical_state, timeout=timeout)


def _key_wait(key_name, down=False, logical_state=False, timeout=None) -> bool:
    options = []
    if down:
        options.append("D")
    if logical_state:
        options.append("L")
    if timeout is not None:
        options.append(f"T{timeout}")
    timed_out = _ahk.call("KeyWait", str(key_name), "".join(options))
    return not timed_out


def remap_key(origin_key, destination_key):
    # TODO: Implement key remapping, e.g. Esc::CapsLock.
    raise NotImplementedError()


def send(keys):
    # TODO: Consider adding `mode` keyword?
    _ahk.call("Send", keys)


def send_level(level: int):
    if not 0 <= level <= 100:
        raise ValueError("level must be between 0 and 100")
    _ahk.call("SendLevel", int(level))


def send_mode(mode):
    _ahk.call("SendMode", mode)
