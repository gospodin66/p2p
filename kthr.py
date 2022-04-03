import threading

class KThr(threading.Thread):
    # input_callback  => function to exec in thread loop
    # args (any type) => additional arguments to function
    # name (string)   => thread name
    def __init__(self,input_callback = None,args = None,name='input-thread'):
        self.input_callback = input_callback
        self.args = args
        super(KThr, self).__init__(name=name)
        self.start()

    def run(self):
        while True:
            # waits to get input() => returns 1/0 (exit/continue)
            try:
                if self.input_callback(input(), self.args) == 1:
                    break
            except ValueError as e:
                print(f"error! attempt to send on broken connection: {e.args[::-1]}")
                break
            except Exception as e:
                print(f"unexpected error on input(): {e.args[::-1]}")
                break
        print("input-thread exited")
        return
        