#!/usr/bin/env python3
# Copyright 2016-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE-examples file in the root directory of this source tree.

import argparse
import logging
import os
import netaddr
import requests

from io import BytesIO
from urllib.parse import urlparse
from colored import fg, bg, attr

from fbtftp.base_handler import BaseHandler
from fbtftp.base_handler import ResponseData
from fbtftp.base_server import BaseServer


class HttpResponseData(ResponseData):
    def __init__(self, next_http_url, path, ip, mac):
        url = "%s/%s" % (next_http_url, path)
        qs = {'ip': ip, 'mac': mac}
        self._r = r = requests.get(url, params=qs)
        self._reader = BytesIO(r.content)
        self._size = len(r.content)
        logging.info("%s%s%s (%s%s%s) is looking for %s%s%s, responses from %s%s%s with %d bytes" % (
            fg('yellow'), ip, attr('reset'),
            fg('blue'), mac, attr('reset'),
            fg('green'), path, attr('reset'),
            fg('red'), next_http_url, attr('reset'),
            self._size
            ))

    def read(self, n):
        return self._reader.read(n)

    def size(self):
        return self._size

    def close(self):
        self._reader.close()


def print_session_stats(stats):
    logging.info('Stats: for %r requesting %r' % (stats.peer, stats.file_path))
    logging.info('Error: %r' % stats.error)
    logging.info('Time spent: %dms' % (stats.duration() * 1e3))
    logging.info('Packets sent: %d' % stats.packets_sent)
    logging.info('Packets ACKed: %d' % stats.packets_acked)
    logging.info('Bytes sent: %d' % stats.bytes_sent)
    logging.info('Options: %r' % stats.options)
    logging.info('Blksize: %r' % stats.blksize)
    logging.info('Retransmits: %d' % stats.retransmits)
    logging.info('Server port: %d' % stats.server_addr[1])
    logging.info('Client port: %d' % stats.peer[1])


def print_server_stats(stats):
    '''
    Print server stats - see the ServerStats class
    '''
    # NOTE: remember to reset the counters you use, to allow the next cycle to
    #       start fresh
    counters = stats.get_and_reset_all_counters()
    logging.info('Server stats - every %d seconds' % stats.interval)
    if 'process_count' in counters:
        logging.info(
            'Number of spawned TFTP workers in stats time frame : %d' %
            counters['process_count']
        )


class HttpHandler(BaseHandler):
    def __init__(self, server_addr, peer, path, options, dns_leases, next_http_url, stats_callback):
        self._path = path
        self._next_http_url = next_http_url
        self._addr = addr = str(netaddr.IPNetwork(peer[0]).ipv4().ip)
        with open(dns_leases) as f:
            data = f.read()
        lines = data.split('\n');
        lines = [ l for l in lines if l.find(addr) > 0 ]
        self._mac = lines[-1].split(' ')[1] if len(lines) > 0 else None
        logging.info("%s%s%s (%s%s%s) is looking for %s%s%s" % (
            fg('yellow'), self._addr, attr('reset'),
            fg('blue'), self._mac, attr('reset'),
            fg('green'), self._path, attr('reset')
            ))
        super().__init__(server_addr, peer, path, options, stats_callback)

    def get_response_data(self):
        # print("get_response_data(): next => %s" % (self._next_http_url))
        # print("get_response_data(): addr => %s" % (self._addr))
        # print("get_response_data(): mac => %s" % (self._mac))
        return None if self._addr is None or self._mac is None else HttpResponseData(self._next_http_url, self._path, self._addr, self._mac)


class ProxyServer(BaseServer):
    def __init__(
        self,
        address,
        port,
        retries,
        timeout,
        dns_leases,
        next_http_url,
        handler_stats_callback,
        server_stats_callback=None
    ):
        self._dns_leases = dns_leases
        self._next_http_url = next_http_url
        self._handler_stats_callback = handler_stats_callback
        super().__init__(address, port, retries, timeout, server_stats_callback)

    def get_handler(self, server_addr, peer, path, options):
        return HttpHandler(
            server_addr, peer, path, options,
            self._dns_leases,
            self._next_http_url,
            self._handler_stats_callback
        )


def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--ip',
        type=str,
        default='::',
        help='IP address to bind to'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=1969,
        help='port to bind to'
    )
    parser.add_argument(
        '--retries',
        type=int,
        default=5,
        help='number of per-packet retries'
    )
    parser.add_argument(
        '--timeout_s',
        type=int,
        default=2,
        help='timeout for packet retransmission'
    )
    parser.add_argument(
        '--dns_leases',
        type=str,
        default='/tmp/dnsmasq.leases',
        help='the dns lease file, to lookup mac address of given ip address'
    )
    parser.add_argument(
        '--next',
        type=str,
        default='',
        help='the next http server to process tftp requests'
    )
    return parser.parse_args()


def main():
    args = get_arguments()
    logging.getLogger().setLevel(logging.DEBUG)

    x = urlparse(args.next)
    if x.hostname is None:
        return print("missing hostname in next-http-url is missing")
    if x.hostname == "localhost":
        return print("hostname in next-http-url shall not be `localhost`")
    if x.hostname == "127.0.0.1":
        return print("hostname in next-http-url shall not be `127.0.0.1`")

    server = ProxyServer(
        args.ip,
        args.port,
        args.retries,
        args.timeout_s,
        args.dns_leases,
        args.next,
        print_session_stats,
        print_server_stats,
    )
    try:
        server.run()
    except KeyboardInterrupt:
        server.close()


if __name__ == '__main__':
    main()
