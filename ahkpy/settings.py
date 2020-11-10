import contextvars
import dataclasses as dc

from .flow import ahk_call

__all__ = [
    "Settings",
    "default_settings",
    "get_settings",
    "local_settings",
    "set_settings",
]


_current_settings = contextvars.ContextVar("script_settings")


@dc.dataclass
class Settings:
    """Settings()

    .. ^^ Hide the __init__ args from the docs.

    The object that holds thread-local AutoHotkey settings. All delays and
    durations are in seconds.
    """

    #: The delay after each control-modifying method.
    #:
    #: AutoHotkey command: `SetControlDelay
    #: <https://www.autohotkey.com/docs/commands/SetControlDelay.htm>`_.
    control_delay: float = 0.02
    # TODO: List the affected methods.

    #: The delay after each keystroke sent by
    #: :func:`~ahkpy.send_event` and :meth:`Control.send`.
    #:
    #: AutoHotkey command: `SetKeyDelay
    #: <https://www.autohotkey.com/docs/commands/SetKeyDelay.htm>`_.
    key_delay: float = 0.01

    #: The delay after the press of the key and before its release sent by
    #: :func:`~ahkpy.send_event` and :meth:`Control.send`.
    #:
    #: AutoHotkey command: `SetKeyDelay
    #: <https://www.autohotkey.com/docs/commands/SetKeyDelay.htm>`_.
    key_duration: float = -1

    #: The delay after each keystroke sent by
    #: :func:`~ahkpy.send_play`.
    #:
    #: AutoHotkey command: `SetKeyDelay
    #: <https://www.autohotkey.com/docs/commands/SetKeyDelay.htm>`_.
    key_delay_play: float = -1

    #: The delay after the press of the key and before its release sent by
    #: :func:`~ahkpy.send_play`.
    #:
    #: AutoHotkey command: `SetKeyDelay
    #: <https://www.autohotkey.com/docs/commands/SetKeyDelay.htm>`_.
    key_duration_play: float = -1

    #: The delay after each mouse movement or click in the Event mode.
    #:
    #: AutoHotkey command: `SetMouseDelay
    #: <https://www.autohotkey.com/docs/commands/SetMouseDelay.htm>`_.
    mouse_delay: float = 0.01

    #: The delay after each mouse movement or click in the Play mode.
    #:
    #: AutoHotkey command: `SetMouseDelay
    #: <https://www.autohotkey.com/docs/commands/SetMouseDelay.htm>`_.
    mouse_delay_play: float = -1

    #: The speed of mouse movement in the range 0 (fastest) to 100 (slowest).
    #: Affects only the Event mode.
    #:
    #: AutoHotkey command: `SetDefaultMouseSpeed
    #: <https://www.autohotkey.com/docs/commands/SetDefaultMouseSpeed.htm>`_.
    mouse_speed: int = 2

    #: Controls which artificial keyboard and mouse events are ignored by
    #: hotkeys and hotstrings. Must be an integer between 0 and 100.
    #:
    #: AutoHotkey command: `SendLevel
    #: <https://www.autohotkey.com/docs/commands/SendLevel.htm>`_.
    send_level: int = 0

    #: The default mode for :func:`~ahkpy.send` and mouse functions.
    #:
    #: AutoHotkey command: `SendMode
    #: <https://www.autohotkey.com/docs/commands/SendMode.htm>`_.
    send_mode: str = "input"

    #: The delay after each window-modifying method.
    #:
    #: AutoHotkey command: `SetWinDelay
    #: <https://www.autohotkey.com/docs/commands/SetWinDelay.htm>`_.
    win_delay: float = 0.1
    # TODO: List the affected methods.

    # Should CoordMode also be here? I don't think so because the above settings
    # change only some aspects like speed and delay and don't change the overall
    # behavior. For example, the function that moves the mouse cursor or types a
    # word is expected to mostly do the same regardless of these settings.
    #
    # CoordMode on the other hand completely changes the behavior of the
    # affected functions.

    def copy(self):
        return dc.replace(self)

    def __delattr__(self, name):
        raise AttributeError(f"{name} cannot be deleted")


def get_settings() -> Settings:
    """get_settings() -> ahkpy.Settings

    Return the current settings for the active thread.
    """
    try:
        return _current_settings.get()
    except LookupError:
        settings = default_settings.copy()
        _current_settings.set(settings)
        return settings


def set_settings(settings):
    """Set the current settings for the active thread."""
    _current_settings.set(settings)


def local_settings(settings=None):
    """local_settings(settings=None)

    Return a context manager that will set the current settings for the
    active thread to a copy of *settings* on entry to the with-statement and
    restore the previous settings when exiting the with-statement. If no context
    is specified, a copy of the current settings is used.

    For example, the following code removes the current delay between window
    manipulations, modifies the active window, and then automatically restores
    the previous settings::

        prev_delay = ahkpy.get_settings().win_delay

        with ahkpy.local_settings() as settings:
            settings.win_delay = 0
            win = ahkpy.windows.get_active()
            win.maximize()
            win.restore()

        assert ahkpy.get_settings().win_delay == prev_delay

    The function can also be used to safely change the settings of an AHK
    callback without affecting the settings in other functions::

        @ahkpy.hotkey("F1")
        def isolated_settings():
            settings = ahkpy.local_settings().activate()
            settings.win_delay = 0
            ...
    """
    if settings is None:
        settings = get_settings()
    return _SettingsManager(settings)


class _SettingsManager:
    """Context manager class to support local_settings().

    Sets a copy of the supplied context in __enter__() and restores the previous
    settings in __exit__().
    """
    def __init__(self, new_settings):
        self.new_settings = new_settings.copy()

    def activate(self) -> Settings:
        self.prior_settings = get_settings()
        set_settings(self.new_settings)
        return self.new_settings

    __enter__ = activate

    def __exit__(self, t, v, tb):
        set_settings(self.prior_settings)


default_settings = Settings()
set_settings(default_settings)


def optional_ms(value):
    if value is None or value < 0:
        return -1
    else:
        return int(value * 1000)


COORD_TARGETS = {"tooltip", "pixel", "mouse", "caret", "menu"}
COORD_MODES = {"screen", "window", "client"}


def _set_coord_mode(target, relative_to):
    if target not in COORD_TARGETS:
        raise ValueError(f"{target!r} is not a valid coord target")
    if relative_to not in COORD_MODES:
        raise ValueError(f"{relative_to!r} is not a valid coord mode")
    ahk_call("CoordMode", target, relative_to)
