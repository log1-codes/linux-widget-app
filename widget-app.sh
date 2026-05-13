#!/bin/sh
if [ "$XDG_SESSION_TYPE" = "wayland" ] && [ -z "$GDK_BACKEND" ]; then
	export GDK_BACKEND=x11
fi
exec /usr/bin/python3 /usr/share/widget-app/main.py "$@"
