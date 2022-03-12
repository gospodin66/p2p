#!/usr/bin/env python3

import threading
import socket
import kthr
import select
import queue
import sys
import errno
import time
from dataclasses import dataclass

@dataclass(frozen=True)
class _Const:
    BUFFER_SIZE = 1024
    MAX_CONNECTIONS = 20
    TIME_FORMAT = "%Y-%m-%d %I:%M:%S %p"


class Node:

    def __init__(self, ip: str, port: int) -> None:
        self.thr_list = []
        self._socket = {
            "socket": socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            "ip": str(ip),
            "port": int(port),
            "type": "MASTER"
        }
        self._socket["socket"].setblocking(False)
        self._socket["socket"].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_connections = [ self._socket ]
        self._INPUT, self._OUTPUT, self._EXCEPT = [], [], []


    def get_socket(self):
        return self._socket


    def get_connections(self):
        return self._tcp_connections


    def set_connections(self, connections: list):
        self._tcp_connections = connections
        return

    # c => _Consts instance
    def init_node_as_server(self, c: _Const) -> None:
        try:
            self._socket["socket"].bind((self._socket["ip"], self._socket["port"]))
            self._socket["socket"].listen(c.MAX_CONNECTIONS)
            print(f"server listening on {self._socket['ip']}:{self._socket['port']}")
        except socket.error as e:
            print(f"unexpected error on bind/listen: {e.args[::-1]}")
        return


    def connect_to_node(self, ip, port) -> int:
        conn_socket = {
            "socket": socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            "ip": str(ip),
            "port": int(port),
            "type": "OUT"
        }
        try:
            conn_socket["socket"].connect((conn_socket["ip"], conn_socket["port"]))
            # update input keyboard to send to new socket
            self._tcp_connections.append(conn_socket)
            # q.put_nowait(conn_socket)
            print(f"connected to node: {ip}:{port}")
            print("input thread updated.")
        except socket.error as e:
            print(f"error on socket-connect: {e.args[::-1]}")
            return 1

        return 0

    # q => Queue instance
    # c => _Consts instance
    def handle_connections(self, q: queue.Queue, c: _Const) -> int:

        stream_in = [ self._socket["socket"] ]
        select_timeout_sec = 3

        while True:
            try:
                self._INPUT, self._OUTPUT, self._EXCEPT = select.select(stream_in, [], [], select_timeout_sec)
            except select.error as e:
                if self._EXIT_ON_CMD:
                    return 1
                print(f"socket-select error: {e.args[::-1]}")
                return -1
            except Exception as e:
                if self._EXIT_ON_CMD:
                    return 1
                print(f"unexpected error on socket-select: {e.args[::-1]}")
                return -1

            for s in self._INPUT:
                if s == self._socket["socket"]:
                    # new connection
                    try:
                        conn, addr = self._socket["socket"].accept()
                        conn.setblocking(False)
                    except socket.error as e:
                        if self._EXIT_ON_CMD:
                            return 1
                        print(f"socket error on accept: {e.args[::-1]}")
                        return -1
                    except Exception as e:
                        if self._EXIT_ON_CMD:
                            return 1
                        print(f"unexpected error on accept: {e.args[::-1]}")
                        return -1
                    self._tcp_connections.append({
                        "socket": conn,
                        "ip": str(addr[0]),
                        "port": int(addr[1]),
                        "type": "INC"
                    })
                    stream_in.append(conn)
                    q.put_nowait(self._tcp_connections)
                    print(f"new connection: {addr[0]}:{addr[1]}")
                    continue

                ip, port = s.getpeername()
                c_i = 0 # current_node_index

                # get current socket in both input & tcp_connections list
                for i in range(len(self._tcp_connections)):
                    sock = self._tcp_connections[i]["socket"]
                    if sock != self._socket["socket"] and sock == s:
                        c_i = i
                        break

                inc_data = s.recv(c.BUFFER_SIZE)

                if not inc_data:
                    print("empty packet!")
                    self.close_socket(s, stream_in, q)

                try:
                    inc_data = inc_data.decode().strip()
                except Exception:
                    print("inc-data are bytes..")

               
                if inc_data != "":
                    if inc_data == "exit:":
                        self.close_socket(s, stream_in, q)
                        break
                
                    t = time.strftime(c.TIME_FORMAT, time.localtime())
                    print(f"{t} :: [{ip}:{port}] :: {inc_data}")

        return 0


    # close socket | remove from lists | re-send new list to stream_in thread
    # s  => socket resource
    # si => stream select inputs list
    # q  => Queue instance
    def close_socket(self, s: socket.socket, si: list, q: queue.Queue) -> None:
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        # exiting by request - stream-input as empty array
        if si:
            si.remove(s)
        for i in range(len(self._tcp_connections)):
            if self._tcp_connections[i].get('socket') == s:
                ip, port = (self._tcp_connections[i]["ip"], self._tcp_connections[i]["port"])
                del self._tcp_connections[i]
                print(f"client {ip}:{port} disconnected!")
                break
        q.put_nowait(self._tcp_connections)
        print("sent new list to input thread..")
        return


    # close master socket & clear connections list
    def close_master_socket(self) -> None:
        connections = self._tcp_connections
        for c in connections:
            if c["socket"] == self._socket["socket"]:
                continue
            c["socket"].shutdown(socket.SHUT_RDWR)
            c["socket"].close()
            print(f"client {c['ip']}:{c['port']} disconnected!")
        self.set_connections([])
        self._socket["socket"].shutdown(socket.SHUT_RDWR)
        self._socket["socket"].close()
        print("disconnected all clients..\nmaster socket closed!")
        return



# read file
def r_file(fpath: str) -> bytes:
    fcontents = b''
    try:
        print(f"PATH: {fpath}")
        with open(fpath, "rb") as f:
            fcontents += f.read()
    except Exception as e:
        print(f"an unexpected error occurred on reading file: {e.args[::-1]}")
        return b''
    return fcontents


# get connected clients
# conns => connected clients list
def getconns(conns: list) -> None:
    for node in range(len(conns)):
        print(f"{node} - {conns[node]['type']} - {conns[node]['ip']}:{conns[node]['port']}")
    return


# global callback for input-thread (broadcast/exec messages/commands)
# inp  => input string | bytes
# args => additional args to fnc
def input_callback(inp, args: tuple) -> int:
    #
    # close server from input thread
    # s => Node instance
    def exit_from_cmd(server: Node) -> int:
        server.close_master_socket()
        server._EXIT_ON_CMD = True
        return 1
    #
    # s => Node instance
    # c => _Consts instance
    # q => Queue instance
    s, c, q = (args[0], args[1], args[2])

    if not isinstance(s, Node) or  not isinstance(c, _Const) or not isinstance(q, queue.Queue):
        print("input-callbacK: invalid class instances.. exiting input thread..")
        return 1
    
    # update input-thread tcp connections list
    if not q.empty():
        new_list = q.get_nowait()
        s.set_connections(new_list)
        q.task_done()

    if "sendfile:" in inp:
        print("sending file..")
        out = r_file(inp.split(":")[1])

    elif inp == "getconns:":
        getconns(s._tcp_connections)
        return 0

    # connnode:192.168.3.148:44555
    elif "connnode:" in inp :
        addr = inp[9:len(inp)].split(":")
        s.connect_to_node(addr[0], addr[1])
        return 0
  
    elif inp == "exit:":
        return exit_from_cmd(s)

    else:
        # default
        out = inp.encode("utf-8")


    for i in range(len(s._tcp_connections)):    
        # not sending to self
        if s._tcp_connections[i]["socket"] == s._socket["socket"]:
            continue
        try:
            s._tcp_connections[i]["socket"].send(out)
        except socket.error as e:
            print(f"unexpected error on send: {e.args[::-1]}")
            s.close_socket(s=s._socket["socket"], si=[], q=q)
            break
        
    return 0

def main():
    if len(sys.argv) != 3:
        print("enter ip:port")
        exit(1)

    ip, port = (str(sys.argv[1]), int(sys.argv[2]))

    # validate ip
    try:
        socket.inet_aton(ip)
    except socket.error as e: 
        print(f"invalid ip address: {e.args[::-1]}")
        exit(1)
    # validate port
    if 0 < port > 65535:
        print("port number not in range")
        exit(1)

    s = Node(ip, port)
    q = queue.Queue(20)
    c = _Const()

    # init non-blocking input thr
    kthr.KThr(input_callback=input_callback, args=(s, c, q))

    # init tcp server
    s.init_node_as_server(c)
    ret = s.handle_connections(q, c)
    if ret == 0:
        print(f"exited normally with [{ret}]")
        s.close_master_socket()
    elif ret == 1:
        print(f"exited by cmd with [{ret}]")
    else:
        print(f"exited with error [{ret}]")
    
    exit(ret)


if __name__ == '__main__':
    main()