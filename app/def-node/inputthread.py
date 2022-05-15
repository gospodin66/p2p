import threading
import sys

class InputThread(threading.Thread):

    def __init__(self, thread_name = 'input-thread', input_callback = None, **kwargs):
        self.input_callback = input_callback
        self.args = kwargs
        self.eof_flag = False
        # declare that InputThread class inherits from threading.Thread class
        # super(param1 >>> {subclass}, param2 >>> {object that is an instance of subclass})
        super(InputThread, self).__init__(name=thread_name)
        self.start()


    #
    # waits to get input() => returns 1/0 (exit/continue)
    #
    def run(self):
        while 1:
            try:
                inp = input()
                if inp:
                    if self.input_callback(inp=inp, args=self.args) == 1:
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
        