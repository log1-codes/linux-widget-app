#!/bin/sh
# Widget App launcher
# Forces GDK_BACKEND=x11 (XWayland) on Wayland sessions.
# This is REQUIRED for:
#   1. Keyboard input to work in task/note widgets (Wayland DOCK hint blocks key events)
#   2. set_keep_below() and WindowTypeHint to behave correctly
if [ -z "$GDK_BACKEND" ]; then
    export GDK_BACKEND=x11
fi
exec /usr/bin/python3 /usr/share/widget-app/main.py "$@"
