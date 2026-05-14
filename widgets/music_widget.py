import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import dbus
import dbus.mainloop.glib
from widgets.base_widget import BaseWidget
from manager.widget_manager import register_widget

MUSIC_CSS = """
    .music-title {
        color: rgba(255, 255, 255, 0.92);
        font-size: 14px;
        font-weight: 600;
    }
    .music-artist {
        color: rgba(255, 255, 255, 0.52);
        font-size: 12px;
    }
    .music-album {
        color: rgba(255, 255, 255, 0.30);
        font-size: 11px;
    }
    .music-status-play {
        color: #30d158;
        font-size: 11px;
        font-weight: 600;
    }
    .music-status-pause {
        color: rgba(255, 255, 255, 0.40);
        font-size: 11px;
    }
    .music-idle {
        color: rgba(255, 255, 255, 0.30);
        font-size: 13px;
    }
    .music-art {
        background-color: rgba(255, 255, 255, 0.07);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
"""

PLAYERS = [
    'org.mpris.MediaPlayer2.spotify',
    'org.mpris.MediaPlayer2.vlc',
    'org.mpris.MediaPlayer2.rhythmbox',
    'org.mpris.MediaPlayer2.firefox',
    'org.mpris.MediaPlayer2.chromium',
    'org.mpris.MediaPlayer2.mpv',
]


class NowPlayingWidget(BaseWidget):
    def __init__(self, on_delete=None):
        BaseWidget.__init__(self, 'now_playing', 'Now Playing', 300, 160, on_delete)
        self._setup_dbus()
        self._apply_music_css()
        self._build_content()

    def _apply_music_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(MUSIC_CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _setup_dbus(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        try:
            self.bus = dbus.SessionBus()
            self.bus.add_signal_receiver(
                self._on_properties_changed,
                dbus_interface='org.freedesktop.DBus.Properties',
                signal_name='PropertiesChanged',
            )
        except Exception:
            self.bus = None

    def _on_properties_changed(self, interface, changed, invalidated):
        if interface == 'org.mpris.MediaPlayer2.Player':
            GLib.idle_add(self._update_track_info)

    def _build_content(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        main_box.set_margin_top(6)
        main_box.set_margin_bottom(4)

        # Art placeholder
        art_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        art_box.get_style_context().add_class('music-art')
        art_box.set_size_request(58, 58)
        self.art_lbl = Gtk.Label(label='🎵')
        self.art_lbl.set_size_request(58, 58)
        art_box.pack_start(self.art_lbl, True, True, 0)
        main_box.pack_start(art_box, False, False, 0)

        # Info
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info_box.set_valign(Gtk.Align.CENTER)

        self.title_lbl = Gtk.Label(label='No music playing')
        self.title_lbl.get_style_context().add_class('music-idle')
        self.title_lbl.set_xalign(0.0)
        self.title_lbl.set_ellipsize(3)  # PANGO_ELLIPSIZE_END

        self.artist_lbl = Gtk.Label(label='')
        self.artist_lbl.get_style_context().add_class('music-artist')
        self.artist_lbl.set_xalign(0.0)
        self.artist_lbl.set_ellipsize(3)

        self.album_lbl = Gtk.Label(label='')
        self.album_lbl.get_style_context().add_class('music-album')
        self.album_lbl.set_xalign(0.0)
        self.album_lbl.set_ellipsize(3)

        self.status_lbl = Gtk.Label(label='Open Spotify, VLC, or mpv')
        self.status_lbl.get_style_context().add_class('music-idle')
        self.status_lbl.set_xalign(0.0)

        info_box.pack_start(self.title_lbl, False, False, 0)
        info_box.pack_start(self.artist_lbl, False, False, 0)
        info_box.pack_start(self.album_lbl, False, False, 0)
        info_box.pack_start(self.status_lbl, False, False, 0)
        main_box.pack_start(info_box, True, True, 0)

        self.content.pack_start(main_box, True, True, 0)
        self._update_track_info()

    def _update_track_info(self):
        if not self.bus:
            return
        for player in PLAYERS:
            try:
                obj = self.bus.get_object(player, '/org/mpris/MediaPlayer2')
                props = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')
                metadata = props.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
                playback = props.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')

                title  = str(metadata.get('xesam:title', 'Unknown'))
                artist = str((metadata.get('xesam:artist') or ['Unknown'])[0])
                album  = str(metadata.get('xesam:album', ''))

                self.title_lbl.set_text(title)
                self.title_lbl.get_style_context().remove_class('music-idle')
                self.title_lbl.get_style_context().add_class('music-title')
                self.artist_lbl.set_text(artist)
                self.album_lbl.set_text(album)

                if str(playback) == 'Playing':
                    self.status_lbl.set_text('▶  Playing')
                    self.status_lbl.get_style_context().remove_class('music-idle')
                    self.status_lbl.get_style_context().remove_class('music-status-pause')
                    self.status_lbl.get_style_context().add_class('music-status-play')
                else:
                    self.status_lbl.set_text('⏸  Paused')
                    self.status_lbl.get_style_context().remove_class('music-idle')
                    self.status_lbl.get_style_context().remove_class('music-status-play')
                    self.status_lbl.get_style_context().add_class('music-status-pause')
                return
            except Exception:
                continue

        # Nothing playing
        self.title_lbl.set_text('No music playing')
        self.title_lbl.get_style_context().remove_class('music-title')
        self.title_lbl.get_style_context().add_class('music-idle')
        self.artist_lbl.set_text('')
        self.album_lbl.set_text('')
        self.status_lbl.set_text('Open Spotify, VLC, or mpv')
        self.status_lbl.get_style_context().remove_class('music-status-play')
        self.status_lbl.get_style_context().remove_class('music-status-pause')
        self.status_lbl.get_style_context().add_class('music-idle')

    def refresh(self):
        self._update_track_info()


register_widget('now_playing', 'Now Playing', NowPlayingWidget, '🎵')
