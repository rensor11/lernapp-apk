import os
import sys
import socket
import threading
import traceback

# --- Android data directory setup (must happen before server_neu import) ---
def _get_android_data_dir():
    """Return a writable directory on Android, or None on desktop."""
    try:
        from android.storage import app_storage_path
        return app_storage_path()
    except ImportError:
        pass
    arg = os.environ.get('ANDROID_ARGUMENT')
    if arg:
        return os.path.dirname(os.path.abspath(arg))
    return None

_data_dir = _get_android_data_dir()
if _data_dir:
    os.makedirs(_data_dir, exist_ok=True)
    os.environ['LERNAPP_DATA_DIR'] = _data_dir

os.environ["KIVY_NO_ENV_CONFIG"] = "1"

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

_import_error = None
try:
    from server_neu import app as flask_app
    from server_neu import init_db, load_questions_from_json
except Exception as exc:
    _import_error = f"Import-Fehler: {exc}\n{traceback.format_exc()}"
    flask_app = None

PORT = 5000
PUBLIC_URL = "https://renlern.org"
server_thread = None
server_running = False


def get_local_ip():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


def start_server_thread():
    global server_running
    if flask_app is None:
        return
    try:
        with flask_app.app_context():
            init_db()
            load_questions_from_json()
        server_running = True
        flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False, threaded=True)
    except Exception as exc:
        print(f"[SERVER ERROR] {exc}\n{traceback.format_exc()}")
        server_running = False


class ServerUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [20, 30, 20, 20]
        self.spacing = 12
        Window.clearcolor = (0.06, 0.10, 0.16, 1)

        self.title = Label(text="LernApp Android Server", font_size="22sp", size_hint_y=None, height=50)
        self.add_widget(self.title)

        self.status = Label(text="Starte Server...", size_hint_y=None, height=35)
        self.add_widget(self.status)

        self.url = Label(text=PUBLIC_URL, font_size="20sp", size_hint_y=None, height=45)
        self.add_widget(self.url)

        self.hint = Label(text="Diese feste URL im Browser aufrufen", size_hint_y=None, height=30)
        self.add_widget(self.hint)

        # Scrollable log area to show errors on screen
        scroll = ScrollView(size_hint=(1, 1))
        self.log_label = Label(
            text="",
            font_size="12sp",
            size_hint_y=None,
            text_size=(Window.width - 40, None),
            valign="top",
            halign="left",
        )
        self.log_label.bind(texture_size=self.log_label.setter("size"))
        scroll.add_widget(self.log_label)
        self.add_widget(scroll)

        refresh_btn = Button(text="IP aktualisieren", size_hint_y=None, height=45)
        refresh_btn.bind(on_press=self.refresh_ip)
        self.add_widget(refresh_btn)

        if _import_error:
            self.status.text = "FEHLER beim Import"
            self.log_label.text = _import_error
        else:
            Clock.schedule_once(self.start_server, 1)

    def refresh_ip(self, _instance):
        ip = get_local_ip()
        self.url.text = f"{PUBLIC_URL}  |  Lokal: http://{ip}:{PORT}"

    def start_server(self, _dt):
        global server_thread
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()
        Clock.schedule_once(self.update_status, 3)

    def _run_server(self):
        global server_running
        try:
            with flask_app.app_context():
                init_db()
                load_questions_from_json()
            server_running = True
            Clock.schedule_once(lambda dt: self._set_log(f"Data: {os.environ.get('LERNAPP_DATA_DIR', 'default')}"), 0)
            flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False, threaded=True)
        except Exception as exc:
            server_running = False
            err = f"{exc}\n{traceback.format_exc()}"
            Clock.schedule_once(lambda dt: self._set_log(err), 0)

    def _set_log(self, text):
        self.log_label.text = str(text)

    def update_status(self, _dt):
        if server_running:
            self.status.text = "Server laeuft"
        else:
            self.status.text = "Server konnte nicht starten"


class LernAppServerApp(App):
    def build(self):
        self.title = "LernApp Server"
        return ServerUI()


if __name__ == "__main__":
    LernAppServerApp().run()
