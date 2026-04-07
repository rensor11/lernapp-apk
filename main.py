"""
LernApp Server - Android APK
============================
Startet automatisch einen Flask-Webserver wenn die App geöffnet wird.
Zugriff vom PC via: http://<Handy-IP>:5000
"""

import threading
import socket
import os
import sys

# ─── Kivy Setup (muss VOR kivy imports gesetzt werden) ────────────────────────
os.environ['KIVY_NO_ENV_CONFIG'] = '1'
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

# ─── Flask Server Import ───────────────────────────────────────────────────────
from flask_server import create_app, get_fragenpool_path

# ─── Globale Variablen ────────────────────────────────────────────────────────
server_thread = None
server_running = False
flask_app = None
PORT = 5000

# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def get_local_ip():
    """Gibt die lokale IP-Adresse des Geräts zurück."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def start_flask_server():
    """Startet den Flask-Server in einem eigenen Thread."""
    global flask_app, server_running
    try:
        flask_app = create_app()
        server_running = True
        flask_app.run(
            host='0.0.0.0',
            port=PORT,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        print(f"[SERVER ERROR] {e}")
        server_running = False

def stop_flask_server():
    """Stoppt den Flask-Server."""
    global server_running
    import requests
    try:
        requests.post(f'http://localhost:{PORT}/api/shutdown', timeout=2)
    except Exception:
        pass
    server_running = False

# ─── Kivy UI ──────────────────────────────────────────────────────────────────

class ServerUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [20, 40, 20, 20]
        self.spacing = 15

        # Hintergrundfarbe
        Window.clearcolor = get_color_from_hex('#0f172a')

        self._build_ui()
        # Server sofort beim Start hochfahren
        Clock.schedule_once(self._auto_start_server, 1)

    def _build_ui(self):
        # ── Titel ──
        title = Label(
            text='[b]🖥️ LernApp Server[/b]',
            markup=True,
            font_size='26sp',
            color=get_color_from_hex('#38bdf8'),
            size_hint_y=None,
            height=60
        )
        self.add_widget(title)

        # ── Status-Anzeige ──
        self.status_label = Label(
            text='[color=#94a3b8]⏳ Starte Server...[/color]',
            markup=True,
            font_size='16sp',
            size_hint_y=None,
            height=40
        )
        self.add_widget(self.status_label)

        # ── IP-Adresse Anzeige ──
        ip = get_local_ip()
        self.ip_label = Label(
            text=f'[b][color=#22d3ee]http://{ip}:{PORT}[/color][/b]',
            markup=True,
            font_size='20sp',
            size_hint_y=None,
            height=50
        )
        self.add_widget(self.ip_label)

        hint = Label(
            text='[color=#64748b]← Diese Adresse im PC-Browser öffnen[/color]',
            markup=True,
            font_size='13sp',
            size_hint_y=None,
            height=30
        )
        self.add_widget(hint)

        # ── SSH Info ──
        self.ssh_label = Label(
            text=f'[color=#64748b]SSH: ssh user@{ip} -p 8022[/color]',
            markup=True,
            font_size='13sp',
            size_hint_y=None,
            height=30
        )
        self.add_widget(self.ssh_label)

        # ── Log-Fenster ──
        log_title = Label(
            text='[color=#475569]── Server-Log ──[/color]',
            markup=True,
            font_size='13sp',
            size_hint_y=None,
            height=25
        )
        self.add_widget(log_title)

        scroll = ScrollView(size_hint=(1, 1))
        self.log_label = Label(
            text='',
            markup=True,
            font_size='12sp',
            color=get_color_from_hex('#94a3b8'),
            text_size=(Window.width - 40, None),
            valign='top',
            halign='left',
            size_hint_y=None
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        scroll.add_widget(self.log_label)
        self.add_widget(scroll)

        # ── Buttons ──
        btn_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=55,
            spacing=10
        )

        self.toggle_btn = Button(
            text='⏹ Server stoppen',
            background_color=get_color_from_hex('#dc2626'),
            color=get_color_from_hex('#ffffff'),
            font_size='15sp',
            bold=True
        )
        self.toggle_btn.bind(on_press=self._toggle_server)
        btn_layout.add_widget(self.toggle_btn)

        refresh_btn = Button(
            text='🔄 IP aktualisieren',
            background_color=get_color_from_hex('#0369a1'),
            color=get_color_from_hex('#ffffff'),
            font_size='15sp'
        )
        refresh_btn.bind(on_press=self._refresh_ip)
        btn_layout.add_widget(refresh_btn)

        self.add_widget(btn_layout)

    def _auto_start_server(self, dt):
        self._start_server()

    def _start_server(self):
        global server_thread, server_running
        if server_running:
            return

        self._log('🚀 Starte Flask-Server...')
        server_thread = threading.Thread(target=start_flask_server, daemon=True)
        server_thread.start()

        # Nach 2 Sekunden Status prüfen
        Clock.schedule_once(self._check_server_status, 2)
        self.toggle_btn.text = '⏹ Server stoppen'
        self.toggle_btn.background_color = get_color_from_hex('#dc2626')

    def _check_server_status(self, dt):
        if server_running:
            ip = get_local_ip()
            self.status_label.text = '[color=#22c55e]✅ Server läuft![/color]'
            self.ip_label.text = f'[b][color=#22d3ee]http://{ip}:{PORT}[/color][/b]'
            self._log(f'✅ Server gestartet auf Port {PORT}')
            self._log(f'🌐 Erreichbar unter: http://{ip}:{PORT}')
            self._log('📱 PC-Browser → diese Adresse öffnen')
        else:
            self.status_label.text = '[color=#ef4444]❌ Server-Fehler![/color]'
            self._log('❌ Server konnte nicht gestartet werden')

    def _toggle_server(self, instance):
        global server_running
        if server_running:
            stop_flask_server()
            self.status_label.text = '[color=#f59e0b]⏸ Server gestoppt[/color]'
            self.toggle_btn.text = '▶ Server starten'
            self.toggle_btn.background_color = get_color_from_hex('#16a34a')
            self._log('⏹ Server gestoppt')
        else:
            self._start_server()

    def _refresh_ip(self, instance):
        ip = get_local_ip()
        self.ip_label.text = f'[b][color=#22d3ee]http://{ip}:{PORT}[/color][/b]'
        self.ssh_label.text = f'[color=#64748b]SSH: ssh user@{ip} -p 8022[/color]'
        self._log(f'🔄 IP aktualisiert: {ip}')

    def _log(self, message):
        from datetime import datetime
        ts = datetime.now().strftime('%H:%M:%S')
        current = self.log_label.text
        new_line = f'[color=#64748b]{ts}[/color] {message}\n'
        self.log_label.text = current + new_line

# ─── Kivy App ─────────────────────────────────────────────────────────────────

class LernAppServerApp(App):
    def build(self):
        self.title = 'LernApp Server'
        return ServerUI()

    def on_stop(self):
        stop_flask_server()

# ─── Desktop-Modus (zum Testen auf PC) ───────────────────────────────────────

if __name__ == '__main__':
    LernAppServerApp().run()
