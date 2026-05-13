import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import json
import os
import importlib
import inspect

CONFIG_DIR = os.path.expanduser('~/.config/widget-app')
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, 'widgets.json')
ACTIVE_FILE = os.path.join(CONFIG_DIR, 'active.json')

WIDGET_REGISTRY = {}

def register_widget(name, title, widget_class, icon=''):
    WIDGET_REGISTRY[name] = {
        'title': title,
        'class': widget_class,
        'icon': icon,
    }

def discover_widgets():
    import widgets.clock_widget
    import widgets.task_widget
    import widgets.weather_widget
    import widgets.music_widget
    import widgets.system_widget
    import widgets.note_widget

class WidgetManager:
    def __init__(self):
        self.active_widgets = {}
        self.window = None
        self._build_manager_window()
        self._load_active_widgets()
        GLib.timeout_add(1000, self._update_widgets)

    def _build_manager_window(self):
        self.window = Gtk.Window(title='Widget Manager')
        self.window.set_default_size(320, 450)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_keep_above(True)

        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.window.set_visual(visual)

        css_provider = Gtk.CssProvider()
        css = """
            .manager-window {
                background-color: rgba(22, 22, 32, 0.65);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            .manager-title {
                color: rgba(255, 255, 255, 0.9);
                font-size: 16px;
                font-weight: 700;
                padding: 4px 0;
            }
            .manager-subtitle {
                color: rgba(255, 255, 255, 0.45);
                font-size: 11px;
            }
            .widget-card {
                background-color: rgba(255, 255, 255, 0.06);
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.06);
                padding: 12px;
                margin: 4px 0;
            }
            .widget-card:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.15);
            }
            .widget-card-title {
                color: rgba(255, 255, 255, 0.85);
                font-size: 13px;
                font-weight: 600;
            }
            .widget-card-desc {
                color: rgba(255, 255, 255, 0.4);
                font-size: 11px;
            }
            .add-btn {
                background-color: rgba(100, 181, 246, 0.15);
                color: #64b5f6;
                border: 1px solid rgba(100, 181, 246, 0.2);
                border-radius: 10px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            .add-btn:hover {
                background-color: rgba(100, 181, 246, 0.25);
            }
            .remove-btn {
                background: none;
                border: none;
                color: rgba(255, 255, 255, 0.3);
                font-size: 16px;
                padding: 2px 6px;
                border-radius: 20px;
            }
            .remove-btn:hover {
                color: #ef5350;
                background-color: rgba(239, 83, 80, 0.15);
            }
            .status-dot {
                font-size: 8px;
                margin-right: 4px;
            }
            .header-bar {
                background-color: rgba(255, 255, 255, 0.03);
                border-radius: 20px 20px 0 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.04);
                padding: 16px;
            }
            .footer-bar {
                background-color: rgba(255, 255, 255, 0.02);
                border-radius: 0 0 20px 20px;
                border-top: 1px solid rgba(255, 255, 255, 0.04);
                padding: 10px 16px;
            }
            .footer-text {
                color: rgba(255, 255, 255, 0.3);
                font-size: 10px;
            }
        """
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.window.get_style_context().add_class('manager-window')

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(vbox)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.get_style_context().add_class('header-bar')
        header.set_margin_start(16)
        header.set_margin_end(16)
        header.set_margin_top(16)
        header.set_margin_bottom(8)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        title_lbl = Gtk.Label(label='Widget Manager')
        title_lbl.get_style_context().add_class('manager-title')
        title_lbl.set_xalign(0.0)
        subtitle_lbl = Gtk.Label(label='Drag widgets to position them on your desktop')
        subtitle_lbl.get_style_context().add_class('manager-subtitle')
        subtitle_lbl.set_xalign(0.0)
        title_box.pack_start(title_lbl, False, False, 0)
        title_box.pack_start(subtitle_lbl, False, False, 0)
        header.pack_start(title_box, True, True, 0)

        self.refresh_btn = Gtk.Button(label='↻')
        self.refresh_btn.set_tooltip_text('Refresh widgets')
        self.refresh_btn.get_style_context().add_class('remove-btn')
        self.refresh_btn.set_size_request(36, 36)
        self.refresh_btn.connect('clicked', self._on_refresh)
        header.pack_end(self.refresh_btn, False, False, 0)

        vbox.pack_start(header, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.get_style_context().add_class('widget-scroll')

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.get_style_context().add_class('widget-list')
        self.list_box.set_margin_start(12)
        self.list_box.set_margin_end(12)
        self.list_box.set_margin_top(4)
        self.list_box.set_margin_bottom(4)

        scroll.add(self.list_box)
        vbox.pack_start(scroll, True, True, 0)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        footer.get_style_context().add_class('footer-bar')
        footer.set_margin_start(16)
        footer.set_margin_end(16)
        footer.set_margin_top(4)
        footer.set_margin_bottom(12)

        footer_lbl = Gtk.Label(label='Right-click manager icon → Quit to exit')
        footer_lbl.get_style_context().add_class('footer-text')
        footer.pack_start(footer_lbl, False, False, 0)

        self.show_btn = Gtk.Button(label='Hide Manager')
        self.show_btn.get_style_context().add_class('add-btn')
        self.show_btn.connect('clicked', self._toggle_manager)
        footer.pack_end(self.show_btn, False, False, 0)

        vbox.pack_start(footer, False, False, 0)

        self.window.connect('delete-event', self._on_delete)

        self.window.show_all()

    def _rebuild_list(self):
        for child in self.list_box.get_children():
            self.list_box.remove(child)

        for name, info in WIDGET_REGISTRY.items():
            card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            card.get_style_context().add_class('widget-card')
            card.set_margin_top(2)
            card.set_margin_bottom(2)

            text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            title_lbl = Gtk.Label(label=info['title'])
            title_lbl.get_style_context().add_class('widget-card-title')
            title_lbl.set_xalign(0.0)
            desc_lbl = Gtk.Label(label=self._get_widget_desc(name))
            desc_lbl.get_style_context().add_class('widget-card-desc')
            desc_lbl.set_xalign(0.0)
            text_box.pack_start(title_lbl, False, False, 0)
            text_box.pack_start(desc_lbl, False, False, 0)

            card.pack_start(text_box, True, True, 0)

            if name in self.active_widgets:
                status_lbl = Gtk.Label(label='● Active')
                status_lbl.set_tooltip_text('Widget is running')
                status_lbl.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.5, 0.9, 0.5, 1))
                status_lbl.set_margin_end(8)
                card.pack_end(status_lbl, False, False, 0)

                remove_btn = Gtk.Button(label='✕')
                remove_btn.get_style_context().add_class('remove-btn')
                remove_btn.set_size_request(28, 28)
                remove_btn.set_tooltip_text('Remove this widget')
                remove_btn.connect('clicked', self._on_remove_widget, name)
                card.pack_end(remove_btn, False, False, 0)
            else:
                add_btn = Gtk.Button(label='+ Add')
                add_btn.get_style_context().add_class('add-btn')
                add_btn.connect('clicked', self._on_add_widget, name)
                card.pack_end(add_btn, False, False, 0)

            self.list_box.add(card)

        self.list_box.show_all()

    def _get_widget_desc(self, name):
        descs = {
            'analog_clock': 'Analog clock with smooth hands',
            'task_list': 'Minimal todo list manager',
            'weather': 'Current weather and forecast',
            'now_playing': 'Currently playing music (MPRIS)',
            'system_monitor': 'CPU, RAM, and disk usage',
            'note': 'Quick sticky notes',
        }
        return descs.get(name, '')

    def _on_add_widget(self, btn, name):
        if name not in self.active_widgets:
            info = WIDGET_REGISTRY[name]
            widget = info['class'](on_delete=self._on_widget_closed)
            widget.load_position()
            if not widget._position_loaded:
                cascade = len(self.active_widgets) * 40
                widget.move(cascade, cascade)
            widget.show_all()
            self.active_widgets[name] = widget
            self._rebuild_list()
            self._save_active()

    def _on_remove_widget(self, btn, name):
        if name in self.active_widgets:
            widget = self.active_widgets[name]
            widget.close()
            del self.active_widgets[name]
            self._rebuild_list()
            self._save_active()

    def _on_widget_closed(self, widget):
        for name, w in list(self.active_widgets.items()):
            if w == widget:
                del self.active_widgets[name]
                self._rebuild_list()
                self._save_active()
                break

    def _save_active(self):
        names = list(self.active_widgets.keys())
        with open(ACTIVE_FILE, 'w') as f:
            json.dump(names, f)

    def _load_active_widgets(self):
        if os.path.exists(ACTIVE_FILE):
            with open(ACTIVE_FILE) as f:
                try:
                    names = json.load(f)
                    for name in names:
                        if name in WIDGET_REGISTRY and name not in self.active_widgets:
                            info = WIDGET_REGISTRY[name]
                            widget = info['class'](on_delete=self._on_widget_closed)
                            widget.load_position()
                            widget.show_all()
                            self.active_widgets[name] = widget
                except:
                    pass
        self._rebuild_list()

    def _update_widgets(self):
        for name, widget in list(self.active_widgets.items()):
            try:
                widget.refresh()
            except:
                pass
        return True

    def _toggle_manager(self, btn):
        if self.window.get_visible():
            self.window.hide()
            self.show_btn.set_label('Show Manager')
        else:
            self.window.show()
            self.window.present()
            self.show_btn.set_label('Hide Manager')

    def _on_refresh(self, btn):
        for name, widget in list(self.active_widgets.items()):
            try:
                widget.refresh()
            except:
                pass

    def _on_delete(self, window, event):
        window.hide()
        self.show_btn.set_label('Show Manager')
        return True

    def get_manager_window(self):
        return self.window
