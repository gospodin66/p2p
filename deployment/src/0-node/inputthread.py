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
                        print("exiting normally")
                        break
            except ValueError as e:
                print(f"input-thread error: attempt to send on broken connection: {e.args[::-1]}")
                break
            except Exception as e:
                print(f"input-thread error: unexpected error on input(): {e.args[::-1]}")
                break
            except EOFError as e:
                pass
        print("\ninput-thread exited")
        return
        