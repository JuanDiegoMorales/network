import json
import threading
import time

from network.common.networkk import Network
from network.controller import Controller
from network.router import Router

threads = []
routers: list[Router] = []


def create_controller(host: str, port: int, network: Network) -> Controller:
    controller = Controller(host, port, network)
    controller.start_server()
    return controller


def create_router(name: str, host: str, port: int, controller: Controller):
    router = Router(controller.host, controller.port, host, port, name)
    router.connect_to_controller()
    routers.append(router)


def main():
    network = Network()

    # Creation of Nodes
    nodes = {
        "WA": ("localhost", 8094),
        "MI": ("localhost", 8081),
        "NY": ("localhost", 8082),
        "CA1": ("localhost", 8083),
        "UT": ("localhost", 8084),
        "CO": ("localhost", 8085),
        "NE": ("localhost", 8086),
        "IL": ("localhost", 8087),
        "PA": ("localhost", 8088),
        "NJ": ("localhost", 8089),
        "CA2": ("localhost", 8090),
        "DC": ("localhost", 8091),
        "TX": ("localhost", 8092),
        "GA": ("localhost", 8093),
    }

    # Creation of Edges
    edges = [
        ("WA", "CA1", 2100),
        ("WA", "CA2", 3000),
        ("WA", "IL", 4800),
        ("CA1", "UT", 1500),
        ("CA1", "CA2", 1200),
        ("CA2", "TX", 3600),
        ("UT", "MI", 3900),
        ("UT", "CO", 1200),
        ("CO", "NE", 1200),
        ("CO", "TX", 2400),
        ("NE", "IL", 1500),
        ("NE", "GA", 2700),
        ("TX", "GA", 1200),
        ("TX", "DC", 3600),
        ("IL", "PA", 1500),
        ("GA", "PA", 1500),
        ("PA", "NY", 600),
        ("PA", "NJ", 600),
        ("MI", "NY", 1200),
        ("MI", "NJ", 1500),
        ("DC", "NY", 600),
        ("DC", "NJ", 300),
    ]

    # Create Controller
    controller = create_controller(
        "localhost",
        8079,
        network
    )

    time.sleep(3)
    print("\n\nTest: Creation of Routers and Edges")

    for node, (host, port) in nodes.items():
        thread = threading.Thread(target=create_router, args=(node, host, port, controller))
        threads.append(thread)
        thread.start()
        time.sleep(1)

    for thread in threads:
        thread.join()

    # Add edges and update routes after all routers are connected
    for (u, v, w) in edges:
        network.add_edge(u, v, w)

    controller.update_routes()

    print("Routes saved successfully.")

    time.sleep(2)
    print("\n\nTest: Creation of routes.json from Edges and Nodes")

    # Store the routes
    routes = network.get_routes_all()
    with open("routes/routes.json", "w") as f:
        json.dump([route.__dict__() for route in routes], f, indent=4)

    print("Updated Routes")

    time.sleep(2)
    print("\n\nTest: Creation and SetUp of Routers Servers")

    ca1 = None
    ny = None
    ut = None

    for router in routers:
        if router.name == "CA1":
            ca1 = router
        if router.name == "UT":
            ut = router
        if router.name == "NY":
            ny = router
        router.start_server()
        time.sleep(2)

    # time.sleep(2)
    # print("\n\nTest: Sending Messages from CA1 to NY")
    #
    # # Test sending a text message
    # ca1.send_message(ny.name, 'Hello, this is a text message!')
    #
    # time.sleep(10)
    # print("\n\nTest: Remove Node UT")
    #
    # ut.stop()
    #
    # time.sleep(10)
    # print("\n\nTest: Sending AUDIO FILES from CA1 to NY")
    #
    # # Test sending an audio file
    # with open('source/test_audio.wav', 'rb') as f:
    #     filedata = f.read()
    # ca1.send_message(ny.name, 'audio_new.wav', is_file=True, filedata=filedata)
    #
    # time.sleep(10)
    # print("\n\nClose Connections")
    #
    # controller.stop()
    #
    # for router in routers:
    #     router.stop()


if __name__ == "__main__":
    main()