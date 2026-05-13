import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import math
import time
from datetime import datetime
from widgets.base_widget import BaseWidget
from manager.widget_manager import register_widget

class AnalogClockWidget(BaseWidget):
    def __init__(self, on_delete=None):
        BaseWidget.__init__(self, 'analog_clock', 'Clock', 280, 320, on_delete)
        self._refresh_id = None
        self._build_clock()

    def _build_clock(self):
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_hexpand(True)
        self.drawing_area.set_vexpand(True)
        self.drawing_area.connect('draw', self._on_draw_clock)
        self.content.pack_start(self.drawing_area, True, True, 0)

        self.digital_label = Gtk.Label()
        self.digital_label.get_style_context().add_class('digital-label')
        self.digital_label.set_margin_top(4)
        self.content.pack_start(self.digital_label, False, False, 0)

        self.date_label = Gtk.Label()
        self.date_label.get_style_context().add_class('date-label')
        self.content.pack_start(self.date_label, False, False, 0)

        css = """
            .digital-label {
                color: rgba(255, 255, 255, 0.9);
                font-size: 22px;
                font-weight: 600;
            }
            .date-label {
                color: rgba(255, 255, 255, 0.45);
                font-size: 12px;
            }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self._refresh_id = GLib.timeout_add(200, self._tick)

    def _tick(self):
        now = datetime.now()
        self.digital_label.set_text(now.strftime('%H:%M:%S'))
        self.date_label.set_text(now.strftime('%A, %B %d'))
        self.drawing_area.queue_draw()
        return True

    def _on_draw_clock(self, widget, cr):
        alloc = widget.get_allocation()
        cx = alloc.width / 2
        cy = alloc.height / 2
        radius = min(cx, cy) - 12

        cr.set_source_rgba(0.15, 0.15, 0.25, 0.6)
        cr.arc(cx, cy, radius + 6, 0, 2 * math.pi)
        cr.fill()

        cr.set_source_rgba(0.25, 0.25, 0.4, 0.5)
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.fill()

        cr.set_source_rgba(1, 1, 1, 0.03)
        cr.arc(cx, cy, radius - 2, 0, 2 * math.pi)
        cr.fill()

        for i in range(60):
            angle = i * 6 * math.pi / 180 - math.pi / 2
            if i % 5 == 0:
                inner_r = radius - 16
                outer_r = radius - 4
                cr.set_source_rgba(0.8, 0.85, 0.95, 0.9)
                cr.set_line_width(2.5)
            else:
                inner_r = radius - 10
                outer_r = radius - 4
                cr.set_source_rgba(0.6, 0.65, 0.8, 0.4)
                cr.set_line_width(1.5)
            cr.move_to(cx + inner_r * math.cos(angle), cy + inner_r * math.sin(angle))
            cr.line_to(cx + outer_r * math.cos(angle), cy + outer_r * math.sin(angle))
            cr.stroke()

        now = datetime.now()
        hours = now.hour % 12
        minutes = now.minute
        seconds = now.second + now.microsecond / 1000000.0

        hour_angle = (hours + minutes / 60.0) * 30 * math.pi / 180 - math.pi / 2
        hour_len = radius * 0.5
        cr.set_source_rgba(0.54, 0.71, 0.98, 0.95)
        cr.set_line_width(4)
        cr.set_line_cap(2)
        cr.move_to(cx, cy)
        cr.line_to(cx + hour_len * math.cos(hour_angle), cy + hour_len * math.sin(hour_angle))
        cr.stroke()

        min_angle = (minutes + seconds / 60.0) * 6 * math.pi / 180 - math.pi / 2
        min_len = radius * 0.7
        cr.set_source_rgba(0.76, 0.83, 0.96, 0.9)
        cr.set_line_width(2.5)
        cr.move_to(cx, cy)
        cr.line_to(cx + min_len * math.cos(min_angle), cy + min_len * math.sin(min_angle))
        cr.stroke()

        sec_angle = seconds * 6 * math.pi / 180 - math.pi / 2
        sec_len = radius * 0.75
        cr.set_source_rgba(0.95, 0.55, 0.66, 0.85)
        cr.set_line_width(1.5)
        cr.move_to(cx, cy)
        cr.line_to(cx + sec_len * math.cos(sec_angle), cy + sec_len * math.sin(sec_angle))
        cr.stroke()

        cr.set_source_rgba(0.95, 0.55, 0.66, 0.9)
        cr.arc(cx, cy, 4, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgba(0.8, 0.85, 0.95, 0.5)
        cr.arc(cx, cy, 2, 0, 2 * math.pi)
        cr.fill()

    def refresh(self):
        pass

    def close(self):
        if self._refresh_id:
            GLib.source_remove(self._refresh_id)
        super().close()

register_widget('analog_clock', 'Analog Clock', AnalogClockWidget, '🕐')
