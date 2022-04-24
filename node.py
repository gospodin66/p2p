#!/usr/bin/env python3

import threading
import socket
import inputthread
import json
import random
import select
import queue
import sys
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
            "ip": str(ip),
            "port": int(port),
            "type": "MASTER"
        }
        self._socket["socket"].setblocking(False)
        self._socket["socket"].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_connections = [ self._socket ]
        self._INPUT, self._OUTPUT, self._EXCEPT = [], [], []
        self._EXIT_ON_CMD = False
        print(f">>>\n>>> P2P Node {self._socket['ip']} {self._socket['port']}\n>>> exec \"getopts:\" for input options\n>>>\n")


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
    def init_node_as_server(self, c: _Const) -> int:
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
        # current_node_index
        c_i = -1

        # get current socket in tcp_connections list
        for i in range(len(self._tcp_connections)):
            if ip == self._tcp_connections[i]["ip"] and port == self._tcp_connections[i]["port"]:
                c_i = i
                break

        conn_socket = {
            "id": self._tcp_connections[c_i]["id"] if c_i >= 0 else str(random.randint(10000000, 99999999)),
            "socket": socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            "ip": str(ip),
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
            
            # TODO: Connection refused: check if firewall?

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
    def handle_inc_connection(self, stream_in: list, q: queue.Queue, c = _Const) -> int:
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
        
        # TODO: create node socket pair: send MASTER id as OUT => recv OUT here and assign to INC
        #       temp id: random.randint(10000000, 99999999)
        #       sending id immediately when connected causes input() exception

        self._tcp_connections.append({
            "id": str(random.randint(10000000, 99999999)),
            "socket": sock,
            "ip": str(addr[0]),
            "port": int(addr[1]),
            "type": "INC"
        })

        stream_in.append(sock)
        q.put_nowait(self._tcp_connections)

        t = time.strftime(c.TIME_FORMAT, time.localtime())
        print(f"{t} :: new connection <<< {addr[0]}:{addr[1]}")
        return 0


    #
    # connect to all new peers in list | send new peer list to input thread
    #
    def loop_connect_nodes(self, json_list: list, q: queue.Queue) -> None:
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
        q.put_nowait(self._tcp_connections)


    #
    # handle recv from stream_select
    #
    def handle_connections(self, q: queue.Queue, c: _Const) -> int:

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
                    inc_conn_res = self.handle_inc_connection(stream_in, q=q, c=c)
                    if inc_conn_res != 0:
                        return inc_conn_res
                    continue

                if self.is_socket_closed(s):
                    print(f"socket closed! removing..")
                    self.close_socket(s=s, ssi=stream_in, q=q, c=c)
                    continue

                try:
                    inc_data = s.recv(c.BUFFER_SIZE)
                except socket.error as e:
                    print(f"socket error on recv(): {e.args[::-1]}")
                    self.close_socket(s=s, ssi=stream_in, q=q, c=c)
                    continue

                if not inc_data:
                    print("empty packet!")
                    self.close_socket(s=s, ssi=stream_in, q=q, c=c)
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
                    self.loop_connect_nodes(json_list, q)
                    continue

                try:
                    inc_data = inc_data.decode().strip()
                except Exception:
                    print("inc data are bytes..")
               
                if inc_data:
                    if inc_data == "exit:":
                        self.close_socket(s=s, ssi=stream_in, q=q, c=c)
                        break
                    elif inc_data[:7] == "inccmd:":
                        cmd = inc_data[7:]
                        print(f">>> executing command: {cmd} ...")
                        self.exec_cmd(cmd=cmd, ip=ip, q=q, c=c)
                        continue
                
                    t = time.strftime(c.TIME_FORMAT, time.localtime())
                    print(f"{t} :: [{ip}:{port}] :: {inc_data}")

        return 0


    #
    #
    #
    def exec_cmd(self, cmd: str, ip: str, q: queue.Queue, c: _Const) -> int:
        target = {
            "node": self._tcp_connections[node] \
                    for node in range(len(self._tcp_connections)) \
                    if self._tcp_connections[node]["ip"] == ip and self._tcp_connections[node]["type"] == "OUT"
        }
        
        if not target:
            print(f"target {ip} with type \"OUT\" doesn't exist")
            return 1

        cmds = cmd.split(";")
        rets = []
        i=0
        for cmd in cmds:
            cmd_args = cmd.strip().split(" ")
            if not cmd_args[1]:
                cmd_args[1]=""
            print(f"DEBUG: CMD-ARGS: {cmd} ||| {cmd_args}")
            rets[i] = subprocess.run([cmd_args[0], cmd_args[1]], capture_output=True, text=True).stdout
            i+=1

        try:
            ret = '---'.join(rets)
            target["node"]["socket"].send(ret.encode("utf-8"))
        except socket.error as e:
            print(f"socket error on cmd-ret socket.send(): {e.args[::-1]}")
            self.close_socket(s=target["node"]["socket"], ssi=[], q=q, c=c)
            return 1
        except Exception as e:
            print(f"unexpected error on cmd-ret socket.send(): {e.args[::-1]}")
            self.close_socket(s=target["node"]["socket"], ssi=[], q=q, c=c)
            return 1
        
        print(">>> command executed and output back to node")
        return 0


    #
    # disconnect node by command
    # TODO: also remove INC node
    #
    def dc_node(self, ip: str, port: int, q: queue.Queue, c: _Const) -> None:
        for node in range(len(self._tcp_connections)):
            if self._tcp_connections[node]["ip"] == ip and int(self._tcp_connections[node]["port"]) == port:
                self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], q=q, c=c)
                break


    #
    # close socket | remove from lists | re-send new list to stream_in thread
    # ssi => stream-select-inputs list
    #
    def close_socket(self, s: socket.socket, ssi: list, q: queue.Queue, c: _Const) -> None:
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
                print(f"{t} :: disconnected {socket_direction_type} {self._tcp_connections[node]['ip']}:{self._tcp_connections[node]['port']}")
                del self._tcp_connections[node]
                break
        q.put_nowait(self._tcp_connections)


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
    # get connected clients
    #
    def getconns(self) -> None:
        for node in range(len(self._tcp_connections)):
            print(f"{node} - {self._tcp_connections[node]['id']} - {self._tcp_connections[node]['type']} - {self._tcp_connections[node]['ip']}:{self._tcp_connections[node]['port']}")


    #
    # send msg to single node
    #
    def send_to_node(self, ip: str, port: int, msg: bytes, c: _Const) -> int:
        target = {
            "node": self._tcp_connections[node] \
                    for node in range(len(self._tcp_connections)) \
                    if self._tcp_connections[node]["ip"] == ip and self._tcp_connections[node]["port"] == port
        }
        if not target:
            print(f"target {ip}:{port} doesn't exist")
            return 1
        try:
            target["node"]["socket"].send(msg)
        except socket.error as e:
            print(f"socket error on socket.send(): {e.args[::-1]}")
            self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], q=q, c=c)
            return 1
        except Exception as e:
            print(f"unexpected error on socket.send(): {e.args[::-1]}")
            self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], q=q, c=c)
            return 1
        return 0


    #
    #
    #
    def broadcast_msg(self, msg: bytes, q: queue.Queue, c: _Const) -> int:
        for node in range(len(self._tcp_connections)):
            if self._tcp_connections[node]["socket"] == self._socket["socket"]: # not sending to self
                continue
            try:
                self._tcp_connections[node]["socket"].send(msg)
            except socket.error as e:
                print(f"socket error on socket.send(): {e.args[::-1]}")
                self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], q=q, c=c)
                return 1
            except Exception as e:
                print(f"unexpected error on soocket.send(): {e.args[::-1]}")
                self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], q=q, c=c)
                return 1
        return 0


    #
    #
    #
    def cmd_to_node(self, ip: str, port: int, cmd: bytes, c: _Const) -> int:
        target = {
            "node": self._tcp_connections[node] \
                    for node in range(len(self._tcp_connections)) \
                    if self._tcp_connections[node]["ip"] == ip and self._tcp_connections[node]["port"] == port
        }
        if not target:
            print(f"target {ip}:{port} doesn't exist")
            return 1
        # send flag that packets are command
        cmd_flag = "inccmd:".encode("utf-8")
        print(f">>> sending command [{cmd}] to node [{ip}:{port}]")
        try:
            target["node"]["socket"].send(cmd_flag + cmd)
        except socket.error as e:
            print(f"socket error on cmd socket.send(): {e.args[::-1]}")
            self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], q=q, c=c)
            return 1
        except Exception as e:
            print(f"unexpected error on cmd socket.send(): {e.args[::-1]}")
            self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], q=q, c=c)
            return 1
        return 0 


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
def display_options() -> None:
    print("| commands |\n> getopts:\n> getconns:\n> sendfile:{file_path}\n> connnode:127.0.0.1:1111\n> sendtonode:127.0.0.1:1111|{\"message\"}\n> dcnode:127.0.0.1:1111\n> exit")


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


# global callback for input-thread (broadcast/exec messages/commands)
# inp  => input string | bytes
# args => additional args to fnc
def input_callback(inp, args: tuple) -> int:
    #
    # close node from input thread
    # node => Node instance
    def exit_from_cmd(node: Node) -> int:
        node.close_master_socket()
        node._EXIT_ON_CMD = True
        return 1
    #
    # s => Node instance
    # c => _Consts instance
    # q => Queue instance
    node, c, q = (args[0], args[1], args[2])

    if not isinstance(node, Node) or not isinstance(c, _Const) or not isinstance(q, queue.Queue):
        print("input-callback: invalid class instances.. exiting input thread..")
        return 1
    
    # update input-thread tcp connections list
    if not q.empty():
        new_list = q.get_nowait()
        node.set_connections(new_list)
        q.task_done()

    if inp[:9] == "sendfile:":
        print("sending file..")
        out = r_file(inp.split(":")[1])
        # TODO: send & recv file as function

    elif inp == "getopts:":
        display_options()
        return 0

    elif inp == "getconns:":
        node.getconns()
        return 0

    elif inp[:9] == "connnode:":
        addr = inp[9:len(inp)].split(":")
        if validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 1
        node.connect_to_node(ip=str(addr[0]), port=int(addr[1]))
        return 0

    elif inp[:7] == "dcnode:":
        addr = inp[7:len(inp)].split(":")
        if validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 1
        node.dc_node(ip=str(addr[0]), port=int(addr[1]), q=q, c=c)
        return 0

    elif inp[:11] == "sendtonode:":
        addr = inp[11:inp.index("|", 11, len(inp))].split(":")
        msg = inp[inp.index("|", 11, len(inp)):].lstrip("|")
        if validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 1
        node.send_to_node(ip=str(addr[0]), port=int(addr[1]), msg=msg.encode("utf-8"), c=c)
        return 0

    elif inp[:10] == "cmdtonode:":
        addr = inp[10:inp.index("|", 10, len(inp))].split(":")
        cmd = inp[inp.index("|", 10, len(inp)):].lstrip("|")
        if validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 1
        node.cmd_to_node(ip=str(addr[0]), port=int(addr[1]), cmd=cmd.encode("utf-8"), c=c)
        return 0


    elif inp == "exit:":
        return exit_from_cmd(node)

    else:
        # default
        out = inp.encode("utf-8")

    node.broadcast_msg(msg=out, q=q, c=c)

    return 0


#
#
#
def main():
    _argc = len(sys.argv)
    # ip:port provided
    if _argc == 3:
        if not isinstance(sys.argv[1], str) \
        or not isinstance(sys.argv[2], str) \
        or not sys.argv[2].isnumeric():
            print(f"invalid arguments type for ip::port >>> {sys.argv[1]}::{sys.argv[2]}")
            exit(1)

        ip, port = (str(sys.argv[1]), int(sys.argv[2]))
    # no args
    else:
        default_port = 45666
        if _argc == 1:
            # assign default host ip & port
            ip, port = (str(socket.gethostbyname(socket.gethostname())), default_port)
            print(f"ip:port not provided >>> using default host ip with default port >>> {ip}:{port}")
        elif _argc == 2:
            # assign default port
            ip, port = (str(sys.argv[1]), default_port)
            print(f"port not provided >>> using default port >>> {ip}:{port}")
        else:
            print("invalid arguments")
            exit(1)

    if validate_ip_port(ip, port) != 0:
        exit(1)
    
    s = Node(ip, port)
    q = queue.Queue(20)
    c = _Const()

    # init non-blocking input thr
    inputthread.InputThread(input_callback=input_callback, args=(s, c, q))

    # init node as tcp server
    if s.init_node_as_server(c) != 0:
        print("[!] failed to initialize node as server")
        exit(1)

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