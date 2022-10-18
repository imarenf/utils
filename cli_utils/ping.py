from ping import ping
import socket


def ping_wrapper(url: str, timeout: int, interval: int):
    host = socket.gethostbyname(url)
    ping(host, timeout, interval)
