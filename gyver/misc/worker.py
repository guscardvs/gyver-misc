import asyncio
from collections.abc import Awaitable, Hashable
from typing import Callable, ClassVar, Generic, TypeVar

from typing_extensions import Self

T = TypeVar("T", bound=Hashable)
R = TypeVar("R")


class WorkerQueue(Generic[T, R]):
    """A queue that processes items asynchronously with a worker function and caching."""

    _global_registry: ClassVar[dict[int, "WorkerQueue"]] = {}

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
        cache_set: Callable[[R], Awaitable[None]],
        maxsize: int = 0,
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
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker())
        return await self._ongoing[item]

    async def _worker(self) -> None:
        """Continuously processes items from the queue."""
        while True:
            value = await self._worker_queue.get()
            if value is None:
                break
            result = await self._handle_request(value)
            future = self._ongoing.pop(value, None)
            if future and not future.done():
                future.set_result(result)
            await self._cache_set(result)
            self._worker_queue.task_done()

    async def _handle_request(self, item: T) -> R:
        """Handles the processing of a single item.

        Args:
            item (T): The item to be processed.

        Returns:
            R: The result of processing the item.

        Raises:
            Exception: If processing the item fails.
        """
        try:
            result = await self._worker_func(item)
        except Exception as e:
            self._ongoing[item].set_exception(e)
            raise
        else:
            return result

    @classmethod
    async def aclose_all(cls):
        """Closes all WorkerQueue instances."""
        for instance in cls._global_registry.values():
            await instance.aclose()
        cls._global_registry.clear()

    async def aclose(self):
        """Closes the WorkerQueue instance."""
        if self._worker_task is not None:
            self._worker_task.cancel()
        WorkerQueue._global_registry.pop(self._id)
