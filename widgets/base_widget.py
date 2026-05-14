"""
BaseWidget – shared foundation for all desktop widgets.

Key Wayland/XWayland notes:
  • We run under GDK_BACKEND=x11 (XWayland) so Gdk.WindowTypeHint.DOCK
    works AND keyboard input is delivered.
  • NORMAL type-hint is used so GNOME/Mutter still passes key events
    to the window even without explicit focus grabs.
  • Colors use a macOS-inspired frosted-glass palette that is readable
    on any wallpaper: semi-transparent dark background + vivid accent text.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf
import cairo
import json
import os
import math

CONFIG_DIR = os.path.expanduser('~/.config/widget-app')
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_DIR, 'widgets.json')
CORNER_RADIUS = 20

# ── macOS-inspired colour palette (works on light AND dark wallpapers) ────────
# Background: rich dark navy at ~78% opacity — enough contrast on any wallpaper
# Text:       pure white at various opacities — always legible over dark bg
# Accent:     Apple "Blue" #0A84FF / translucent tint for highlights
PALETTE_CSS = """
    .widget-outer {
        background-color: rgba(20, 20, 30, 0.82);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.14);
    }
    .title-bar {
        background-color: rgba(255, 255, 255, 0.055);
        border-radius: 20px 20px 0 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.07);
    }
    .title-bar:hover {
        background-color: rgba(255, 255, 255, 0.10);
    }
    .title-label {
        color: rgba(255, 255, 255, 0.90);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .close-btn {
        color: rgba(255, 255, 255, 0.45);
        font-size: 15px;
        font-weight: 300;
        background: transparent;
        border: none;
        padding: 0;
        min-width: 24px;
        min-height: 24px;
    }
    .close-btn:hover {
        color: #ff453a;
        background-color: rgba(255, 69, 58, 0.18);
        border-radius: 50%;
    }
    .widget-content {
        background: transparent;
    }
    /* ── Generic text helpers used across widgets ── */
    .text-primary {
        color: rgba(255, 255, 255, 0.92);
    }
    .text-secondary {
        color: rgba(255, 255, 255, 0.52);
    }
    .text-muted {
        color: rgba(255, 255, 255, 0.30);
    }
    .accent-blue {
        color: #64b5f6;
    }
    .accent-green {
        color: #30d158;
    }
    .accent-red {
        color: #ff453a;
    }
    .inset-card {
        background-color: rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
"""


class BaseWidget(Gtk.Window):
    instances = []

    def __init__(self, widget_id, title, default_w=300, default_h=300, on_delete=None):
        Gtk.Window.__init__(self)
        self.widget_id = widget_id
        self.on_delete = on_delete
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self._resizing = False
        self._resize_edge = None
        self._resize_start_x = 0
        self._resize_start_y = 0
        self._resize_start_w = default_w
        self._resize_start_h = default_h

        self.set_default_size(default_w, default_h)
        self.set_decorated(False)
        self.set_keep_below(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_app_paintable(True)
        self.set_resizable(True)
        self.stick()

        # NORMAL hint keeps keyboard input working under XWayland on GNOME.
        # DOCK disables keyboard focus in Wayland security model.
        self.set_type_hint(Gdk.WindowTypeHint.NORMAL)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.set_position(Gtk.WindowPosition.NONE)
        self._build_title_bar(title)

        self.connect('realize', self._on_realize)
        self.connect('draw', self._on_draw_bg)
        self.connect('button-press-event', self._on_button_press)
        self.connect('button-release-event', self._on_button_release)
        self.connect('motion-notify-event', self._on_motion)
        self.connect('key-press-event', self._on_key_press)
        self.set_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.KEY_PRESS_MASK
        )

        BaseWidget.instances.append(self)

    # ── Window shape ──────────────────────────────────────────────────────────

    def _on_realize(self, widget):
        self._shape_window()

    def _shape_window(self):
        w = self.get_allocation().width
        h = self.get_allocation().height
        if w <= 0 or h <= 0:
            return
        r = CORNER_RADIUS
        mask = cairo.ImageSurface(cairo.FORMAT_A8, w, h)
        cr = cairo.Context(mask)
        cr.set_source_rgba(1, 1, 1, 1)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.new_path()
        cr.arc(r, r, r, math.pi, 3 * math.pi / 2)
        cr.arc(w - r, r, r, 3 * math.pi / 2, 2 * math.pi)
        cr.arc(w - r, h - r, r, 0, math.pi / 2)
        cr.arc(r, h - r, r, math.pi / 2, math.pi)
        cr.close_path()
        cr.fill()
        region = Gdk.cairo_region_create_from_surface(mask)
        self.get_window().shape_combine_region(region, 0, 0)
        self.get_window().input_shape_combine_region(region, 0, 0)

    # ── Title bar & layout ────────────────────────────────────────────────────

    def _build_title_bar(self, title):
        self.outer_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.outer_box.get_style_context().add_class('widget-outer')
        self.add(self.outer_box)

        self.title_bar = Gtk.EventBox()
        self.title_bar.get_style_context().add_class('title-bar')
        self.title_bar.set_size_request(-1, 34)
        self.title_bar.connect('button-press-event', self._on_title_press)
        self.title_bar.connect('button-release-event', self._on_title_release)
        self.title_bar.connect('motion-notify-event', self._on_title_motion)

        title_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        title_hbox.set_margin_start(10)
        title_hbox.set_margin_end(6)
        title_hbox.set_margin_top(5)
        title_hbox.set_margin_bottom(5)

        self.title_label = Gtk.Label(label=title.upper())
        self.title_label.set_xalign(0.0)
        self.title_label.get_style_context().add_class('title-label')

        close_btn = Gtk.Button(label='×')
        close_btn.set_relief(Gtk.ReliefStyle.NONE)
        close_btn.set_size_request(24, 24)
        close_btn.connect('clicked', self._on_close)
        close_btn.get_style_context().add_class('close-btn')
        close_btn.set_tooltip_text('Remove widget')

        title_hbox.pack_start(self.title_label, True, True, 0)
        title_hbox.pack_end(close_btn, False, False, 0)
        self.title_bar.add(title_hbox)
        self.outer_box.pack_start(self.title_bar, False, False, 0)

        self.content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.content.set_margin_start(8)
        self.content.set_margin_end(8)
        self.content.set_margin_bottom(8)
        self.outer_box.pack_start(self.content, True, True, 0)

        self._apply_css()

    def _apply_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(PALETTE_CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _on_draw_bg(self, widget, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        return False

    # ── Drag (title bar) ──────────────────────────────────────────────────────

    def _on_title_press(self, widget, event):
        if event.button == 1:
            self._drag_start_x = event.x_root
            self._drag_start_y = event.y_root
            x, y = self.get_position()
            self._drag_offset_x = int(event.x_root - x)
            self._drag_offset_y = int(event.y_root - y)
            return True
        return False

    def _on_title_release(self, widget, event):
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.save_position()

    def _on_title_motion(self, widget, event):
        if self._drag_start_x != 0 and self._drag_start_y != 0:
            new_x = int(event.x_root - self._drag_offset_x)
            new_y = int(event.y_root - self._drag_offset_y)
            self.move(new_x, new_y)
            return True
        return False

    # ── Resize + whole-window drag ────────────────────────────────────────────

    def _on_button_press(self, widget, event):
        if event.button == 1:
            alloc = self.get_allocation()
            edge = self._get_resize_edge(event.x, event.y, alloc)
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._resize_start_x = int(event.x_root)
                self._resize_start_y = int(event.y_root)
                self._resize_start_w = alloc.width
                self._resize_start_h = alloc.height
                return True
        return False

    def _on_button_release(self, widget, event):
        if event.button == 1:
            self._resizing = False
            self._resize_edge = None
            self.save_position()
            return True
        return False

    def _on_motion(self, widget, event):
        alloc = self.get_allocation()
        edge = self._get_resize_edge(event.x, event.y, alloc)
        if edge:
            self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.BOTTOM_RIGHT_CORNER))
        elif not self._resizing:
            self.get_window().set_cursor(Gdk.Cursor(Gdk.CursorType.LEFT_PTR))

        if self._resizing and self._resize_edge:
            dx = int(event.x_root - self._resize_start_x)
            dy = int(event.y_root - self._resize_start_y)
            new_w = max(150, self._resize_start_w + dx)
            new_h = max(150, self._resize_start_h + dy)
            self.resize(new_w, new_h)
            self._shape_window()
            return True
        return False

    def _get_resize_edge(self, x, y, alloc):
        margin = 14
        if x >= alloc.width - margin and y >= alloc.height - margin:
            return 'se'
        return None

    # ── Close / Key ───────────────────────────────────────────────────────────

    def _on_close(self, btn):
        self.close()

    def close(self):
        self.save_position()
        self.hide()
        if self.on_delete:
            self.on_delete(self)
        if self in BaseWidget.instances:
            BaseWidget.instances.remove(self)
        self.destroy()

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False

    # ── Position persistence ──────────────────────────────────────────────────

    def save_position(self):
        x, y = self.get_position()
        w, h = self.get_size()
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}
        data[self.widget_id] = {'x': x, 'y': y, 'w': w, 'h': h}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def load_position(self):
        self._position_loaded = False
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                try:
                    data = json.load(f)
                    if self.widget_id in data:
                        pos = data[self.widget_id]
                        if 'x' in pos and 'y' in pos:
                            self.move(pos['x'], pos['y'])
                            self._position_loaded = True
                        if 'w' in pos and 'h' in pos:
                            self.resize(max(150, pos['w']), max(150, pos['h']))
                            self._shape_window()
                except Exception:
                    pass

    # ── Subclass hook ─────────────────────────────────────────────────────────

    def refresh(self):
        pass
