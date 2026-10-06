"""The lock a server takes its changes under lets them in in the order they came to it (the plan's decision 8): with
one change being taken and several waiting, in a known order, each goes in its turn, none barging ahead."""
import threading

from kb import server

PATIENCE = 30.0  # seconds a wait is given before the test fails
WAITING = 5


def test_changes_waiting_on_a_server_are_taken_in_the_order_they_arrived():
    taking, taken = server.InOrder(), []
    taking.__enter__()
    threads = []
    for each in range(WAITING):
        thread = threading.Thread(target=lambda each=each: _taken(taking, taken, each), daemon=True)
        thread.start()
        threads.append(thread)
        assert taking.arrived(each + 2, PATIENCE), f"change {each} never came to the lock"
    taking.__exit__(None, None, None)
    for thread in threads:
        thread.join(PATIENCE)
        assert not thread.is_alive()
    assert taken == list(range(WAITING))


def _taken(taking, taken, each):
    with taking:
        taken.append(each)
