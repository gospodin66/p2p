import socket
import base64
import logging
from dataclasses import dataclass

@dataclass(frozen=True)
class _Const:
    BUFFER_SIZE = 4096
    MAX_CONNECTIONS = 100
    TIME_FORMAT = "%Y-%m-%d %I:%M:%S %p"
    LOG_FORMAT = '%(asctime)s --- %(message)s'
    LOG_FILE_PATH = './0-node-log.txt'


def isbase64(s: str) -> bool:
    try:
        res = base64.b64decode(s)
        return True
    except Exception:
        return False
    return False


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


def display_options() -> None:
    print("""\
-------------------------------------------------------------------
| CMD_PREFIX |             DESCRIPTION             |  ARGS        |
-------------------------------------------------------------------
| b          | (broadcast cmd)                     |  cmd         |
| f          | (file(send))                        |  file_path   |
| c          | (connect)                           |  ip:port     |
| dc         | (disconnect)                        |  ip          |
| cmd        | (cmd to node)                       |  ip:port|cmd |
| s          | (send to single node)               |  ip:port|msg |
| cs         | (connections)                       |              |
| opts       | (list options)                      |              |
| listconn   | (connect to ips from provided list) |              |
| reset      | (disconnect all nodes, re-scan net) |              |
| close      | (disconnect all nodes)              |              |
| renew      | (re-scan net)                       |              |
| exit       | (self-expl.)                        |              |
-------------------------------------------------------------------""")





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


def write_log(msg: str, c: _Const) -> None:
    logging.basicConfig(format=c.LOG_FORMAT, filename=c.LOG_FILE_PATH, filemode='a', level=logging.INFO)
    logger = logging.getLogger('node')
    logger.info('%s', msg)
    # logger.warning('Protocol problem: %s', msg, extra=d)