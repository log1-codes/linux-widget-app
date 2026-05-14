#!/usr/bin/env python3
"""
Widget App – desktop widgets for GNOME/Wayland (via XWayland)
Run: widget-app
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from manager.widget_manager import WidgetManager, discover_widgets

try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
    HAS_INDICATOR = True
except (ValueError, ImportError):
    HAS_INDICATOR = False

# ── SVG app logo ──────────────────────────────────────────────────────────────
APP_ICON_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1a1a2e"/>
      <stop offset="100%" style="stop-color:#16213e"/>
    </linearGradient>
    <linearGradient id="ac" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#64b5f6"/>
      <stop offset="100%" style="stop-color:#82b1ff"/>
    </linearGradient>
  </defs>
  <rect width="64" height="64" rx="14" fill="url(#bg)"/>
  <rect x="8"  y="8"  width="22" height="22" rx="5" fill="url(#ac)" opacity="0.90"/>
  <rect x="34" y="8"  width="22" height="22" rx="5" fill="url(#ac)" opacity="0.55"/>
  <rect x="8"  y="34" width="22" height="22" rx="5" fill="url(#ac)" opacity="0.55"/>
  <rect x="34" y="34" width="22" height="22" rx="5" fill="url(#ac)" opacity="0.30"/>
  <circle cx="19" cy="19" r="7" fill="none" stroke="white" stroke-width="1.2" opacity="0.7"/>
  <line x1="19" y1="19" x2="19" y2="13.5" stroke="white" stroke-width="1.5" stroke-linecap="round" opacity="0.95"/>
  <line x1="19" y1="19" x2="23.5" y2="21" stroke="white" stroke-width="1.2" stroke-linecap="round" opacity="0.95"/>
  <circle cx="45" cy="19" r="3.5" fill="white" opacity="0.25"/>
  <line x1="40" y1="40" x2="56" y2="40" stroke="white" stroke-width="1.5" stroke-linecap="round" opacity="0.35"/>
  <line x1="40" y1="44" x2="52" y2="44" stroke="white" stroke-width="1.5" stroke-linecap="round" opacity="0.25"/>
  <line x1="40" y1="48" x2="54" y2="48" stroke="white" stroke-width="1.5" stroke-linecap="round" opacity="0.20"/>
</svg>"""


def _svg_to_pixbuf(svg_bytes, size=64):
    loader = GdkPixbuf.PixbufLoader.new_with_type('svg')
    loader.set_size(size, size)
    loader.write(svg_bytes)
    loader.close()
    return loader.get_pixbuf()


def _write_icon_file():
    icon_dir = os.path.expanduser('~/.local/share/icons/widget-app')
    os.makedirs(icon_dir, exist_ok=True)
    icon_path = os.path.join(icon_dir, 'widget-app.svg')
    with open(icon_path, 'wb') as f:
        f.write(APP_ICON_SVG)
    return icon_dir, 'widget-app'


class WidgetApp:
    def __init__(self):
        discover_widgets()
        self.manager = WidgetManager()
        # Set window icon from SVG
        try:
            pixbuf = _svg_to_pixbuf(APP_ICON_SVG, 64)
            Gtk.Window.set_default_icon(pixbuf)
        except Exception:
            pass
        self._setup_tray()

    def _setup_tray(self):
        if HAS_INDICATOR:
            self._setup_app_indicator()
        else:
            self._setup_status_icon()

    def _setup_app_indicator(self):
        icon_dir, icon_name = _write_icon_file()
        self.indicator = AppIndicator3.Indicator.new(
            'widget-app', icon_name,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_icon_theme_path(icon_dir)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self._build_menu())

    def _setup_status_icon(self):
        self.tray_icon = Gtk.StatusIcon()
        try:
            pixbuf = _svg_to_pixbuf(APP_ICON_SVG, 22)
            self.tray_icon.set_from_pixbuf(pixbuf)
        except Exception:
            self.tray_icon.set_from_icon_name('utilities-system-monitor')
        self.tray_icon.set_tooltip_text('Widget App')
        self.tray_icon.connect('popup-menu', self._on_tray_popup)
        self.tray_icon.connect('activate', self._toggle_manager)

    def _on_tray_popup(self, icon, button, time):
        menu = self._build_menu()
        menu.popup(None, None, Gtk.StatusIcon.position_menu, icon, button, time)

    def _build_menu(self):
        menu = Gtk.Menu()
        show_item = Gtk.MenuItem(label='Toggle Widget Manager')
        show_item.connect('activate', self._toggle_manager)
        menu.append(show_item)
        menu.append(Gtk.SeparatorMenuItem())
        quit_item = Gtk.MenuItem(label='Quit')
        quit_item.connect('activate', self._quit)
        menu.append(quit_item)
        menu.show_all()
        return menu

    def _toggle_manager(self, widget=None):
        win = self.manager.get_manager_window()
        if win.get_visible():
            win.hide()
        else:
            win.show()
            win.present()

    def _quit(self, widget=None):
        for name, w in list(self.manager.active_widgets.items()):
            w.close()
        Gtk.main_quit()

    def run(self):
        Gtk.main()


if __name__ == '__main__':
    app = WidgetApp()
    app.run()
