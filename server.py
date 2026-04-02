import socket
import threading
import time
from collections import deque


class SpaceInvadersServer:
    def __init__(self, host="0.0.0.0", port=12345):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_socket = None
        self.running = False
        self.pending_commands = deque()
        self._lock = threading.Lock()
        self._accept_thread = None

    def get_local_ip(self):
        try:
            probe_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probe_socket.connect(("8.8.8.8", 80))
            ip = probe_socket.getsockname()[0]
            probe_socket.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _create_server_socket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(1)
        return server_socket

    def _print_startup_banner(self, real_ip):
        print("=" * 50)
        print("SERVER ACTIV!")
        print(f"Enter this address on your phone: {real_ip}")
        print("Waiting for the phone to connect...")

    def _queue_command(self, command):
        with self._lock:
            self.pending_commands.append(command)

    def start(self):
        if self.running:
            return

        self.server_socket = self._create_server_socket()
        self.running = True

        real_ip = self.get_local_ip()
        self._print_startup_banner(real_ip)

        self._accept_thread = threading.Thread(target=self._accept_client, daemon=True)
        self._accept_thread.start()

    def _accept_client(self):
        try:
            self.client_socket, addr = self.server_socket.accept()
        except OSError:
            return

        print(f"Phone connected from address: {addr}")
        threading.Thread(target=self._listen_for_commands, daemon=True).start()

    def _listen_for_commands(self):
        buffer = ""
        try:
            while self.running and self.client_socket:
                data = self.client_socket.recv(1024)
                if not data:
                    break

                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    raw_command, buffer = buffer.split("\n", 1)
                    command = raw_command.strip().upper()
                    if not command:
                        continue

                    self._queue_command(command)
        except Exception as error:
            if self.running:
                print(f"Reception error: {error}")
        finally:
            self._close_client()

    def _send_signal(self, message):
        if not self.client_socket:
            return

        try:
            self.client_socket.sendall(f"{message}\n".encode("utf-8"))
        except Exception:
            self._close_client()

    def send_start_signal(self):
        self._send_signal("START")

    def send_life_lost_signal(self):
        self._send_signal("LIFE_LOST")

    def send_state_signal(self, state):
        self._send_signal(f"STATE:{state}")

    def send_message(self, message):
        self._send_signal(message)

    def pop_commands(self):
        with self._lock:
            commands = list(self.pending_commands)
            self.pending_commands.clear()
        return commands

    def has_client(self):
        return self.client_socket is not None

    def _close_client(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except OSError:
                pass
            finally:
                self.client_socket = None

        with self._lock:
            self.pending_commands.clear()

    def stop(self):
        self.running = False
        self._close_client()
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
            finally:
                self.server_socket = None


if __name__ == "__main__":
    server = SpaceInvadersServer()
    server.start()
    try:
        while True:
            for command in server.pop_commands():
                print(f"Processing: {command}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        server.stop()
