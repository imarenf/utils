import argparse

from cli_utils.rps_test import calculate_rps
from cli_utils.ping import ping_wrapper
from cli_utils.netscan import PortScaner


def main():
    parser = argparse.ArgumentParser(description='List of command-line network utilities')
    subparsers = parser.add_subparsers(title='commands',
                                       dest='command')

    rps_test_subparser = subparsers.add_parser('rps-test',
                                               help='RPS metrics testing utility')
    rps_test_subparser.add_argument('url',
                                    help='Url to test')
    rps_test_subparser.add_argument('-n', '--count',
                                    help='Total number of requests to perform for the session, default is 1',
                                    dest='count',
                                    default=1,
                                    type=int)
    rps_test_subparser.add_argument('-c', '--concurrency-level',
                                    help='Number of requests to perform at a time, default is 1 '
                                         '(in this case requests will be sent non-concurrently).',
                                    dest='level',
                                    default=1,
                                    type=int)
    rps_test_subparser.add_argument('-t', '--timeout',
                                    help='Timeout in seconds',
                                    dest='timeout',
                                    type=int)

    ping_subparser = subparsers.add_parser('ping',
                                           help='Ping to a host')
    ping_subparser.add_argument('url',
                                help='Url to ping')
    ping_subparser.add_argument('--timeout', '-t',
                                help='Timeout in seconds',
                                dest='timeout',
                                type=int)
    ping_subparser.add_argument('--interval', '-i',
                                help='Interval between pings in microseconds',
                                dest='interval',
                                type=int)

    netscan_subparser = subparsers.add_parser('netscan',
                                              help='Scan open ports of the given domain')
    netscan_subparser.add_argument('target',
                                   help='Target host (ip or hostname format)')
    netscan_subparser.add_argument('--timeout', '-t',
                                   help='Timeout in seconds',
                                   dest='timeout',
                                   type=int)

    args = parser.parse_args()
    if args.command == 'rps-test':
        calculate_rps(args.url, args.count, args.level, args.timeout)
    elif args.command == 'ping':
        ping_wrapper(args.url, args.timeout, args.interval)
    elif args.command == 'netscan':
        PortScaner(args.target, args.timeout).net_scan()
    else:
        print('Nothing to do')


if __name__ == '__main__':
    main()
