#!/usr/bin/python3

import sys
import os
import socket

from inputthread import InputThread
from queue import Queue
from node import Node
from node_fnc import _Const, validate_ip_port
from inputcallback import input_callback

def main():
    _argc = len(sys.argv)
    # ip:port provided
    if _argc == 2:
        host = sys.argv[1].split(':')
        ip, port = (str(host[0]), int(host[1]))
        if validate_ip_port(ip, port) != 0:
            print(f"invalid ip:port.")
            exit(1)
    # no args
    else:
        default_port = 45665
        if _argc == 1:
            # assign default host ip & port
            ip, port = (str(socket.gethostbyname(socket.gethostname())), default_port)
            print(f"ip:port not provided >>> using default host ip with default port >>> {ip}:{port}")
        else:
            print("invalid arguments")
            exit(1)

    if validate_ip_port(ip, port) != 0:
        exit(1)
    
    n = Node(ip, port)
    q = Queue(512)
    c = _Const()

    # init non-blocking input thr
    inpthr = InputThread(input_callback=input_callback, _node=n, _const=c, _queue=q)
    # thread watcher
    while 1:
        if not inpthr.is_alive():
            print("re-starting input-thread")
            inpthr = None
            inpthr = InputThread(input_callback=input_callback, _node=n, _const=c, _queue=q)
            break
        else:
            print("input-thread is alive.")
            break

    # init node as tcp server
    if n.init_server(c) != 0:
        print("[!] failed to initialize node as server")
        exit(1)

    print(f">>>\n>>> P2P Node-0 {ip}:{port}\n>>>")

    while True:
        
        ret = n.handle_connections(q, c)

        if ret != 0:
            print(">>> exiting handle connections loop")
            break

    if ret == 0:
        print(f"exited normally with [{ret}]")
        n.close_master_socket()
    elif ret == 1:
        print(f"exited by cmd with [{ret}]")
    else:
        print(f"exited with error [{ret}]")
    
    exit(ret)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"exiting by SIGINT..")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)