import asyncio
from collections.abc import Awaitable, Coroutine, Hashable
from typing import Callable, ClassVar, Generic, TypeVar

import exceptiongroup
from typing_extensions import Self

from gyver.misc.casting import filter_isinstance

T = TypeVar('T', bound=Hashable)
R = TypeVar('R')


class WorkerQueue(Generic[T, R]):
    """A queue that processes items asynchronously with a worker function and caching."""

    _global_registry: ClassVar[dict[int, 'WorkerQueue']] = {}

    def __new__(cls, *args, **kwargs) -> Self:
        """Creates and registers a new instance of WorkerQueue.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Self: A new instance of WorkerQueue.
        """
        del args, kwargs
        instance = object.__new__(cls)
        cls._global_registry[id(instance)] = instance
        return instance

    def __init__(
        self,
        worker: Callable[[T], Awaitable[R]],
        cache_get: Callable[[T], Awaitable[R | None]],
        cache_set: Callable[[T, R], Awaitable[None]],
        maxsize: int = 3,
        finish_timeout: float = 3.0,
    ):
        """Initializes the WorkerQueue.

        Args:
            worker (Callable[[T], Awaitable[R]]): The worker function to process items.
            cache_get (Callable[[T], Awaitable[R | None]]): Function to get item from cache.
            cache_set (Callable[[R], Awaitable[None]]): Function to set item in cache.
            maxsize (int, optional): Maximum size of the queue. Defaults to 0.
        """
        self._worker_func = worker
        self._cache_get = cache_get
        self._cache_set = cache_set
        self._worker_task: asyncio.Task | None = None
        self._worker_queue = asyncio.Queue(maxsize)
        self._ongoing: dict[T, asyncio.Future] = {}
        self._id = id(self)
        self._maxtasks = maxsize
        self._event = asyncio.Event()
        self._finish_timeout = finish_timeout

    async def require(self, item: T) -> R:
        """Requests processing of an item, using cache if available.

        Args:
            item (T): The item to be processed.

        Returns:
            R: The result of processing the item.
        """
        result = await self._cache_get(item)
        if result is not None:
            return result
        if item in self._ongoing:
            return await self._ongoing[item]
        self._ongoing[item] = asyncio.Future()
        await self._worker_queue.put(item)
        if not self.running:
            await self.aclose()
            self._worker_task = self._open()
        return await self._ongoing[item]

    def _open(self):
        if self._id not in (registry := type(self)._global_registry):
            registry[self._id] = self
        if self._event.is_set():
            self._event.clear()
        return asyncio.create_task(self._worker())

    async def _worker(self) -> None:
        """Continuously processes items from the queue."""
        excs = None
        while not self._event.is_set():
            excs = list(
                filter_isinstance(
                    Exception,
                    await asyncio.gather(
                        *(self._handle_request() for _ in range(self._maxtasks)),
                        return_exceptions=True,
                    ),
                )
            )
        tasks: list[asyncio.Task] = []
        finisher_function, timeouts = self._finisher()
        for key, ongoing in self._ongoing.items():
            if ongoing.done():
                continue
            task = asyncio.create_task(finisher_function(key, ongoing))
            tasks.append(task)
        await asyncio.gather(*tasks)
        if timeouts:
            excs = (excs or []) + timeouts
        if excs:
            raise exceptiongroup.ExceptionGroup(
                'WorkerQueue stopped due to the following exceptions', excs
            )

    async def _handle_request(self) -> None:
        """Handles the processing of a single item.

        Args:
            item (T): The item to be processed.

        Returns:
            R: The result of processing the item.

        Raises:
            Exception: If processing the item fails.
        """
        item = await self._worker_queue.get()
        if item is None:
            if not self._event.is_set():
                self._event.set()
            self._worker_queue.task_done()
            return
        try:
            result = await self._worker_func(item)
        except Exception as e:
            self._ongoing[item].set_exception(e)
            self._event.set()
        else:
            future = self._ongoing.pop(item, None)
            if future and not future.done():
                future.set_result(result)
            await self._cache_set(item, result)
            self._worker_queue.task_done()

    @classmethod
    async def aclose_all(cls):
        """Closes all WorkerQueue instances."""
        for instance in cls._global_registry.values():
            await instance.aclose()
        cls._global_registry.clear()

    async def aclose(self):
        """Closes the WorkerQueue instance."""
        if self._worker_task is None:
            return
        if not self._event.is_set():
            self._event.set()
        while not self._worker_queue.qsize() == self._maxtasks:
            self._worker_queue.put_nowait(None)
        await self._worker_task
        if (exception := self._worker_task.exception()) is not None:
            raise exception
        WorkerQueue._global_registry.pop(self._id, None)

    def _finisher(
        self,
    ) -> tuple[
        Callable[[T, asyncio.Future], Coroutine[None, None, None]],
        list[asyncio.TimeoutError],
    ]:
        semaphore = asyncio.Semaphore(self._maxtasks)
        timeouts: list[asyncio.TimeoutError] = []

        async def _finish(item: T, future: asyncio.Future) -> None:
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        self._worker_func(item),
                        self._finish_timeout,
                    )
                except asyncio.TimeoutError as err:
                    future.set_exception(err)
                    timeouts.append(err)
                else:
                    await self._cache_set(item, result)
                    future.set_result(result)

        return _finish, timeouts

    @property
    def running(self) -> bool:
        if self._worker_task is None:
            return False
        return not (self._worker_task.done() or self._worker_task.cancelled())

    async def __aenter__(self) -> Self:
        if not self.running:
            self._worker_task = self._open()
        return self

    async def __aexit__(self, *_) -> None:
        await self.aclose()
