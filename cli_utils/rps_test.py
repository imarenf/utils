import asyncio
import aiohttp
import functools
import requests
import socket
import signal
from sys import exit
from urllib.parse import urlparse
from collections import Counter
from typing import Tuple
from datetime import datetime
from statistics import fmean, median
from dataclasses import dataclass


rps_tester_stopped = False


@dataclass
class ChunkData:
    received: int
    failed: int
    full_time: float
    request_time: float
    rps: float


class RPSTester:
    def __init__(self, url: str):
        self.url = url
        self.data = []
        self.headers = {}
        self.total_sent = 0

    @staticmethod
    def handle_timeout(signum: int, frame):
        global rps_tester_stopped
        rps_tester_stopped = False

    @staticmethod
    def _run_and_get_stats(func):
        @functools.wraps(func)
        async def inner(*args, **kwargs):
            self = args[0]
            start_timestamp = datetime.now()
            sent, received = await func(*args, **kwargs)
            task_time = (datetime.now() - start_timestamp).total_seconds()
            rps = round(sent / task_time, 1)
            request_time = round(task_time / sent, 2)
            self.total_sent += sent
            self.data.append(ChunkData(received, sent-received, task_time, request_time, rps))
        return inner

    @staticmethod
    def _resolve_hostname(hostname: str) -> Tuple[str, str] | Tuple[str]:
        if hostname.find(':') != -1:
            host, port = hostname.split(':')
            return host, port
        else:
            return hostname,

    def _collect_and_print_server_info(self) -> None:
        url_parsed = urlparse(self.url)
        response = requests.get(self.url)
        host_data = RPSTester._resolve_hostname(url_parsed.netloc)
        match host_data:
            case (host_,):
                host = host_
                port = 443 if url_parsed.scheme == 'https' else 80
            case host_, port_:
                host = host_
                port = port_
            case _:
                host = url_parsed.netloc
                port = None
        try:
            ip = socket.gethostbyname(host)
        except ...:
            ip = None
        print(
            f'Server: {response.headers.get("Server")}\n'
            f'Host: {host}\n'
            f'IP: {ip}\n'
            f'Port: {port}\n'
            f'Protocol: {url_parsed.scheme}\n\n'
            f'Document Path: {url_parsed.path}\n'
            f'Type: {response.headers.get("Content-Type")}\n'
            f'Document Length: {response.headers.get("Content-Length")}'
        )

    def _print_stats(self):
        rps_data = [chunk.rps for chunk in self.data]
        mean_rps = fmean(rps_data)
        median_rps = median(rps_data)
        max_rps = max(rps_data)
        min_rps = min(rps_data)
        total_complete = sum(chunk.received for chunk in self.data)
        total_failed = sum(chunk.failed for chunk in self.data)
        mean_request_time = fmean(chunk.request_time for chunk in self.data)
        full_time = round(sum(chunk.full_time for chunk in self.data), 4)
        print(
            f'Total Requests Sent: {self.total_sent}\n'
            f'Complete Requests: {total_complete}\n'
            f'Failed Requests: {total_failed}\n'
            f'Total Time: {full_time}\n'
            f'Mean Time per Request: {mean_request_time}\n'
            f'RPS: {mean_rps} (mean),  {median_rps} (median),  {min_rps} (min),  {max_rps} (max)'
        )

    @_run_and_get_stats
    async def _send_requests(self, times: int, session) -> Tuple[int, int]:
        tasks = (asyncio.create_task(session.get(self.url)) for _ in range(times))
        responses = await asyncio.gather(*tasks)
        stats = Counter((r.ok for r in responses))
        return stats.total(), stats.get(True)

    @staticmethod
    def validate_args(requests_total: int, concurrency_level: int, timeout: int) -> None:
        if requests_total <= 0:
            print('The number of requests must be positive')
            exit(1)
        if concurrency_level <= 0:
            print('Concurrency level must be positive')
            exit(1)
        if timeout and timeout <= 0:
            print('Timeout must be a positive number of seconds')
            exit(1)

    async def start_testing(self, total: int, level: int) -> None:
        global rps_tester_stopped
        self._collect_and_print_server_info()
        async with aiohttp.ClientSession() as session:
            while self.total_sent < total and not rps_tester_stopped:
                await self._send_requests(times=level, session=session)
        self._print_stats()


def calculate_rps(url: str, requests_total: int, concurrency_level: int, timeout: int = None) -> None:
    RPSTester.validate_args(requests_total, concurrency_level, timeout)
    if timeout:
        signal.signal(__signalnum=signal.SIGALRM, __handler=RPSTester.handle_timeout)
        signal.alarm(__seconds=timeout)
    api = RPSTester(url)
    asyncio.run(api.start_testing(total=requests_total, level=concurrency_level))
