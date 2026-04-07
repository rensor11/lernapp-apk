import os
import socket
import threading

os.environ["KIVY_NO_ENV_CONFIG"] = "1"

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from server_neu import app as flask_app
from server_neu import init_db, load_questions_from_json

PORT = 5000
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
    try:
        with flask_app.app_context():
            init_db()
            load_questions_from_json()
        server_running = True
        flask_app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False, threaded=True)
    except Exception as exc:
        print(f"[SERVER ERROR] {exc}")
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

        ip = get_local_ip()
        self.url = Label(text=f"http://{ip}:{PORT}", font_size="20sp", size_hint_y=None, height=45)
        self.add_widget(self.url)

        self.hint = Label(text="Diese URL im Browser aufrufen", size_hint_y=None, height=30)
        self.add_widget(self.hint)

        refresh_btn = Button(text="IP aktualisieren", size_hint_y=None, height=45)
        refresh_btn.bind(on_press=self.refresh_ip)
        self.add_widget(refresh_btn)

        Clock.schedule_once(self.start_server, 1)

    def refresh_ip(self, _instance):
        ip = get_local_ip()
        self.url.text = f"http://{ip}:{PORT}"

    def start_server(self, _dt):
        global server_thread
        server_thread = threading.Thread(target=start_server_thread, daemon=True)
        server_thread.start()
        Clock.schedule_once(self.update_status, 2)

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
