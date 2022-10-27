import socket
from scapy.layers.inet import TCP, IP, ICMP, sr1

from .base.constants import REGULAR_PORTS


class PortScaner:
    def __init__(self, hostname, timeout=None):
        self.host = socket.gethostbyname(hostname)
        self.timeout = timeout if timeout else 10
        self.open_ports = []

    def try_access_host(self):
        icmp_packet = IP(dst=self.host) / ICMP()
        resp_packet = sr1(icmp_packet, timeout=self.timeout)
        return resp_packet is not None

    def try_access(self, port):
        syn_packet = IP(dst=self.host) / TCP(dport=port, flags='S')
        resp_packet = sr1(syn_packet, timeout=self.timeout)
        if resp_packet is not None and resp_packet.getlayer('TCP').flags & 0x12 != 0:
            self.open_ports.append(port)

    def format_output(self):
        if not self.open_ports:
            print(f'No open ports found on host {self.host}')
            return
        print('PORT   STATE    SERVICE')
        for port in self.open_ports:
            print(f'{port}   open    {REGULAR_PORTS[port]}')

    def net_scan(self):
        for port, _ in REGULAR_PORTS.items():
            if self.try_access(port):
                self.open_ports.append(port)
        self.format_output()
