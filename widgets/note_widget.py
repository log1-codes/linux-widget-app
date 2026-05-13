import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import json
import os
from datetime import datetime
from widgets.base_widget import BaseWidget
from manager.widget_manager import register_widget

NOTES_FILE = os.path.expanduser('~/.config/widget-app/notes.json')

class NoteWidget(BaseWidget):
    def __init__(self, on_delete=None):
        BaseWidget.__init__(self, 'note', 'Quick Note', 280, 250, on_delete)
        self.current_note = ''
        self._load_notes()
        self._build_content()

    def _build_content(self):
        css = """
            .note-textview {
                background-color: transparent;
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
            }
            .note-textview text {
                background-color: rgba(255, 255, 255, 0.04);
                color: rgba(255, 255, 255, 0.9);
                border-radius: 12px;
                padding: 10px;
            }
            .note-status {
                color: rgba(255, 255, 255, 0.3);
                font-size: 10px;
            }
            .note-timestamp {
                color: rgba(255, 255, 255, 0.2);
                font-size: 10px;
            }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.textview = Gtk.TextView()
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.textview.get_style_context().add_class('note-textview')
        self.textview.set_accepts_tab(False)
        self.buffer = self.textview.get_buffer()

        if self.current_note:
            self.buffer.set_text(self.current_note)

        self.buffer.connect('changed', self._on_text_changed)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add(self.textview)
        self.content.pack_start(scroll, True, True, 0)

        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.status_lbl = Gtk.Label(label=self.current_note and 'Saved' or 'Empty')
        self.status_lbl.get_style_context().add_class('note-status')
        self.status_lbl.set_xalign(0.0)
        bottom.pack_start(self.status_lbl, True, True, 0)

        self.time_lbl = Gtk.Label(label='')
        self.time_lbl.get_style_context().add_class('note-timestamp')
        bottom.pack_end(self.time_lbl, False, False, 0)

        self.content.pack_start(bottom, False, False, 0)

        self._save_timer_id = None

    def _on_text_changed(self, buffer):
        if self._save_timer_id:
            GLib.source_remove(self._save_timer_id)
        self._save_timer_id = GLib.timeout_add(1000, self._save_note)
        self.status_lbl.set_text('Unsaved...')

    def _save_note(self):
        start_iter = self.buffer.get_start_iter()
        end_iter = self.buffer.get_end_iter()
        text = self.buffer.get_text(start_iter, end_iter, True)
        self.current_note = text

        notes = {'note': text, 'updated': datetime.now().isoformat()}
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f, indent=2)

        self.status_lbl.set_text('Saved')
        now = datetime.now()
        self.time_lbl.set_text(now.strftime('%H:%M'))
        self._save_timer_id = None
        return False

    def _load_notes(self):
        if os.path.exists(NOTES_FILE):
            try:
                with open(NOTES_FILE) as f:
                    data = json.load(f)
                    self.current_note = data.get('note', '')
            except:
                self.current_note = ''

    def refresh(self):
        pass

register_widget('note', 'Quick Note', NoteWidget, '📝')
