import node
import node_fnc
import queue
import ipaddress

# global callback for input-thread (broadcast/exec messages/commands)
# inp  => input string | bytes
# args => additional args to fnc
def input_callback(inp, args) -> int:

    # close node from input thread
    def exit_from_cmd(n: node.Node) -> int:
        n.close_master_socket()
        n._EXIT_ON_CMD = True
        return 1

    n, c, q = (args["_node"], args["_const"], args["_queue"])

    if not isinstance(n, node.Node) or not isinstance(c, node_fnc._Const) or not isinstance(q, queue.Queue):
        print("input-callback: invalid class instances.. exiting input thread..")
        return 1
    
    # update input-thread tcp connections list
    if not q.empty():
        new_list = q.get_nowait()
        n.set_connections(new_list)
        q.task_done()

    if not inp or inp == "":
        print("--- empty input..")
        return 0

    if inp[:9] == "sendfile:":
        print("sending file..")
        out = node_fnc.r_file(inp.split(":")[1])

    elif inp == "getopts:":
        node_fnc.display_options()
        return 0

    elif inp == "listconn:":
        n.conn_from_list(q=q, c=c)
        return 0

    elif inp == "conninfo:":
        n.conninfo()
        return 0

    elif inp[:9] == "connnode:":
        if inp[9:].find(':') == -1:
            print(f"[!] invalid ip/port: {inp[9:]}")
            return 0

        addr = inp[9:len(inp)].split(":")
        if node_fnc.validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 0
        n.connect_to_node(ip=str(addr[0]), port=int(addr[1]), c=c)
        return 0

    elif inp[:7] == "dcnode:":
        addr = inp[7:len(inp)]
        try:
            temp = ipaddress.ip_address(inp[7:])
        except ValueError as e:
            print(f"[!] invalid ip address format: {inp[7:]} | {e.args[::-1]}")
            return 0
        # 1 as dummy port argument => disconnects by ip
        if node_fnc.validate_ip_port(str(addr), 1) != 0:
            return 0
        n.dc_node(ip=str(addr), q=q, c=c)
        return 0

    elif inp[:11] == "sendtonode:":
        addr = inp[11:inp.index("|", 11, len(inp))].split(":")
        msg = inp[inp.index("|", 11, len(inp)):].lstrip("|")
        if node_fnc.validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 0
        n.send_to_node(ip=str(addr[0]), port=int(addr[1]), msg=msg.encode(), c=c, q=q)
        return 0

    elif inp[:10] == "cmdtonode:":
        addr = inp[10:inp.index("|", 10, len(inp))].split(":")
        cmd = inp[inp.index("|", 10, len(inp)):].lstrip("|")
        if node_fnc.validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 0
        n.cmd_to_node(ip=str(addr[0]), port=int(addr[1]), cmd=cmd.encode(), c=c, q=q)
        return 0

    elif inp[:6] == "bccmd:":
        print(f">>> broadcasting command [{inp[6:]}]")
        cmd = str("inccmd:" + inp[6:]).encode()
        n.broadcast_msg(msg=cmd, c=c, q=q)
        return 0

    elif inp == "exit:":
        return exit_from_cmd(n)

    else:
        # default
        out = inp.encode()

    n.broadcast_msg(msg=out, c=c, q=q)
    
    q.queue.clear()

    return 0
