#!/usr/bin/python3

import socket
import queue
import node
import inputthread
import node_fnc
import inputcallback
import sys

def main():
    _argc = len(sys.argv)
    # ip:port provided
    if _argc >= 2:
        host = sys.argv[1].split(':')

        if len(host) == 2:
            # specified host
            ip, port = (str(host[0]), int(host[1]))
        elif len(host) == 1:
            # default host
            ip, port = (str(socket.gethostbyname(socket.gethostname())), int(host[0]))
        else:
            print(f"invalid host (ip:port): {host}")
            exit(1)

        if node_fnc.validate_ip_port(ip, port) != 0:
            print(f"invalid host (ip:port): {host}")
            exit(1)

        # initial target provided
        if _argc == 3:
            rn_0 = sys.argv[2].split(':')
            ip_0, port_0 = (str(rn_0[0]), int(rn_0[1]))
        else:
            ip_0, port_0 = (None, None)

    # no args
    else:
        ip_0, port_0 = (None, None)
        default_port = 45666

        if _argc == 1:
            # assign default host ip & port
            ip, port = (str(socket.gethostbyname(socket.gethostname())), default_port)
            print(f"ip:port not provided >>> using default host ip with default port >>> {ip}:{port}")
        else:
            print("invalid arguments")
            exit(1)
    
    n = node.Node(ip, port)
    q = queue.Queue(20)
    c = node_fnc._Const()

    # init non-blocking input thr
    inpthr = inputthread.InputThread(input_callback=inputcallback.input_callback, _node=n, _const=c, _queue=q)
    # thread watcher
    while 1:
        if not inpthr.is_alive():
            print("re-starting input-thread")
            inpthr = None
            inpthr = inputthread.InputThread(input_callback=inputcallback.input_callback, _node=n, _const=c, _queue=q)
            break
        else:
            print("input-thread is alive.")
            break

    # init node as tcp server
    if n.init_server(c) != 0:
        print("[!] failed to initialize node as server")
        exit(1)

    print(f">>>\n>>> P2P Node {ip}:{port}\n>>>")

    # make initial connection
    if ip_0 and port_0 and node_fnc.validate_ip_port(ip_0, port_0) == 0:
        print(f">>> connecting to node-0 [{ip_0}:{port_0}]")
        n.connect_to_node(ip=ip_0, port=port_0, c=c)

    while True:    
        ret = n.handle_connections(q=q, c=c)
        if ret != 0:
            print(">>> breaking handle connections loop")
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
    main()