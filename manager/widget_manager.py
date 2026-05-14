"""
Widget Manager – the control panel for adding/removing desktop widgets.

Design:
  • Dark frosted-glass look (same macOS-inspired palette as widgets)
  • White text on dark cards = readable at all times
  • Full dark theme so titles, descriptions, and buttons are always visible
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import json
import os

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
    import widgets.clock_widget    # noqa: F401
    import widgets.task_widget     # noqa: F401
    import widgets.weather_widget  # noqa: F401
    import widgets.music_widget    # noqa: F401
    import widgets.system_widget   # noqa: F401
    import widgets.note_widget     # noqa: F401


# ── CSS (full dark theme, no light colours) ───────────────────────────────────
MANAGER_CSS = """
    /* ── Window ── */
    .manager-window {
        background-color: rgba(18, 18, 26, 0.96);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }

    /* ── Header ── */
    .header-bar {
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 20px 20px 0 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    }
    .manager-title {
        color: rgba(255, 255, 255, 0.95);
        font-size: 17px;
        font-weight: 700;
    }
    .manager-subtitle {
        color: rgba(255, 255, 255, 0.42);
        font-size: 11px;
    }

    /* ── Widget cards ── */
    .widget-card {
        background-color: rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.09);
        padding: 12px;
        margin: 3px 0;
    }
    .widget-card:hover {
        background-color: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    .widget-icon {
        font-size: 22px;
        min-width: 36px;
    }
    .widget-card-title {
        color: rgba(255, 255, 255, 0.92);
        font-size: 13px;
        font-weight: 600;
    }
    .widget-card-desc {
        color: rgba(255, 255, 255, 0.48);
        font-size: 11px;
        margin-top: 1px;
    }

    /* ── Buttons ── */
    .add-btn {
        background-color: rgba(100, 181, 246, 0.18);
        color: #64b5f6;
        border: 1px solid rgba(100, 181, 246, 0.30);
        border-radius: 10px;
        padding: 5px 14px;
        font-size: 12px;
        font-weight: 700;
    }
    .add-btn:hover {
        background-color: rgba(100, 181, 246, 0.30);
        color: #bbdefb;
    }
    .remove-btn {
        background: none;
        border: none;
        color: rgba(255, 255, 255, 0.35);
        font-size: 16px;
        padding: 2px 6px;
        border-radius: 20px;
    }
    .remove-btn:hover {
        color: #ff453a;
        background-color: rgba(255, 69, 58, 0.18);
    }
    .active-pill {
        background-color: rgba(48, 209, 88, 0.15);
        color: #30d158;
        border: 1px solid rgba(48, 209, 88, 0.25);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 11px;
        font-weight: 600;
    }

    /* ── Footer ── */
    .footer-bar {
        background-color: rgba(255, 255, 255, 0.02);
        border-radius: 0 0 20px 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
    .footer-text {
        color: rgba(255, 255, 255, 0.28);
        font-size: 10px;
    }

    /* ── ListBox rows – remove default white bg ── */
    row {
        background: transparent;
        border: none;
        padding: 0;
    }
    row:hover {
        background: transparent;
    }
    row:selected {
        background: transparent;
    }
"""

WIDGET_DESCS = {
    'analog_clock':   'Analog clock with smooth hands',
    'task_list':      'Todo list — add tasks right from your desktop',
    'weather':        'Current weather + feels-like, humidity, wind',
    'now_playing':    'Currently playing music via MPRIS',
    'system_monitor': 'CPU, RAM, disk usage at a glance',
    'note':           'Quick sticky note — always visible',
}


class WidgetManager:
    def __init__(self):
        self.active_widgets = {}
        self.window = None
        self._build_manager_window()
        self._load_active_widgets()
        GLib.timeout_add(1000, self._update_widgets)

    # ── Build UI ──────────────────────────────────────────────────────────────

    def _build_manager_window(self):
        self.window = Gtk.Window(title='Widget Manager')
        self.window.set_default_size(340, 480)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_keep_above(True)
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)

        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.window.set_visual(visual)

        # Apply CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(MANAGER_CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.window.get_style_context().add_class('manager-window')

        # Allow dragging the manager window by its header
        self._mgr_drag_x = 0
        self._mgr_drag_y = 0
        self._mgr_offset_x = 0
        self._mgr_offset_y = 0

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.window.add(vbox)

        # ── Header ──
        header_eb = Gtk.EventBox()
        header_eb.get_style_context().add_class('header-bar')
        header_eb.connect('button-press-event', self._on_mgr_press)
        header_eb.connect('button-release-event', self._on_mgr_release)
        header_eb.connect('motion-notify-event', self._on_mgr_motion)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.set_margin_start(18)
        header.set_margin_end(14)
        header.set_margin_top(18)
        header.set_margin_bottom(14)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_lbl = Gtk.Label(label='Widget Manager')
        title_lbl.get_style_context().add_class('manager-title')
        title_lbl.set_xalign(0.0)
        subtitle_lbl = Gtk.Label(label='Click + Add to place a widget on your desktop')
        subtitle_lbl.get_style_context().add_class('manager-subtitle')
        subtitle_lbl.set_xalign(0.0)
        title_box.pack_start(title_lbl, False, False, 0)
        title_box.pack_start(subtitle_lbl, False, False, 0)
        header.pack_start(title_box, True, True, 0)

        close_mgr = Gtk.Button(label='×')
        close_mgr.get_style_context().add_class('remove-btn')
        close_mgr.set_size_request(32, 32)
        close_mgr.set_tooltip_text('Hide manager')
        close_mgr.connect('clicked', lambda b: self.window.hide())
        header.pack_end(close_mgr, False, False, 0)

        header_eb.add(header)
        vbox.pack_start(header_eb, False, False, 0)

        # ── Scrollable list ──
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.list_box.set_margin_start(12)
        self.list_box.set_margin_end(12)
        self.list_box.set_margin_top(6)
        self.list_box.set_margin_bottom(6)

        scroll.add(self.list_box)
        vbox.pack_start(scroll, True, True, 0)

        # ── Footer ──
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        footer.get_style_context().add_class('footer-bar')
        footer.set_margin_start(18)
        footer.set_margin_end(14)
        footer.set_margin_top(8)
        footer.set_margin_bottom(14)

        footer_lbl = Gtk.Label(label='Right-click tray icon → Quit to exit')
        footer_lbl.get_style_context().add_class('footer-text')
        footer.pack_start(footer_lbl, True, True, 0)

        vbox.pack_start(footer, False, False, 0)

        self.window.connect('delete-event', self._on_delete)
        self.window.show_all()

    # ── Manager window drag ───────────────────────────────────────────────────

    def _on_mgr_press(self, widget, event):
        if event.button == 1:
            self._mgr_drag_x = event.x_root
            self._mgr_drag_y = event.y_root
            x, y = self.window.get_position()
            self._mgr_offset_x = int(event.x_root - x)
            self._mgr_offset_y = int(event.y_root - y)
            return True
        return False

    def _on_mgr_release(self, widget, event):
        self._mgr_drag_x = 0
        self._mgr_drag_y = 0

    def _on_mgr_motion(self, widget, event):
        if self._mgr_drag_x != 0:
            self.window.move(
                int(event.x_root - self._mgr_offset_x),
                int(event.y_root - self._mgr_offset_y),
            )
            return True
        return False

    # ── List rebuild ──────────────────────────────────────────────────────────

    def _rebuild_list(self):
        for child in self.list_box.get_children():
            self.list_box.remove(child)

        for name, info in WIDGET_REGISTRY.items():
            card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            card.get_style_context().add_class('widget-card')
            card.set_margin_top(2)
            card.set_margin_bottom(2)

            # Icon
            icon_lbl = Gtk.Label(label=info.get('icon', '□'))
            icon_lbl.get_style_context().add_class('widget-icon')
            card.pack_start(icon_lbl, False, False, 0)

            # Text
            text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            title_lbl = Gtk.Label(label=info['title'])
            title_lbl.get_style_context().add_class('widget-card-title')
            title_lbl.set_xalign(0.0)
            desc_lbl = Gtk.Label(label=WIDGET_DESCS.get(name, ''))
            desc_lbl.get_style_context().add_class('widget-card-desc')
            desc_lbl.set_xalign(0.0)
            text_box.pack_start(title_lbl, False, False, 0)
            text_box.pack_start(desc_lbl, False, False, 0)
            card.pack_start(text_box, True, True, 0)

            # Action buttons
            if name in self.active_widgets:
                pill = Gtk.Label(label='● Active')
                pill.get_style_context().add_class('active-pill')
                card.pack_end(pill, False, False, 0)

                rm_btn = Gtk.Button(label='✕')
                rm_btn.get_style_context().add_class('remove-btn')
                rm_btn.set_size_request(28, 28)
                rm_btn.set_tooltip_text('Remove widget')
                rm_btn.connect('clicked', self._on_remove_widget, name)
                card.pack_end(rm_btn, False, False, 0)
            else:
                add_btn = Gtk.Button(label='+ Add')
                add_btn.get_style_context().add_class('add-btn')
                add_btn.connect('clicked', self._on_add_widget, name)
                card.pack_end(add_btn, False, False, 0)

            self.list_box.add(card)

        self.list_box.show_all()

    # ── Widget lifecycle ──────────────────────────────────────────────────────

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
            self.active_widgets[name].close()
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
        with open(ACTIVE_FILE, 'w') as f:
            json.dump(list(self.active_widgets.keys()), f)

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
                except Exception:
                    pass
        self._rebuild_list()

    def _update_widgets(self):
        for name, widget in list(self.active_widgets.items()):
            try:
                widget.refresh()
            except Exception:
                pass
        return True

    # ── Misc ──────────────────────────────────────────────────────────────────

    def _on_delete(self, window, event):
        window.hide()
        return True

    def get_manager_window(self):
        return self.window
