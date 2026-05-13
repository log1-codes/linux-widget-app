import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import json
import os
import threading
import time
from widgets.base_widget import BaseWidget
from manager.widget_manager import register_widget

WEATHER_CACHE = os.path.expanduser('~/.config/widget-app/weather_cache.json')
CACHE_DURATION = 600

class WeatherWidget(BaseWidget):
    def __init__(self, on_delete=None):
        BaseWidget.__init__(self, 'weather', 'Weather', 280, 320, on_delete)
        self.weather_data = None
        self._build_content()
        self._fetch_weather()

    def _build_content(self):
        css = """
            .weather-temp {
                color: rgba(255, 255, 255, 0.9);
                font-size: 40px;
                font-weight: 600;
            }
            .weather-desc {
                color: rgba(255, 255, 255, 0.55);
                font-size: 13px;
                margin-top: 2px;
            }
            .weather-location {
                color: #64b5f6;
                font-size: 12px;
                font-weight: 600;
            }
            .weather-detail {
                color: rgba(255, 255, 255, 0.3);
                font-size: 10px;
                font-weight: 600;
            }
            .weather-detail-value {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                font-weight: 600;
            }
            .weather-update {
                color: rgba(255, 255, 255, 0.2);
                font-size: 9px;
            }
            .weather-header {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                padding: 14px;
            }
            .weather-detail-box {
                background-color: rgba(255, 255, 255, 0.04);
                border-radius: 12px;
                padding: 10px;
                margin: 2px;
            }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.content.pack_start(self.main_vbox, True, True, 0)

        self.loading_label = Gtk.Label(label='Fetching weather...')
        self.loading_label.get_style_context().add_class('weather-desc')
        self.main_vbox.pack_start(self.loading_label, True, True, 0)

    def _fetch_weather(self):
        def fetch():
            data = self._get_cached_weather()
            if data:
                self.weather_data = data
                GLib.idle_add(self._display_weather)
                return

            import requests
            city = 'Unknown'
            lat = 0
            lon = 0
            try:
                loc_resp = requests.get('https://ipapi.co/json/', timeout=5)
                if loc_resp.status_code == 200:
                    location_data = loc_resp.json()
                    city = location_data.get('city', city)
                    lat = location_data.get('latitude', lat)
                    lon = location_data.get('longitude', lon)
                else:
                    loc_resp = requests.get('http://ip-api.com/json/', timeout=5)
                    if loc_resp.status_code == 200:
                        location_data = loc_resp.json()
                        city = location_data.get('city', city)
                        lat = location_data.get('lat', lat)
                        lon = location_data.get('lon', lon)
            except:
                try:
                    loc_resp = requests.get('http://ip-api.com/json/', timeout=5)
                    if loc_resp.status_code == 200:
                        location_data = loc_resp.json()
                        city = location_data.get('city', city)
                        lat = location_data.get('lat', lat)
                        lon = location_data.get('lon', lon)
                except:
                    pass

            try:
                resp = requests.get(
                    f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}'
                    f'&current=temperature_2m,relative_humidity_2m,apparent_temperature,'
                    f'weather_code,wind_speed_10m'
                    f'&timezone=auto',
                    timeout=5
                )

                if resp.status_code == 200:
                    raw = resp.json()
                    current = raw.get('current', {})
                    wmo_code = current.get('weather_code', 0)
                    temp = current.get('temperature_2m')
                    self.weather_data = {
                        'city': city,
                        'temp': f'{temp:.0f}' if temp is not None else '--',
                        'feels_like': f'{current.get("apparent_temperature", 0):.0f}',
                        'humidity': f'{current.get("relative_humidity_2m", "--")}',
                        'wind': f'{current.get("wind_speed_10m", "--")}',
                        'condition': self._wmo_to_text(wmo_code),
                        'emoji': self._wmo_to_emoji(wmo_code),
                    }
                    self._cache_weather(self.weather_data)
                    GLib.idle_add(self._display_weather)
                else:
                    GLib.idle_add(self._show_error, 'Weather API unavailable')
            except Exception as e:
                GLib.idle_add(self._show_error, f'Weather: {str(e)[:25]}')

        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()

    def _display_weather(self):
        for child in self.main_vbox.get_children():
            self.main_vbox.remove(child)

        w = self.weather_data
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.get_style_context().add_class('weather-header')

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        temp_lbl = Gtk.Label(label=f'{w["emoji"]}  {w["temp"]}°C')
        temp_lbl.get_style_context().add_class('weather-temp')
        left.pack_start(temp_lbl, False, False, 0)

        cond_lbl = Gtk.Label(label=w['condition'])
        cond_lbl.get_style_context().add_class('weather-desc')
        cond_lbl.set_xalign(0.0)
        left.pack_start(cond_lbl, False, False, 0)

        city_lbl = Gtk.Label(label=w['city'])
        city_lbl.get_style_context().add_class('weather-location')
        city_lbl.set_xalign(0.0)
        left.pack_start(city_lbl, False, False, 0)

        header.pack_start(left, True, True, 0)
        self.main_vbox.pack_start(header, False, False, 0)

        details = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        items = [
            ('Feels Like', f'{w["feels_like"]}°C'),
            ('Humidity', f'{w["humidity"]}%'),
            ('Wind', f'{w["wind"]} km/h'),
        ]

        for label, value in items:
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.get_style_context().add_class('weather-detail-box')
            lbl = Gtk.Label(label=label)
            lbl.get_style_context().add_class('weather-detail')
            val = Gtk.Label(label=value)
            val.get_style_context().add_class('weather-detail-value')
            box.pack_start(lbl, False, False, 0)
            box.pack_start(val, False, False, 0)
            details.pack_start(box, True, True, 0)

        self.main_vbox.pack_start(details, False, False, 0)

        self.main_vbox.show_all()

    def _show_error(self, msg):
        for child in self.main_vbox.get_children():
            self.main_vbox.remove(child)
        err_lbl = Gtk.Label(label=f'⚠ {msg}')
        err_lbl.get_style_context().add_class('weather-desc')
        self.main_vbox.pack_start(err_lbl, True, True, 0)
        self.main_vbox.show_all()

    def _wmo_to_text(self, code):
        codes = {
            0: 'Clear Sky', 1: 'Mainly Clear', 2: 'Partly Cloudy', 3: 'Overcast',
            45: 'Foggy', 48: 'Depositing Rime Fog',
            51: 'Light Drizzle', 53: 'Moderate Drizzle', 55: 'Dense Drizzle',
            56: 'Freezing Light Drizzle', 57: 'Freezing Dense Drizzle',
            61: 'Slight Rain', 63: 'Moderate Rain', 65: 'Heavy Rain',
            66: 'Freezing Light Rain', 67: 'Freezing Heavy Rain',
            71: 'Slight Snow', 73: 'Moderate Snow', 75: 'Heavy Snow',
            77: 'Snow Grains',
            80: 'Slight Rain Showers', 81: 'Moderate Rain Showers', 82: 'Violent Rain Showers',
            85: 'Slight Snow Showers', 86: 'Heavy Snow Showers',
            95: 'Thunderstorm', 96: 'Thunderstorm with Hail', 99: 'Thunderstorm with Heavy Hail',
        }
        return codes.get(code, f'Code {code}')

    def _wmo_to_emoji(self, code):
        if code == 0: return '☀️'
        if code <= 2: return '⛅'
        if code == 3: return '☁️'
        if code in (45, 48): return '🌫️'
        if code <= 57: return '🌦️'
        if code <= 67: return '🌧️'
        if code <= 77: return '🌨️'
        if code <= 86: return '🌦️'
        return '⛈️'

    def _get_cached_weather(self):
        if os.path.exists(WEATHER_CACHE):
            try:
                with open(WEATHER_CACHE) as f:
                    data = json.load(f)
                if time.time() - data.get('timestamp', 0) < CACHE_DURATION:
                    return data.get('data')
            except:
                pass
        return None

    def _cache_weather(self, data):
        with open(WEATHER_CACHE, 'w') as f:
            json.dump({'data': data, 'timestamp': time.time()}, f)

    def refresh(self):
        self._fetch_weather()

register_widget('weather', 'Weather', WeatherWidget, '🌤')
