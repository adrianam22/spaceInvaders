from game import SpaceInvaders
from server import SpaceInvadersServer


if __name__ == "__main__":
    server = SpaceInvadersServer()
    server.start()

    try:
        SpaceInvaders(server=server).run()
    finally:
        server.stop()
