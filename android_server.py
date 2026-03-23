import json
import socket
import threading


class AndroidServer:
    """Asculta comenzi de pe telefonul Android via Wi-Fi."""

    def __init__(self, port=5555):
        self.port = port
        self.commands = {"left": False, "right": False, "fire": False}
        self.lock = threading.Lock()
        self.running = False
        self.server_ip = self._get_local_ip()

    def _get_local_ip(self):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.connect(("8.8.8.8", 80))
            ip = client.getsockname()[0]
            client.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        self.running = True
        listener = threading.Thread(target=self._listen, daemon=True)
        listener.start()
        print(f"[SERVER] Pornit pe {self.server_ip}:{self.port}")
        print("[SERVER] Conecteaza telefonul la aceasta adresa IP!")

    def _listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("0.0.0.0", self.port))
            server.listen(5)
            server.settimeout(1)
            while self.running:
                try:
                    conn, addr = server.accept()
                    print(f"[SERVER] Telefon conectat: {addr}")
                    thread = threading.Thread(target=self._handle, args=(conn,), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue

    def _handle(self, conn):
        with conn:
            conn.settimeout(5)
            buffer = ""
            while self.running:
                try:
                    data = conn.recv(256).decode("utf-8")
                    if not data:
                        break
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        try:
                            command = json.loads(line.strip())
                            with self.lock:
                                self.commands.update(command)
                        except Exception:
                            pass
                except Exception:
                    break

    def get_commands(self):
        with self.lock:
            return dict(self.commands)

    def stop(self):
        self.running = False
