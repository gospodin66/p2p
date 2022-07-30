#!/usr/bin/env python3

#######################################################################
### NODE 0 [MASTER] - not executing commands                        ###
###                 - input                                         ###
###                 - TODO: selective connections (not any in list) ###
###                 - ?????????                                     ###
###                 - ?????????                                     ###
###                 - ?????????                                     ###
###                                                                 ###
#######################################################################
#######################################################################
import socket
import select
import queue
import node_fnc
import random
import json
import errno
import base64
import time


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


    def get_socket(self) -> socket.socket:
        return self._socket


    def get_connections(self) -> list:
        return self._tcp_connections


    def set___list(self, newlist: list) -> None:
        self.__list = newlist


    def set_connections(self, connections: list):
        self._tcp_connections = connections


    #
    #
    #
    def init_server(self, c: node_fnc._Const) -> int:

        node_fnc.write_log(">>> Initializing server..", c)

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
    def connect_to_node(self, ip: str, port: int, c: node_fnc._Const) -> int:
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

        for node in range(len(self._tcp_connections)):
            if self._tcp_connections[node]["ip"] == conn_socket["ip"] \
            and self._tcp_connections[node]["port"] == conn_socket["port"]:
                print(f"{t} :: node {conn_socket['ip']}:{conn_socket['port']} is already connected.")
                return 1

        try:
            conn_socket["socket"].connect((conn_socket["ip"], conn_socket["port"]))
        except socket.error as e:
            print(f"socket error on socket.connect(): {ip}:{port} :: {e.args[::-1]}")
            return 1
        except Exception as e:
            print(f"unexpected error on socket.connect(): {ip}:{port} :: {e.args[::-1]}")
            return 1

        self._tcp_connections.append(conn_socket)
        self.send_list(target=conn_socket["socket"])

        out = f"new connection >>> {conn_socket['ip']}:{conn_socket['port']}"
        node_fnc.write_log(out, c)

        print(f"{t} :: {out}")

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

        # convert to string with newlines
        out1 = "inc-conns:"
        out2 = "\n".join(f"{peer['ip']}:{peer['port']}" for peer in self.__list)
        
        out = (out1 + out2).encode()

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
            return True
        except BlockingIOError:
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
    def handle_inc_connection(self, stream_in: list, q: queue.Queue, c: node_fnc._Const) -> int:
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
        q.put_nowait(self._tcp_connections)

        t = time.strftime(c.TIME_FORMAT, time.localtime())

        out = f"new connection <<< {addr[0]}:{addr[1]}"
        node_fnc.write_log(out, c)

        print(f"{t} :: {out}")


        return 0


    #
    # connect to all new peers in list | send new peer list to input thread
    #
    def loop_connect_nodes(self, peer_list: str, q: queue.Queue, c: node_fnc._Const) -> None:

        peer_list_arr = peer_list.split("\n")
        peers_len = range(len(peer_list_arr))

        for node in peers_len:
            
            if not isinstance(node, str):
                # print("skipping int value - DEBUG: ", peer_list_arr)
                continue

            node = node.strip()

            ip = node[:(node.find(':'))]
            port = int(node[(node.find(':') +1):])
            
            already_connected = False
            # not connecting to self
            if ip == self._socket["ip"] \
            and port == self._socket["port"]:
                continue

            # not connecting to already connected
            for i in range(len(self._tcp_connections)):
                if self._tcp_connections[i]["ip"] == ip \
                and self._tcp_connections[i]["port"] == port:
                    already_connected = True
                    break
            
            if already_connected:
                continue

            # selective connections
            #if peer_list[node]["type"] == 'OUT':
            #    ans = input(f">>> accept connection from {peer_list[node]['ip']}:{peer_list[node]['port']} ??")
            #    if ans and (ans == 'y' or ans == 'yes'):
            #        self.connect_to_node(ip=peer_list[node]["ip"], port=peer_list[node]["port"], c=c)
            #    else:
            #        print(f"skipping {peer_list[node]['ip']}:{peer_list[node]['port']}")
            #else:
            #    self.connect_to_node(ip=peer_list[node]["ip"], port=peer_list[node]["port"], c=c)
            self.connect_to_node(ip=ip, port=port, c=c)
            
        q.put_nowait(self._tcp_connections)


    #
    # handle recv from stream_select
    #
    # saved_stream_in => list of sockets
    #
    def handle_connections(self, q: queue.Queue, c: node_fnc._Const) -> int:

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
            except ValueError as e:
                print("ValueError: FD -1 -- node disconnected unexpectedly -- removing from input stream")
                for s in stream_in:
                    if s.fileno() == -1:
                        stream_in.remove(s)
                        continue                
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

                inc = {
                    "node": self._tcp_connections[node] \
                            for node in range(len(self._tcp_connections)) \
                            if self._tcp_connections[node]["socket"] == s
                }

                if not inc:
                    print(">>> node not found?")
                    continue

                # if client disconnects unexpectedly
                if self.is_socket_closed(s=inc['node']['socket']):
                    self.dc_node(ip=inc['node']['ip'], q=q, c=c)
                    continue

                try:
                    inc_data = inc['node']['socket'].recv(c.BUFFER_SIZE)
                except socket.error as e:
                    print(f"socket error on recv(): {e.args[::-1]}")
                    self.dc_node(ip=inc['node']['ip'], q=q, c=c)
                    continue

                if not inc_data:
                    print("empty packet!")
                    self.dc_node(ip=inc['node']['ip'], q=q, c=c)
                    continue

                if isinstance(inc_data, bytes):
                    inc_data = inc_data.decode().strip()

                if inc_data:
                    if inc_data == "exit:":
                        self.dc_node(ip=inc['node']['ip'], q=q, c=c)
                        break

                    elif inc_data[:10] == "inc-conns:":
                        self.loop_connect_nodes(peer_list=inc_data[10:], q=q, c=c)
                        continue

                    elif inc_data[:12] == "inc-ret-cmd:":
                        try:
                            inc_data = base64.b64decode(inc_data[12:]).decode()
                            if isinstance(inc_data, bytes):
                                inc_data = inc_data.decode()
                        except Exception as e:
                            print(f"unexpected error on base64-decode: {e.args[::-1]}")

                    elif node_fnc.isbase64(inc_data):
                        inc_data = base64.b64decode(inc_data[12:]).decode()
                        if isinstance(inc_data, bytes):
                            inc_data = inc_data.decode()

                    t = time.strftime(c.TIME_FORMAT, time.localtime())
                    print(f"{t} :: [{inc['node']['ip']}:{inc['node']['port']}] :: {inc_data}")

        return 0


    #
    # disconnect both node sockets
    #
    def dc_node(self, ip: str, q: queue.Queue, c: node_fnc._Const) -> None:
        inc_type_port, out_type_port = (0, 0)
        operation_success=False
        # close "OUT" socket
        for node in range(len(self._tcp_connections)):
            if self._tcp_connections[node]["ip"] == ip:
                if self._tcp_connections[node]["type"] == "OUT":
                    out_type_port = int(self._tcp_connections[node]["port"])

                if self._tcp_connections[node]["ip"] == ip and \
                (out_type_port > 0 and self._tcp_connections[node]["port"] == out_type_port) and \
                self._tcp_connections[node]["type"] == "OUT":
                    self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], q=q, c=c)
                    break
        # close "INC" socket
        for node in range(len(self._tcp_connections)):
            if self._tcp_connections[node]["ip"] == ip:
                # get "INC" socket port
                if self._tcp_connections[node]["type"] == "INC":
                    inc_type_port = int(self._tcp_connections[node]["port"])

                if self._tcp_connections[node]["ip"] == ip and \
                (inc_type_port > 0 and self._tcp_connections[node]["port"] == inc_type_port) and \
                self._tcp_connections[node]["type"] == "INC":
                    self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], q=q, c=c)
                    operation_success=True
                    break

        if operation_success:
            print(f">>> sockets closed successfuly for ip [{ip}].")
        else:
            print(f">>> error! sockets not closed for ip [{ip}].")


    #
    # close socket | remove from lists | re-send new list to stream_in thread
    # ssi => stream-select-inputs list
    #
    def close_socket(self, s: socket.socket, ssi: list, q: queue.Queue, c: node_fnc._Const) -> None:
        try:
            s.shutdown(socket.SHUT_RDWR)
        except socket.error as e:
            pass
        
        s.close()

        # exiting by request - stream-input as empty array
        if ssi:
            ssi.remove(s)
        for node in range(len(self._tcp_connections)):
            if node and self._tcp_connections[node]["socket"] == s:
                t = time.strftime(c.TIME_FORMAT, time.localtime())
                socket_direction_type = ">>>" if self._tcp_connections[node]['type'] == "OUT" else "<<<"

                out = f"disconnected {self._tcp_connections[node]['ip']}:{self._tcp_connections[node]['port']} | type: {socket_direction_type}"
                
                node_fnc.write_log(out, c)
                print(f"{t} :: {out}")

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
            self.dc_node(c["ip"])
            # c["socket"].shutdown(socket.SHUT_RDWR)
            # c["socket"].close()
            # socket_direction_type = ">>>" if c['type'] == "OUT" else "<<<"
            print(f"{t} :: disconnected {c['ip']}:{c['port']}")
            time.sleep(0.5)
        self.set_connections([])
        self._socket["socket"].shutdown(socket.SHUT_RDWR)
        self._socket["socket"].close()
        print("disconnected all clients..\nmaster socket closed!")


    #
    # get connected clients
    #
    def conninfo(self) -> None:
        for node in range(len(self._tcp_connections)):
            print(f"{node} - {self._tcp_connections[node]['id']} - {self._tcp_connections[node]['type']} - {self._tcp_connections[node]['ip']}:{self._tcp_connections[node]['port']}")


    #
    # send msg to single node
    #
    def send_to_node(self, ip: str, port: int, msg: bytes, c: node_fnc._Const, q: queue.Queue) -> int:
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
            self.dc_node(ip=ip, q=q, c=c)
            return 1
        except Exception as e:
            print(f"unexpected error on socket.send(): {e.args[::-1]}")
            self.dc_node(ip=ip, q=q, c=c)
            return 1
        return 0


    #
    #
    #
    def broadcast_msg(self, msg: bytes, c: node_fnc._Const, q: queue.Queue) -> int:

        out = f"broadcasting >>> {msg}"

        for node in range(len(self._tcp_connections)):
            if self._tcp_connections[node]["socket"] == self._socket["socket"]: # not sending to self
                continue
            try:
                node_fnc.write_log(out, c)
                self._tcp_connections[node]["socket"].send(msg)
            except socket.error as e:
                print(f"socket error on socket.send(): {e.args[::-1]}")
                self.dc_node(ip=self._tcp_connections[node]["ip"], q=q, c=c)
                return 1
            except Exception as e:
                print(f"unexpected error on soocket.send(): {e.args[::-1]}")
                self.dc_node(ip=self._tcp_connections[node]["ip"], q=q, c=c)
                return 1
        return 0


    #
    #
    #
    def cmd_to_node(self, ip: str, port: int, cmd: bytes, c: node_fnc._Const, q: queue.Queue) -> int:
        target = {
            "node": self._tcp_connections[node] \
                    for node in range(len(self._tcp_connections)) \
                    if self._tcp_connections[node]["ip"] == ip and self._tcp_connections[node]["port"] == port
        }
        if not target:
            print(f"target {ip}:{port} doesn't exist")
            return 1
        # send flag that packets are command
        cmd_flag = "inccmd:".encode()
        print(f">>> sending command [{cmd.decode()}] to node [{ip}:{port}]")
        try:
            target["node"]["socket"].send(cmd_flag + cmd)
        except socket.error as e:
            print(f"socket error on cmd socket.send(): {e.args[::-1]}")
            self.dc_node(ip=ip, q=q, c=c)
            return 1
        except Exception as e:
            print(f"unexpected error on cmd socket.send(): {e.args[::-1]}")
            self.dc_node(ip=ip, q=q, c=c)
            return 1
        return 0 


    #
    #
    #
    def conn_from_list(self, q: queue.Queue, c: node_fnc._Const) -> None:
        ip = b''
        ips_path = '/p2p/ips.txt'
        try:
            with open(ips_path, "r") as f:
                while (ip := f.readline().rstrip()):

                    if ip == self._socket['ip']:
                        print("[!] skipping self..")
                        continue

                    port = 45666

                    print(f"[!] connecting to peer {ip}:{port}")
                    self.connect_to_node(ip=ip, port=port, c=c)
                    q.put_nowait(self._tcp_connections)
                    time.sleep(0.5)

        except Exception as e:
            print(f"unexpected error on file.read() in conn_from_list(): {e.args[::-1]}")
    

###### TODO: implement a function to check on nodes connections (broadcast ping) & clear list accordingly