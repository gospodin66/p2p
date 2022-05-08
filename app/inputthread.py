import threading
import time
import sys

class InputThread(threading.Thread):

    # input_callback  => function to exec in thread loop
    # args (any type) => additional arguments to function
    # name (string)   => thread name
    def __init__(self, input_callback = None, args = None, name='input-thread'):
        self.input_callback = input_callback
        self.args = args
        self.eof_flag = False
        super(InputThread, self).__init__(name=name)
        self.start()


    #
    # waits to get input() => returns 1/0 (exit/continue)
    #
    def run(self):
        while 1:
            try:
                inp = input()
                if inp:
                    if self.input_callback(inp, self.args) == 1:
                        break
            except ValueError as e:
                print(f"input-thread error: attempt to send on broken connection: {e.args[::-1]}")
                break
            except EOFError as e:
                print(f"input-thread error: EOF: {e.args[::-1]}")
                #
                # temp workaround for piping into script
                # => opens input as FIFO instead tty
                # => echo -n "connnode:172.17.0.7:45666" | /p2p/node.py `hostname -I` 45666
                #
                if not sys.stdin.isatty():
                    print("setting sys.stdin as tty..")
                    sys.stdin = open("/dev/tty")
                continue
            except Exception as e:
                print(f"input-thread error: unexpected error on input(): {e.args[::-1]}")
                break
        print("\ninput-thread exited")
        return
        