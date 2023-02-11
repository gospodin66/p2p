from node_fnc import _Const, r_file, validate_ip_port, display_options
from queue import Queue
from node import Node
from base64 import b64encode

# global callback for input-thread (broadcast/exec messages/commands)
# inp  => input string | bytes
# args => additional args to fnc
def input_callback(inp, args) -> int:

    # close node from input thread
    def exit_from_cmd(n: Node) -> int:
        n.close_master_socket()
        n._EXIT_ON_CMD = True
        return 1

    n, c, q = (args["_node"], args["_const"], args["_queue"])

    if not isinstance(n, Node) or not isinstance(c, _Const) or not isinstance(q, Queue):
        print("input-callback: invalid class instances.. exiting input thread..")
        return 1
    
    # update input-thread tcp connections list
    if not q.empty():
        new_list = q.get_nowait()
        n.set_connections_from_thread(new_list)
        q.task_done()
        print(f"received in queue -- size {q.qsize()}")


    if not inp or inp == "":
        print("--- empty input..")
        return 0

    # -------------------------------------------------------------------
    # | CMD_PREFIX |             DESCRIPTION             |  ARGS        |
    # -------------------------------------------------------------------
    # | b          | (broadcast cmd)                     |  cmd         |
    # | f          | (file(send))                        |  file_path   |
    # | c          | (connect)                           |  ip:port     |
    # | dc         | (disconnect)                        |  ip          |
    # | cmd        | (cmd to node)                       |  ip:port|cmd |
    # | s          | (send to single node)               |  ip:port|msg |
    # | cs         | (connections)                       |              |
    # | opts       | (list options)                      |              |
    # | listconn   | (connect to ips from provided list) |              |
    # | exit       | (self-expl.)                        |              |
    # -------------------------------------------------------------------

    if inp[:2] == "b:":
        print(f">>> broadcasting command [{inp[2:]}]")
        out = "inccmd:".encode() + b64encode(str(inp[2:]).encode())

    elif inp[:2] == "f:":
        print("sending file..")
        out = r_file(inp.split(":")[1])

    elif inp[:2] == "c:":
        if inp[2:].find(':') == -1:
            print(f"[!] invalid ip/port: {inp[2:]}")
            return 0

        addr = inp[2:len(inp)].split(":")

        if validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 0

        n.connect_to_node(ip=str(addr[0]), port=int(addr[1]), c=c)
        q.queue.clear()
        # print(f"cleared queue -- size: {q.qsize()}")
        return 0

    elif inp[:3] == "dc:":
        addr = inp[3:len(inp)]
        # 1 as dummy port argument => disconnects by ip
        if validate_ip_port(str(addr), 1) != 0:
            return 0
        n.dc_node(ip=str(addr), q=q, c=c)
        q.queue.clear()
        print(f"cleared queue -- size: {q.qsize()}")
        return 0

    elif inp[:2] == "s:":
        addr = inp[2:inp.index("|", 2, len(inp))].split(":")
        msg = inp[inp.index("|", 2, len(inp)):].lstrip("|")
        if validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 0
        n.send_to_node(ip=str(addr[0]), port=int(addr[1]), msg=msg.encode(), c=c, q=q)
        q.queue.clear()
        # print(f"cleared queue -- size: {q.qsize()}")
        return 0

    elif inp[:4] == "cmd:":
        addr = inp[4:inp.index("|", 4, len(inp))].split(":")
        cmd = inp[inp.index("|", 4, len(inp)):].lstrip("|")
        if validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 0
        n.cmd_to_node(ip=str(addr[0]), port=int(addr[1]), cmd=cmd.encode(), c=c, q=q)
        q.queue.clear()
        # print(f"cleared queue -- size: {q.qsize()}")
        return 0

    elif inp == "opts:":
        display_options()
        return 0

    elif inp == "listconn:":
        n.conn_from_list(q=q, c=c)
        q.queue.clear()
        # print(f"cleared queue -- size: {q.qsize()}")
        return 0

    elif inp == "cs:":
        n.conninfo()
        return 0

    elif inp == "exit:":
        return exit_from_cmd(n)

    # default
    else:
        out = inp.encode()

    n.broadcast_msg(msg=out, c=c, q=q)
    q.queue.clear()
    # print(f"cleared queue -- size: {q.qsize()}")

    return 0
