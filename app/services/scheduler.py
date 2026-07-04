from __future__ import annotations

import asyncio
import heapq
import itertools
from contextlib import asynccontextmanager
from enum import IntEnum


class Priority(IntEnum):
    HIGH = 0
    NORMAL = 1
    LOW = 2


class SchedulerTimeoutError(Exception):
    pass


class _Waiter:
    __slots__ = ("priority", "seq", "future")

    def __init__(self, priority: int, seq: int, future: asyncio.Future):
        self.priority = priority
        self.seq = seq
        self.future = future

    def __lt__(self, other: "_Waiter") -> bool:
        return (self.priority, self.seq) < (other.priority, other.seq)


class Scheduler:
    def __init__(self, max_concurrent: int, max_queue: int = 1000, queue_timeout: float = 30.0):
        self._max_concurrent = max_concurrent
        self._max_queue = max_queue
        self._queue_timeout = queue_timeout
        self._in_flight = 0
        self._queue: list[_Waiter] = []
        self._seq = itertools.count()
        self._lock = asyncio.Lock()

    @property
    def in_flight(self) -> int:
        return self._in_flight

    @property
    def queued(self) -> int:
        return len(self._queue)

    async def _acquire(self, priority: Priority) -> None:
        async with self._lock:
            if self._in_flight < self._max_concurrent and not self._queue:
                self._in_flight += 1
                return
            if len(self._queue) >= self._max_queue:
                raise SchedulerTimeoutError("queue full")
            future = asyncio.get_event_loop().create_future()
            waiter = _Waiter(int(priority), next(self._seq), future)
            heapq.heappush(self._queue, waiter)

        try:
            await asyncio.wait_for(waiter.future, timeout=self._queue_timeout)
        except asyncio.TimeoutError:
            async with self._lock:
                try:
                    self._queue.remove(waiter)
                    heapq.heapify(self._queue)
                except ValueError:
                    pass
            raise SchedulerTimeoutError("queue timeout")

    async def _release(self) -> None:
        async with self._lock:
            if self._queue:
                waiter = heapq.heappop(self._queue)
                if not waiter.future.done():
                    waiter.future.set_result(None)
                return
            self._in_flight -= 1

    @asynccontextmanager
    async def slot(self, priority: Priority = Priority.NORMAL):
        await self._acquire(priority)
        try:
            yield
        finally:
            await self._release()
