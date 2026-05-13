#!/bin/bash
if [ "$XDG_SESSION_TYPE" = "wayland" ] && [ -z "$GDK_BACKEND" ]; then
    export GDK_BACKEND=x11
fi
cd "$(dirname "$0")"
exec python3 main.py "$@"
