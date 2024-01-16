from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Any, Callable, Coroutine, List, Optional

import aiohttp
from psutil import AccessDenied, Process, cpu_percent

if TYPE_CHECKING:
    from discord import Client as DiscordClient

    from .types import CustomGraphData


BASE_URL = "https://disstat-api.tomatenkuchen.com/v1"


class DisstatClient:
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
        self.client = client
        self.api_key = api_key
        self.auto_post = auto_post
        self.session: Optional[aiohttp.ClientSession] = session
        self.get_custom_graph_data = get_custom_graph_data

    async def get_bot(
        self,
        bot_id: Optional[int] = None,
        get_stats: bool = False,
        data_points: Optional[int] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
    ):
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
        guilds: int,
        users: Optional[int] = None,
        shards: Optional[int] = None,
        api_ping: Optional[int] = None,
        ram_usage: Optional[int] = None,
        total_ram: Optional[int] = None,
        cpu_usage: Optional[int] = None,
        bandwidth: Optional[int] = None,
        custom_data: Optional[List[CustomGraphData]] = None,
    ):
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
        response = await self.session.post(
            f"{BASE_URL}/bot/{self.client.user.id}",
            json=filtered_data,
        )
        response.raise_for_status()
        return response

    async def _auto_post(self):
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
        data = {"customData": custom_data}
        response = await self.session.post(
            f"{BASE_URL}/bot/{self.client.user.id}/custom",
            json=data,
        )
        data = await response.json()
        return data

    async def post_command(
        self, command_name: str, invoker_id: int, guild_id: Optional[int] = None
    ):
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
        self.client.loop.create_task(self._auto_post())
