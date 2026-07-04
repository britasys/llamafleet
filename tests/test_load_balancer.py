import pytest

from app.services.load_balancer import LoadBalancer, NoHealthyBackendError
from app.services.transport_pool import TransportPool


class FakeTransport:
    def __init__(self, in_flight=0, last_latency=None, is_open=False):
        self.in_flight = in_flight
        self.last_latency = last_latency
        self.is_open = is_open


class FakePool(TransportPool):
    def __init__(self, transports):
        self._transports = transports

    def get(self, name):
        return self._transports[name]


def test_picks_least_loaded(base_config):
    a, b = base_config.backends[0], base_config.backends[1]
    pool = FakePool({a.name: FakeTransport(in_flight=5),
                    b.name: FakeTransport(in_flight=1)})
    lb = LoadBalancer(pool)
    assert lb.pick([a, b]).name == b.name


def test_skips_open_circuit(base_config):
    a, b = base_config.backends[0], base_config.backends[1]
    pool = FakePool({a.name: FakeTransport(
        in_flight=0, is_open=True), b.name: FakeTransport(in_flight=100)})
    lb = LoadBalancer(pool)
    assert lb.pick([a, b]).name == b.name


def test_raises_when_all_open(base_config):
    a, b = base_config.backends[0], base_config.backends[1]
    pool = FakePool({a.name: FakeTransport(is_open=True),
                    b.name: FakeTransport(is_open=True)})
    lb = LoadBalancer(pool)
    with pytest.raises(NoHealthyBackendError):
        lb.pick([a, b])


def test_raises_on_empty_candidates(base_config):
    pool = FakePool({})
    lb = LoadBalancer(pool)
    with pytest.raises(NoHealthyBackendError):
        lb.pick([])


def test_preferred_name_wins_despite_load(base_config):
    a, b = base_config.backends[0], base_config.backends[1]
    pool = FakePool({a.name: FakeTransport(in_flight=0),
                    b.name: FakeTransport(in_flight=0)})
    lb = LoadBalancer(pool)
    assert lb.pick([a, b], preferred_name=b.name).name == b.name


def test_latency_factors_into_score(base_config):
    a, b = base_config.backends[0], base_config.backends[1]
    pool = FakePool(
        {a.name: FakeTransport(in_flight=0, last_latency=5.0), b.name: FakeTransport(
            in_flight=0, last_latency=0.1)}
    )
    lb = LoadBalancer(pool)
    assert lb.pick([a, b]).name == b.name
