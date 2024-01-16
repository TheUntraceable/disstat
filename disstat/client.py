from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Any, Callable, Coroutine, List, Optional
import warnings

import aiohttp
from psutil import AccessDenied, Process, cpu_percent

if TYPE_CHECKING:
    from discord import Client as DiscordClient

    from .types import CustomGraphData


BASE_URL = "https://disstat-api.tomatenkuchen.com/v1"


class DisstatClient:
    """
    A client for interacting with the Disstat API.

    Attributes:
        client (DiscordClient): The Discord client object.
        api_key (str): The API key for accessing the Disstat API.
        auto_post (bool): Whether to automatically post data to the Disstat API.
        session (Optional[aiohttp.ClientSession]): The aiohttp client session to use for API requests.
        get_custom_graph_data (Optional[Callable[..., Coroutine[Any, None, List[CustomGraphData]]]]): A callable function to retrieve custom graph data.

    Methods:
        get_bot: Get the stats for a bot.
        post_stats: Post stats to the Disstat API.
        post_custom_graph_data: Post custom graph data to the Disstat API.
        post_command: Post a command invocation to the Disstat API.
        start_auto_post: Start the auto-post loop.
    """

    def __init__(
        self,
        client: DiscordClient,
        api_key: str,
        auto_post: bool = True,
        session: Optional[aiohttp.ClientSession] = None,
        get_custom_graph_data: Optional[
            Callable[..., Coroutine[Any, None, List[CustomGraphData]]]
        ] = None,
    ):
        """
        Initialize a new instance of the Client class.

        Args:
            client (DiscordClient): The Discord client object.
            api_key (str): The API key for accessing the Disstat API.
            auto_post (bool, optional): Whether to automatically post data to the Disstat API. Defaults to True.
            session (Optional[aiohttp.ClientSession], optional): The aiohttp client session to use for API requests. Defaults to None.
            get_custom_graph_data (Optional[Callable[..., Coroutine[Any, None, List[CustomGraphData]]]], optional): A callable function to retrieve custom graph data. Defaults to None.
        """
        self.client = client
        self.api_key = api_key
        self.auto_post = auto_post
        self.session: Optional[aiohttp.ClientSession] = session
        self.get_custom_graph_data = get_custom_graph_data

    async def get_bot(
        self,
        *,
        bot_id: Optional[int] = None,
        get_stats: bool = False,
        data_points: Optional[int] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ):
        """
        Get the stats for a bot.

        Args:
            bot_id (Optional[int], optional): The ID of the bot to get stats for. Defaults to None.
            get_stats (bool, optional): Whether to get stats for the bot. Defaults to False.
            data_points (Optional[int], optional): The number of data points to get. Defaults to None.
            start (Optional[int], optional): The start time to get data points from. Defaults to None.
            end (Optional[int], optional): The end time to get data points from. Defaults to None.

        Returns:
            The response from the Disstat API.

        Raises:
            ValueError: No bot ID was provided, and Discord Client has not logged in yet.
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": self.api_key,
                }
            )
        with contextlib.suppress(AttributeError):
            bot_id = bot_id or self.client.user.id  # type: ignore
        if not bot_id:
            raise ValueError(
                "No bot ID was provided, and Discord Client has not logged in yet."
            )
        params = {
            "returnStats": get_stats,
            "dataPoints": data_points,
            "start": start,
            "end": end,
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}
        for k, v in filtered_params.items():
            filtered_params[k] = str(v).lower()
        response = await self.session.get(
            f"{BASE_URL}/bot/{bot_id}",
            params=filtered_params,
        )
        return await response.json()

    async def post_stats(
        self,
        *,
        guilds: Optional[int] = None,
        users: Optional[int] = None,
        shards: Optional[int] = None,
        api_ping: Optional[int] = None,
        ram_usage: Optional[int] = None,
        total_ram: Optional[int] = None,
        cpu_usage: Optional[int] = None,
        bandwidth: Optional[int] = None,
        custom_data: Optional[List[CustomGraphData]] = None,
    ):
        """
        Post stats to the Disstat API.

        Args:
            guilds (Optional[int], optional): The number of guilds the bot is in. Defaults to None.
            users (Optional[int], optional): The number of users the bot can see. Defaults to None.
            shards (Optional[int], optional): The number of shards the bot has. Defaults to None.
            api_ping (Optional[int], optional): The latency of the bot to the Discord API. Defaults to None.
            ram_usage (Optional[int], optional): The RAM usage of the bot. Defaults to None.
            total_ram (Optional[int], optional): The total RAM usage of the bot. Defaults to None.
            cpu_usage (Optional[int], optional): The CPU usage of the bot. Defaults to None.
            bandwidth (Optional[int], optional): The bandwidth usage of the bot. Defaults to None.
            custom_data (Optional[List[CustomGraphData]], optional): The custom graph data to post. Defaults to None.

        Returns:
            The response from the Disstat API.

        Raises:
            ValueError: The Discord client has not logged in yet.
        """
        if not self.client.user:
            raise ValueError(
                "Discord Client has not logged in yet, post_stats after READY."
            )
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": self.api_key,
                }
            )
        data = {
            "guilds": guilds,
            "users": users,
            "shards": shards,
            "apiPing": api_ping,
            "ramUsage": ram_usage,
            "totalRam": total_ram,
            "cpuUsage": cpu_usage,
            "bandwidth": bandwidth,
            "customData": custom_data,
        }
        filtered_data = {k: v for k, v in data.items() if v is not None}
        if not filtered_data:
            warnings.warn("No data was provided to post_stats.")
            return
        response = await self.session.post(
            f"{BASE_URL}/bot/{self.client.user.id}",
            json=filtered_data,
        )
        response.raise_for_status()
        return response

    async def _auto_post(self):
        """The auto-post loop."""
        while True:
            payload = {
                "guilds": len(self.client.guilds),
                "cpu_usage": cpu_percent(),
            }
            try:
                proc = Process()

                with proc.oneshot():
                    with contextlib.suppress(AccessDenied):
                        mem = proc.memory_full_info()
                        payload["ram_usage"] = mem.uss
                        payload["total_ram"] = mem.rss
            except AccessDenied:
                ...

            if self.client.intents.members:
                payload["users"] = len(self.client.users)
            if self.client.shard_count:
                payload["shards"] = self.client.shard_count
            if self.client.latency:
                payload["api_ping"] = round(self.client.latency * 1000)
            # TODO: Add bandwidth support
            if self.get_custom_graph_data:
                payload["custom_data"] = await self.get_custom_graph_data()
            try:
                await self.post_stats(**payload)
                self.client.dispatch("disstat_post", payload)
            except Exception as e:
                self.client.dispatch("disstat_post_error", payload, e)
            await asyncio.sleep(90)

    async def post_custom_graph_data(self, custom_data: CustomGraphData):
        """
        Post custom graph data to the Disstat API.

        Args:
            custom_data (CustomGraphData): The custom graph data to post.

        Returns:
            The response from the Disstat API.

        Raises:
            ValueError: The Discord client has not logged in yet.
        """
        if not self.client.user:
            raise ValueError(
                "Discord Client has not logged in yet, post_stats after READY."
            )
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": self.api_key,
                }
            )
        response = await self.session.post(
            f"{BASE_URL}/bot/{self.client.user.id}/custom",
            json=custom_data,
        )
        return await response.json()

    async def post_command(
        self, command_name: str, *, invoker_id: int, guild_id: Optional[int] = None
    ):
        """
        Post a command invocation to the Disstat API.

        Args:
            command_name (str): The name of the command.
            invoker_id (int): The ID of the user who invoked the command.
            guild_id (Optional[int], optional): The ID of the guild the command was invoked in. Defaults to None.

        Returns:
            The response from the Disstat API.

        Raises:
            ValueError: The Discord client has not logged in yet.

        """
        if not self.client.user:
            raise ValueError(
                "Discord Client has not logged in yet, post_stats after READY."
            )
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": self.api_key,
                }
            )
        data: CustomGraphData = {
            "type": "Commands Used",
            "value1": command_name,
            "value2": invoker_id,
            "value3": guild_id,
        }
        try:
            response = await self.session.post(
                f"{BASE_URL}/bot/{self.client.user.id}/custom",
                json=data,
            )
            response.raise_for_status()
        except Exception as e:
            self.client.dispatch("disstat_post_command_error", data, e)
            return
        self.client.dispatch("disstat_post_command", data)

    async def start_auto_post(self):
        """Start the auto-post loop."""
        self.client.loop.create_task(self._auto_post())
