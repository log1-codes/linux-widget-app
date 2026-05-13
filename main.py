#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
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

class WidgetApp:
    def __init__(self):
        discover_widgets()
        self.manager = WidgetManager()
        self._setup_tray()

    def _setup_tray(self):
        if HAS_INDICATOR:
            self._setup_app_indicator()
        else:
            self._setup_status_icon()

    def _setup_app_indicator(self):
        from gi.repository import AppIndicator3
        self.indicator = AppIndicator3.Indicator.new(
            'widget-app', 'utilities-system-monitor',
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        menu = self._build_menu()
        self.indicator.set_menu(menu)

    def _setup_status_icon(self):
        self.tray_icon = Gtk.StatusIcon()
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
