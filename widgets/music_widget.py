import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import dbus
import dbus.mainloop.glib
from widgets.base_widget import BaseWidget
from manager.widget_manager import register_widget

class NowPlayingWidget(BaseWidget):
    def __init__(self, on_delete=None):
        BaseWidget.__init__(self, 'now_playing', 'Now Playing', 300, 160, on_delete)
        self.current_track = None
        self._setup_dbus()
        self._build_content()

    def _setup_dbus(self):
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        try:
            self.bus = dbus.SessionBus()
            self.bus.add_signal_receiver(
                self._on_properties_changed,
                dbus_interface='org.freedesktop.DBus.Properties',
                signal_name='PropertiesChanged',
            )
        except:
            self.bus = None

    def _on_properties_changed(self, interface, changed, invalidated):
        if interface == 'org.mpris.MediaPlayer2.Player':
            GLib.idle_add(self._update_track_info)

    def _build_content(self):
        css = """
            .music-title {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                font-weight: 600;
            }
            .music-artist {
                color: rgba(255, 255, 255, 0.5);
                font-size: 12px;
            }
            .music-album {
                color: rgba(255, 255, 255, 0.3);
                font-size: 11px;
            }
            .music-status {
                color: rgba(255, 255, 255, 0.5);
                font-size: 11px;
            }
            .music-progress-box {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 14px;
                padding: 12px;
            }
            .music-idle {
                color: rgba(255, 255, 255, 0.3);
                font-size: 13px;
            }
            .music-art {
                border-radius: 10px;
            }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.main_box.set_margin_top(4)

        self.art_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.art_box.set_size_request(60, 60)

        self.art_placeholder = Gtk.Label(label='🎵')
        self.art_placeholder.set_size_request(60, 60)
        self.art_box.pack_start(self.art_placeholder, True, True, 0)

        self.main_box.pack_start(self.art_box, False, False, 0)

        self.info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.info_box.set_valign(Gtk.Align.CENTER)

        self.title_lbl = Gtk.Label(label='No music playing')
        self.title_lbl.get_style_context().add_class('music-idle')
        self.title_lbl.set_xalign(0.0)
        self.info_box.pack_start(self.title_lbl, False, False, 0)

        self.artist_lbl = Gtk.Label(label='')
        self.artist_lbl.get_style_context().add_class('music-artist')
        self.artist_lbl.set_xalign(0.0)
        self.info_box.pack_start(self.artist_lbl, False, False, 0)

        self.album_lbl = Gtk.Label(label='')
        self.album_lbl.get_style_context().add_class('music-album')
        self.album_lbl.set_xalign(0.0)
        self.info_box.pack_start(self.album_lbl, False, False, 0)

        self.status_lbl = Gtk.Label(label='')
        self.status_lbl.get_style_context().add_class('music-status')
        self.status_lbl.set_xalign(0.0)
        self.info_box.pack_start(self.status_lbl, False, False, 0)

        self.main_box.pack_start(self.info_box, True, True, 0)
        self.content.pack_start(self.main_box, True, True, 0)

        self._update_track_info()

    def _update_track_info(self):
        self._try_other_players()

    def _try_other_players(self):
        players = ['org.mpris.MediaPlayer2.spotify',
                    'org.mpris.MediaPlayer2.vlc',
                    'org.mpris.MediaPlayer2.rhythmbox',
                    'org.mpris.MediaPlayer2.firefox',
                    'org.mpris.MediaPlayer2.chromium',
                    'org.mpris.MediaPlayer2.mpv']
        for player in players:
            try:
                obj = self.bus.get_object(player, '/org/mpris/MediaPlayer2')
                props = dbus.Interface(obj, 'org.freedesktop.DBus.Properties')
                metadata = props.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
                playback = props.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus')

                title = str(metadata.get('xesam:title', 'Unknown'))
                artist = str(metadata.get('xesam:artist', ['Unknown'])[0])
                album = str(metadata.get('xesam:album', ''))

                self.title_lbl.set_text(title)
                self.title_lbl.get_style_context().remove_class('music-idle')
                self.title_lbl.get_style_context().add_class('music-title')
                self.artist_lbl.set_text(artist)
                self.album_lbl.set_text(album)
                self.status_lbl.set_text('▶ Playing' if playback == 'Playing' else '⏸ Paused')
                self.art_placeholder.set_text('🎵')
                return
            except:
                continue

        self.title_lbl.set_text('No music playing')
        self.title_lbl.get_style_context().remove_class('music-title')
        self.title_lbl.get_style_context().add_class('music-idle')
        self.artist_lbl.set_text('')
        self.album_lbl.set_text('')
        self.status_lbl.set_text('Open Spotify or VLC to see playback')
        self.art_placeholder.set_text('🎵')

    def refresh(self):
        self._update_track_info()

register_widget('now_playing', 'Now Playing', NowPlayingWidget, '🎵')
