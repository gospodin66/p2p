#!/usr/bin/env python3

#######################################################################
### NODE 0 [MASTER] - not executing commands                        ###
###                 - input                                         ###
###                 - TODO: selective connections                   ###
###                 - ?????????                                     ###
###                 - ?????????                                     ###
###                 - ?????????                                     ###
###                 - send connections list to each new node        ###
#######################################################################
#######################################################################

###### TODO: implement a function to check on nodes connections (broadcast ping) & clear list accordingly

###### TODO: implement global list of peers which will be redistributed among peers (obfuscate node-0 => tunnel?)

###### TODO: implement encryption 


import socket
import select
import tcp_http
import subprocess
import errno

from node_fnc import _Const, write_log, isbase64, validate_ip_port
from queue import Queue
from ipaddress import ip_address
from re import search as regex_search
from time import strftime, localtime, sleep
from random import randint
from base64 import b64encode, b64decode
from typing import Union

# Console colors
W = '\033[0m'  # white (normal)
R = '\033[31m'  # red
G = '\033[32m'  # green
O = '\033[33m'  # orange
B = '\033[34m'  # blue
P = '\033[35m'  # purple
C = '\033[36m'  # cyan
GR = '\033[37m'  # gray
BOLD = '\033[1m'
END = '\033[0m'

class Node:

    def __init__(self, ip: str, port: int) -> None:
        self._socket = {
            "id": str(randint(10000000, 99999999)),
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

    
    def set_connections_from_thread(self, connections: list):
        self._tcp_connections = connections


    #
    #
    #
    def init_server(self, c: _Const) -> int:

        write_log(">>> Initializing server..", c)

        try:
            self._socket["socket"].bind((self._socket["ip"], self._socket["port"]))
            self._socket["socket"].listen(c.MAX_CONNECTIONS)
        except socket.error as e:
            print(f"socket error on socket.bind()/socket.listen(): {e.args[::-1]}")
            return 1
        except Exception as e:
            print(f"error on socket.bind()/socket.listen(): {e.args[::-1]}")
            return 1
        return 0


    #
    # connect to peer
    #
    def connect_to_node(self, ip: str, port: int, q: Queue, c: _Const) -> int:
        target = {
            "id": self._tcp_connections[i]["id"] \
                    for i in range(len(self._tcp_connections)) \
                    if ip == self._tcp_connections[i]["ip"] and port == self._tcp_connections[i]["port"]
        }

        if target:
            node_id = target["id"]
        else:
            #print(f"[!] unable to find node_id for OUT target: {target}")
            node_id = str(randint(10000000, 99999999))

        conn_socket = {
            "id": node_id,
            "socket": socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            "ip": ip,
            "port": int(port),
            "type": "OUT"
        }

        t = strftime("%Y-%m-%d %I:%M:%S %p", localtime())

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
            print(f"error on socket.connect(): {ip}:{port} :: {e.args[::-1]}")
            return 1

        self._tcp_connections.append(conn_socket)
        self.send_list(target=conn_socket["socket"])

        out = f"connected {'':<5}>>> {conn_socket['ip']}:{conn_socket['port']}"
        write_log(out, c)

        print(f"{t} :: {out}")
        q.put_nowait(self._tcp_connections)

        return 0



    #
    #
    #
    def renew_ip_list(self, ips_list: list, output_path: str) -> list:
        print(f"Scanning networks: {ips_list}")
        try:
            subprocess.run([
                    "sh", 
                    "-c", 
                    "nmap -n -sn "+' '.join(ips_list)+" -oG - | awk '/Up$/{print $2}' | sort -V | tee "+str(output_path)
                ],
                capture_output=True,
                timeout=60,
                check=True
            )
        except FileNotFoundError as exc:
            print(f"Process failed because the executable could not be found.\n{exc}")
            return []
        except subprocess.CalledProcessError as exc:
            print(
                f"Process failed because did not return a successful return code. "
                f"Returned {exc.returncode}\n{exc}"
            )
            return []
        except subprocess.TimeoutExpired as exc:
            print(f"Process timed out.\n{exc}")
            return []

        nodes = []
        with open(output_path, 'r') as f:
            nodes = f.read()

        print("Networks scanned -- ips list updated.")

        return nodes



    def remote_connection_closed(self, sock: socket.socket) -> bool:
        """
        Returns True if the remote side did close the connection

        """
        try:
            buf = sock.recv(1, socket.MSG_PEEK | socket.MSG_DONTWAIT)
            if buf == b'':
                return True
        except BlockingIOError as exc:
            if exc.errno != errno.EAGAIN:
                # Raise on unknown exception
                raise
        return False


    #
    #
    #
    def reset_connections(self, q: Queue):
        ips_list = ["10.244.1-2.2-255"]
        output_path = "/p2p/ips.txt"

        self.loop_close_all_sockets(q=q)
        self.renew_ip_list(ips_list=ips_list, output_path=output_path)


    #
    # send peer list to target
    #
    def send_list(self, target: socket.socket) -> None:
        
        temp_list = []

        for i in range(len(self._tcp_connections)):
            ftd = {}
            for key, val in self._tcp_connections[i].items():
                if key == 'socket':
                    continue
                ftd[key] = val
            temp_list.append(ftd)

        # filter nodes => send only OUT & MASTER sockets
        temp_list[:] = (node for node in temp_list if node["type"] != "INC")

        # convert to string with newlines
        peerslist = "\r\n".join(f"{peer['ip']}:{peer['port']}" for peer in temp_list)
        
        b64out = "inc-conns:".encode() + b64encode(peerslist.encode())

        # print(f"DEBUG: sending list:\r\n{peerslist}\r\n")

        temp_list.clear()
        target.sendall(b64out)


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
    def handle_inc_connection(self, stream_in: list, q: Queue, c: _Const) -> int:
        try:
            sock, addr = self._socket["socket"].accept()
            sock.setblocking(False)
        except socket.error as e:
            if self._EXIT_ON_CMD:
                return 1
            if e.errno == 11:
                # chrome's favicon request results with 'resource unavailable' error when dropped
                print(f"socket.accept(): {e.args[::-1]}")
                return 0
            print(f"socket error on socket.accept(): {e.args[::-1]}")
            return -1
        except Exception as e:
            if self._EXIT_ON_CMD:
                return 1
            print(f"error on socket.accept(): {e.args[::-1]}")
            return -1
        
        target = {
            "id": self._tcp_connections[i]["id"] \
                    for i in range(len(self._tcp_connections)) \
                        if addr[0] == self._tcp_connections[i]["ip"]
        }

        node_id = target["id"] if target else str(randint(10000000, 99999999))

        self._tcp_connections.append({
            "id": node_id,
            "socket": sock,
            "ip": addr[0],
            "port": int(addr[1]),
            "type": "INC"
        })
        
        stream_in.append(sock)
        q.put_nowait(self._tcp_connections)

        t = strftime(c.TIME_FORMAT, localtime())

        # drop master when searching
        pairs_in_list = len([n for n in self._tcp_connections[1:] if n['id'] == node_id])

        out = f"connected {'':<5}<<< {addr[0]}:{addr[1]}"
        write_log(out, c)

        print(f"{t} :: {out}")

        if pairs_in_list < 2:
            print(f"did not found ID pair -- reverse-connecting to node..")
            self.connect_to_node(ip=addr[0], port=45666, q=q, c=c)


        return 0


    #
    # connect to all new peers in list | send new peer list to input thread
    #
    def loop_connect_nodes(self, peer_list: str, q: Queue, c: _Const) -> None:

        peer_list_arr = peer_list.splitlines()
        peers_len = range(len(peer_list_arr))

        for node in peers_len:
            if not isinstance(node, str):
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

            # TODO: selective connections
            
            if validate_ip_port(ip=ip, port=port):
                continue

            self.connect_to_node(ip=ip, port=port, q=q, c=c)
            

    #
    # handle recv from stream_select
    #
    # saved_stream_in => list of sockets
    #
    def handle_connections(self, q: Queue, c: _Const) -> int:

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
                # print("ValueError: FD -1 -- node disconnected unexpectedly -- removing from input stream")
                for s in stream_in:
                    if s.fileno() == -1:
                        stream_in.remove(s)
                        continue                
            except Exception as e:
                if self._EXIT_ON_CMD:
                    return 1
                print(f"error on select.socket-select(): {e.args[::-1]}")
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
                    # print(">>> node not found?")
                    continue

                # if client disconnects unexpectedly
                if self.is_socket_closed(s=inc['node']['socket']):
                    self.dc_node(ip=inc['node']['ip'], q=q, c=c)
                    continue

                # get data
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

                try:
                    if isinstance(inc_data, bytes):
                        inc_data = inc_data.decode().strip()
                except Exception as e:
                    print(f"error on decoding received data: {e.args[::-1]}")
                    return 0

                if inc_data:
                    t = strftime(c.TIME_FORMAT, localtime())
                    #
                    # HTTP (plaintext) => auto-response over same socket
                    #
                    if self.check_http_request(data=inc_data):
                        # drop blacklisted requests => 403
                        blacklist = tcp_http.get_blacklist()
                        break_continue = False
                        for request_path in blacklist:
                            if regex_search(f"{request_path}", inc_data):
                                print(f"dropping blacklisted request: {request_path}")
                                headers_arr = tcp_http.set_http_headers()
                                headers_str = "\r\n".join(str(header) for header in headers_arr)
                                response = f"HTTP/1.1 403 Forbidden\r\n{headers_str}\r\n"
                                s.send(response.encode('utf-8'))
                                self.close_socket(s=s, ssi=stream_in, q=q, c=c)
                                break_continue = True
                                break
                        if break_continue:
                            # do not print blacklisted requests
                            continue
                        # craft & send HTTP response to target
                        response = tcp_http.craft_http_response(inc_data)
                        s.send(response.encode('utf-8'))
                        # close socket for response to be received and rendered at endpoint
                        self.close_socket(s=s, ssi=stream_in, q=q, c=c)
                        data_formatted = inc_data.replace("\r\n", f"\r\n{'':<46}")
                        output = f"{t} :: [{inc['node']['ip']}:{inc['node']['port']}] :: {B}{data_formatted}{END}"
                        print(output)
                        write_log(output, c)
                    #
                    # NON-HTTP (pure tcp)
                    #
                    else:
                        # chec if bidirectional (2 sockets)
                        pairs_in_list = len([n for n in self._tcp_connections[1:] if n['id'] == inc['node']['id']])
                        if pairs_in_list != 0 and pairs_in_list < 2:
                            print(f"[!] did not found ID pair -- reverse-connecting to node..")
                            self.connect_to_node(ip=inc['node']['ip'], port=45666, q=q, c=c)
                        #
                        # tcp (bytes)
                        #
                        if inc_data == "exit:":
                            self.dc_node(ip=inc['node']['ip'], q=q, c=c)
                            break

                        elif inc_data[:10] == "inc-conns:":
                            try:
                                peerlist = b64decode(inc_data[10:]).decode()
                                if isinstance(peerlist, bytes):
                                    peerlist = peerlist.decode()
                                self.loop_connect_nodes(peer_list=peerlist, q=q, c=c)
                                continue
                            except Exception as e:
                                print(f"error on base64-decode connection-list: {e.args[::-1]}")

                        elif inc_data[:12] == "inc-ret-cmd:":
                            try:
                                inc_data = b64decode(inc_data[12:]).decode()
                                if isinstance(inc_data, bytes):
                                    inc_data = inc_data.decode()
                            except Exception as e:
                                print(f"error on base64-decode returning-cmd: {e.args[::-1]}")

                        elif isbase64(inc_data):
                            try:
                                inc_data = b64decode(inc_data).decode()
                                if isinstance(inc_data, bytes):
                                    inc_data = inc_data.decode()
                            except Exception as e:
                                pass

                        if isinstance(inc_data, bytes):
                            inc_data = inc_data.decode()

                        data_formatted = inc_data.replace("\r\n", f"\r\n{'':<46}")
                        print(f"{t} :: [{inc['node']['id']}]:[{inc['node']['ip']}:{inc['node']['port']}] :: {R}{data_formatted}{END}")

        #return 0


    #
    #
    #
    def check_http_request(self, data: str) -> Union[str, None]:
        http_request_methods=["GET","POST"]
        return regex_search("^("+'|'.join(http_request_methods)+"){1}\s{1}/[a-zA-Z0-9 -.]*\s{1}HTTP/1.1", data)


    #
    # disconnect both node sockets
    #
    def dc_node(self, ip: str, q: Queue, c: _Const) -> None:

        inc_type_port, out_type_port = (0, 0)
        operation_success=False

        try:
            temp = ip_address(ip)
        except ValueError as e:
            print(f"[!] invalid ip address: {e.args[::-1]}")
            return

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
            print(f">>> sockets closed successfuly for ip [{ip}]")
        else:
            print(f">>> error! sockets not closed for ip [{ip}]")

    #
    # close socket | remove from lists | re-send new list to stream_in thread
    # ssi => stream-select-inputs list
    #
    def close_socket(self, s: socket.socket, ssi: list, q: Queue, c: _Const) -> None:
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
                t = strftime(c.TIME_FORMAT, localtime())
                socket_direction_type = ">>>" if self._tcp_connections[node]['type'] == "OUT" else "<<<"

                out = f"disconnected {'':<2}{socket_direction_type} {self._tcp_connections[node]['ip']}:{self._tcp_connections[node]['port']}"
                write_log(out, c)
                print(f"{t} :: {out}")

                if self._tcp_connections[node] in self._tcp_connections:
                    del self._tcp_connections[node]
                    break
                    
                print("[!] node was not in list!")
                break

        q.put_nowait(self._tcp_connections)


    #
    # close master socket & clear connections list
    #
    def close_master_socket(self, q: Queue) -> None:
        t = strftime("%Y-%m-%d %I:%M:%S %p", localtime())
        self.loop_close_all_sockets(q=q)
        self._socket["socket"].shutdown(socket.SHUT_RDWR)
        self._socket["socket"].close()
        print("disconnected all clients..\nmaster socket closed!")


    #
    #
    #
    def loop_close_all_sockets(self, q: Queue) -> None:
        inc_type_port, out_type_port = (0, 0)
        while len(self._tcp_connections) > 0:
            # always grab 1st element of the list sequentially
            tcp_conn = self._tcp_connections.pop(0)
            ip = tcp_conn["ip"]
            operation_success=False
            # close "OUT" socket
            for node in range(len(self._tcp_connections)):
                if self._tcp_connections[node]["ip"] == ip:
                    if self._tcp_connections[node]["type"] == "OUT":
                        out_type_port = int(self._tcp_connections[node]["port"])
                    if self._tcp_connections[node]["ip"] == ip \
                    and (out_type_port > 0 and self._tcp_connections[node]["port"] == out_type_port) \
                    and self._tcp_connections[node]["type"] == "OUT":
                        try:
                            self._tcp_connections[node]["socket"].shutdown(socket.SHUT_RDWR)
                        except socket.error as e:
                            pass
                        self._tcp_connections[node]["socket"].close()
                        del self._tcp_connections[node]
                        break
            # close "INC" socket
            for node in range(len(self._tcp_connections)):
                if self._tcp_connections[node]["ip"] == ip:
                    # get "INC" socket port
                    if self._tcp_connections[node]["type"] == "INC":
                        inc_type_port = int(self._tcp_connections[node]["port"])
                    if self._tcp_connections[node]["ip"] == ip \
                    and (inc_type_port > 0 and self._tcp_connections[node]["port"] == inc_type_port) \
                    and self._tcp_connections[node]["type"] == "INC":
                        try:
                            self._tcp_connections[node]["socket"].shutdown(socket.SHUT_RDWR)
                        except socket.error as e:
                            pass
                        self._tcp_connections[node]["socket"].close()
                        del self._tcp_connections[node]
                        operation_success=True
                        break

            if operation_success:
                print(f">>> sockets closed successfuly for ip [{ip}]")
                sleep(0.5)
            else:
                print(f">>> error! sockets not closed for ip [{ip}]")
                
            q.put_nowait(self._tcp_connections)


    #
    # get connected clients
    #
    def conninfo(self) -> None:
        for node in range(len(self._tcp_connections)):
            print(f"{node} - {self._tcp_connections[node]['id']} - {self._tcp_connections[node]['type']} - {self._tcp_connections[node]['ip']}:{self._tcp_connections[node]['port']}")


    #
    # send msg to single node
    #
    def send_to_node(self, ip: str, port: int, msg: bytes, c: _Const, q: Queue) -> int:
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
            print(f"error on socket.send(): {e.args[::-1]}")
            self.dc_node(ip=ip, q=q, c=c)
            return 1
        return 0


    #
    #
    #
    def broadcast_msg(self, msg: bytes, c: _Const, q: Queue) -> int:

        out = f"broadcasting >>> {msg}"

        for node in range(len(self._tcp_connections)):
            if self._tcp_connections[node]["socket"] == self._socket["socket"]: # not sending to self
                continue
            try:
                write_log(out, c)
                #
                # TODO: http response
                #       curl does not accept bytes => 'HTTP/0.9 error'
                #       use plain string
                #
                self._tcp_connections[node]["socket"].send(msg)
            except socket.error as e:
                print(f"socket error on socket.send(): {e.args[::-1]}")
                self.dc_node(ip=self._tcp_connections[node]["ip"], q=q, c=c)
                return 1
            except Exception as e:
                print(f"error on soocket.send(): {e.args[::-1]}")
                self.dc_node(ip=self._tcp_connections[node]["ip"], q=q, c=c)
                return 1
        return 0


    #
    #
    #
    def cmd_to_node(self, ip: str, port: int, cmd: bytes, c: _Const, q: Queue) -> int:
        target = {
            "node": self._tcp_connections[node] \
                    for node in range(len(self._tcp_connections)) \
                    if self._tcp_connections[node]["ip"] == ip and self._tcp_connections[node]["port"] == port
        }
        if not target:
            print(f"target {ip}:{port} doesn't exist")
            return 1
        # send flag that packets are command
        print(f">>> sending command [{cmd.decode()}] to node [{ip}:{port}]")
        try:
            cmd64 = "inccmd:".encode() + b64encode(cmd)
            target["node"]["socket"].send(cmd64)
        except socket.error as e:
            print(f"socket error on cmd socket.send(): {e.args[::-1]}")
            self.dc_node(ip=ip, q=q, c=c)
            return 1
        except Exception as e:
            print(f"error on cmd socket.send(): {e.args[::-1]}")
            self.dc_node(ip=ip, q=q, c=c)
            return 1
        return 0 


    #
    #
    #
    def conn_from_list(self, q: Queue, c: _Const) -> None:
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
                    self.connect_to_node(ip=ip, port=port, q=q, c=c)
                    sleep(0.5)

        except Exception as e:
            print(f"error on file.read() in conn_from_list(): {e.args[::-1]}")
    