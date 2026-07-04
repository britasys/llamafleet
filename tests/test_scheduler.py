import asyncio

import pytest

from app.services.scheduler import Priority, Scheduler, SchedulerTimeoutError


async def test_allows_up_to_max_concurrent():
    scheduler = Scheduler(max_concurrent=2)
    entered = []

    async def worker(i):
        async with scheduler.slot():
            entered.append(i)
            await asyncio.sleep(0.05)

    await asyncio.gather(worker(1), worker(2))
    assert set(entered) == {1, 2}
    assert scheduler.in_flight == 0


async def test_queues_beyond_capacity():
    scheduler = Scheduler(max_concurrent=1)
    order = []

    async def worker(i, delay):
        async with scheduler.slot():
            order.append(i)
            await asyncio.sleep(delay)

    await asyncio.gather(worker(1, 0.05), worker(2, 0.0))
    assert order == [1, 2]


async def test_priority_jumps_queue():
    scheduler = Scheduler(max_concurrent=1)
    order = []

    async def hold():
        async with scheduler.slot():
            await asyncio.sleep(0.05)

    async def worker(i, priority):
        await asyncio.sleep(0.01)
        async with scheduler.slot(priority):
            order.append(i)

    await asyncio.gather(
        hold(),
        worker(1, Priority.LOW),
        worker(2, Priority.HIGH),
    )
    assert order == [2, 1]


async def test_queue_full_raises():
    scheduler = Scheduler(max_concurrent=1, max_queue=1, queue_timeout=1)

    async def hold():
        async with scheduler.slot():
            await asyncio.sleep(0.2)

    async def waiter():
        async with scheduler.slot():
            pass

    async def overflow():
        async with scheduler.slot():
            pass

    task = asyncio.create_task(hold())
    await asyncio.sleep(0.01)
    w = asyncio.create_task(waiter())
    await asyncio.sleep(0.01)
    with pytest.raises(SchedulerTimeoutError):
        await overflow()
    await asyncio.gather(task, w)


async def test_queue_timeout_raises():
    scheduler = Scheduler(max_concurrent=1, max_queue=5, queue_timeout=0.05)

    async def hold():
        async with scheduler.slot():
            await asyncio.sleep(0.5)

    task = asyncio.create_task(hold())
    await asyncio.sleep(0.01)
    with pytest.raises(SchedulerTimeoutError):
        async with scheduler.slot():
            pass
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
