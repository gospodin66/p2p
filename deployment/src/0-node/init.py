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

    queue_size = 512
    _argc = len(sys.argv)
    
    ip, port = (str(socket.gethostbyname(socket.gethostname())), int(sys.argv[1])) \
        if _argc == 2 \
            else (str(socket.gethostbyname(socket.gethostname())), 45666)

    if validate_ip_port(ip, port) != 0:
        print(f"invalid ip:port.")
        exit(1)
    
    n = Node(ip, port)
    q = Queue(queue_size)
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