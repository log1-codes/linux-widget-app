import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import json
import os
import threading
import time
from widgets.base_widget import BaseWidget
from manager.widget_manager import register_widget

WEATHER_CACHE = os.path.expanduser('~/.config/widget-app/weather_cache.json')
CACHE_DURATION = 600

WEATHER_CSS = """
    .weather-temp {
        color: rgba(255, 255, 255, 0.92);
        font-size: 38px;
        font-weight: 600;
    }
    .weather-desc {
        color: rgba(255, 255, 255, 0.52);
        font-size: 13px;
    }
    .weather-location {
        color: #64b5f6;
        font-size: 12px;
        font-weight: 600;
    }
    .weather-header {
        background-color: rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.07);
        padding: 12px;
    }
    .weather-detail-box {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 8px;
        margin: 2px;
    }
    .weather-detail-lbl {
        color: rgba(255, 255, 255, 0.32);
        font-size: 10px;
        font-weight: 600;
    }
    .weather-detail-val {
        color: rgba(255, 255, 255, 0.88);
        font-size: 13px;
        font-weight: 600;
    }
"""

WMO_TEXT = {
    0: 'Clear Sky', 1: 'Mainly Clear', 2: 'Partly Cloudy', 3: 'Overcast',
    45: 'Foggy', 48: 'Rime Fog',
    51: 'Light Drizzle', 53: 'Drizzle', 55: 'Heavy Drizzle',
    61: 'Light Rain', 63: 'Rain', 65: 'Heavy Rain',
    71: 'Light Snow', 73: 'Snow', 75: 'Heavy Snow',
    80: 'Rain Showers', 81: 'Showers', 82: 'Violent Showers',
    95: 'Thunderstorm', 96: 'Hail Storm', 99: 'Heavy Hail Storm',
}

def _wmo_text(c):
    return WMO_TEXT.get(c, f'Code {c}')

def _wmo_emoji(c):
    if c == 0: return '☀️'
    if c <= 2: return '⛅'
    if c == 3: return '☁️'
    if c in (45, 48): return '🌫️'
    if c <= 67: return '🌧️'
    if c <= 77: return '🌨️'
    if c <= 86: return '🌦️'
    return '⛈️'


class WeatherWidget(BaseWidget):
    def __init__(self, on_delete=None):
        BaseWidget.__init__(self, 'weather', 'Weather', 280, 300, on_delete)
        self.weather_data = None
        self._apply_weather_css()
        self._build_content()
        self._fetch_weather()

    def _apply_weather_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(WEATHER_CSS.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_content(self):
        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.main_vbox.set_margin_top(6)
        self.content.pack_start(self.main_vbox, True, True, 0)

        loading = Gtk.Label(label='Fetching weather…')
        loading.get_style_context().add_class('weather-desc')
        self.main_vbox.pack_start(loading, True, True, 0)

    def _fetch_weather(self):
        def fetch():
            data = self._get_cached()
            if data:
                self.weather_data = data
                GLib.idle_add(self._display)
                return
            try:
                import requests
                city, lat, lon = 'Unknown', 0, 0
                for url in ('https://ipapi.co/json/', 'http://ip-api.com/json/'):
                    try:
                        r = requests.get(url, timeout=5)
                        if r.status_code == 200:
                            j = r.json()
                            city = j.get('city', city)
                            lat  = j.get('latitude', j.get('lat', lat))
                            lon  = j.get('longitude', j.get('lon', lon))
                            break
                    except Exception:
                        continue

                r = requests.get(
                    f'https://api.open-meteo.com/v1/forecast'
                    f'?latitude={lat}&longitude={lon}'
                    f'&current=temperature_2m,relative_humidity_2m,'
                    f'apparent_temperature,weather_code,wind_speed_10m'
                    f'&timezone=auto',
                    timeout=5
                )
                if r.status_code == 200:
                    cur = r.json().get('current', {})
                    code = cur.get('weather_code', 0)
                    temp = cur.get('temperature_2m')
                    self.weather_data = {
                        'city':       city,
                        'temp':       f'{temp:.0f}' if temp is not None else '--',
                        'feels_like': f'{cur.get("apparent_temperature", 0):.0f}',
                        'humidity':   str(cur.get('relative_humidity_2m', '--')),
                        'wind':       str(cur.get('wind_speed_10m', '--')),
                        'condition':  _wmo_text(code),
                        'emoji':      _wmo_emoji(code),
                    }
                    self._cache(self.weather_data)
                    GLib.idle_add(self._display)
                else:
                    GLib.idle_add(self._show_error, 'Weather API unavailable')
            except Exception as e:
                GLib.idle_add(self._show_error, str(e)[:30])

        threading.Thread(target=fetch, daemon=True).start()

    def _display(self):
        for child in self.main_vbox.get_children():
            self.main_vbox.remove(child)

        w = self.weather_data
        header = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        header.get_style_context().add_class('weather-header')

        temp_lbl = Gtk.Label(label=f'{w["emoji"]}  {w["temp"]}°C')
        temp_lbl.get_style_context().add_class('weather-temp')
        temp_lbl.set_xalign(0.0)

        cond_lbl = Gtk.Label(label=w['condition'])
        cond_lbl.get_style_context().add_class('weather-desc')
        cond_lbl.set_xalign(0.0)

        city_lbl = Gtk.Label(label=w['city'])
        city_lbl.get_style_context().add_class('weather-location')
        city_lbl.set_xalign(0.0)

        header.pack_start(temp_lbl, False, False, 0)
        header.pack_start(cond_lbl, False, False, 0)
        header.pack_start(city_lbl, False, False, 0)
        self.main_vbox.pack_start(header, False, False, 0)

        details = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        for label, value in [
            ('Feels Like', f'{w["feels_like"]}°C'),
            ('Humidity',   f'{w["humidity"]}%'),
            ('Wind',       f'{w["wind"]} km/h'),
        ]:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.get_style_context().add_class('weather-detail-box')
            lbl = Gtk.Label(label=label.upper())
            lbl.get_style_context().add_class('weather-detail-lbl')
            val = Gtk.Label(label=value)
            val.get_style_context().add_class('weather-detail-val')
            box.pack_start(lbl, False, False, 0)
            box.pack_start(val, False, False, 0)
            details.pack_start(box, True, True, 0)

        self.main_vbox.pack_start(details, False, False, 0)
        self.main_vbox.show_all()

    def _show_error(self, msg):
        for child in self.main_vbox.get_children():
            self.main_vbox.remove(child)
        err = Gtk.Label(label=f'⚠  {msg}')
        err.get_style_context().add_class('weather-desc')
        self.main_vbox.pack_start(err, True, True, 0)
        self.main_vbox.show_all()

    def _get_cached(self):
        if os.path.exists(WEATHER_CACHE):
            try:
                with open(WEATHER_CACHE) as f:
                    data = json.load(f)
                if time.time() - data.get('timestamp', 0) < CACHE_DURATION:
                    return data.get('data')
            except Exception:
                pass
        return None

    def _cache(self, data):
        with open(WEATHER_CACHE, 'w') as f:
            json.dump({'data': data, 'timestamp': time.time()}, f)

    def refresh(self):
        self._fetch_weather()


register_widget('weather', 'Weather', WeatherWidget, '🌤')
