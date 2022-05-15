import node
import node_fnc
import queue

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

    if not inp:
        print("--- empty input..")
        return 1

    if inp[:9] == "sendfile:":
        print("sending file..")
        out = node_fnc.r_file(inp.split(":")[1])
        # TODO: send & recv file as function

    elif inp == "getopts:":
        node_fnc.display_options()
        return 0

    elif inp == "conninfo:":
        n.conninfo()
        return 0

    elif inp[:9] == "connnode:":
        addr = inp[9:len(inp)].split(":")
        if node_fnc.validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 1
        n.connect_to_node(ip=str(addr[0]), port=int(addr[1]))
        return 0

    elif inp[:7] == "dcnode:":
        addr = inp[7:len(inp)].split(":")
        if node_fnc.validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 1
        n.dc_node(ip=str(addr[0]), port=int(addr[1]), q=q, c=c)
        return 0

    elif inp[:11] == "sendtonode:":
        addr = inp[11:inp.index("|", 11, len(inp))].split(":")
        msg = inp[inp.index("|", 11, len(inp)):].lstrip("|")
        if node_fnc.validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 1
        n.send_to_node(ip=str(addr[0]), port=int(addr[1]), msg=msg.encode(), c=c)
        return 0

    elif inp[:10] == "cmdtonode:":
        addr = inp[10:inp.index("|", 10, len(inp))].split(":")
        cmd = inp[inp.index("|", 10, len(inp)):].lstrip("|")
        if node_fnc.validate_ip_port(str(addr[0]), int(addr[1])) != 0:
            return 1
        n.cmd_to_node(ip=str(addr[0]), port=int(addr[1]), cmd=cmd.encode(), c=c)
        return 0

    elif inp[:6] == "bccmd:":
        print(f">>> broadcasting command [{inp[6:]}]")
        cmd = str("inccmd:" + inp[6:]).encode()
        n.broadcast_msg(msg=cmd, q=q, c=c)
        return 0

    elif inp == "exit:":
        return exit_from_cmd(n)

    else:
        # default
        out = inp.encode()

    n.broadcast_msg(msg=out, q=q, c=c)

    return 0
