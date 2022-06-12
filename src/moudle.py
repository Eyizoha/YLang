from threading import Thread
from interpreter import Interpreter
from time import sleep



class MoudleError(Exception):
    """ 外部模块异常 """


class BaseMoudle:
    def __init__(self, command: str, level=1):
        self.command = command
        self.level = level
        self.api = None

    def run(self, thread: Interpreter, args: list):
        pass

    def set_api(self, api):
        self.api = api


class Inputer(BaseMoudle):
    def __init__(self):
        BaseMoudle.__init__(self, 'in')
        self.ret = {}
        self.threads = {}

    def run(self, thread: Interpreter, args: list):
        if len(args) > 0:
            raise MoudleError('IN takes no argument but {} were given'.format(len(args)))
        tid = thread.tid
        if tid not in self.ret.keys():
            self.ret[tid] = None
            t = Thread(target=self._input_thread, args=(tid,))
            self.threads[tid] = t
            t.start()

        ret = self.ret[tid]
        if ret is None:
            self.api['block_thread'](tid)
            thread.pointer -= 1
            return

        del self.ret[tid]
        del self.threads[tid]

        # TODO: Support Str input
        try:
            return int(ret)
        except ValueError:
            try:
                return float(ret)
            except ValueError:
                raise MoudleError(ret + ' is not a number')

    def _input_thread(self, tid):
        ret = ''
        while not ret:
            ret = input()
        self.ret[tid] = ret
        self.api['activate_thread'](tid)


class Outputer(BaseMoudle):
    def __init__(self):
        BaseMoudle.__init__(self, 'out')

    def run(self, thread: Interpreter, args: list):
        print(*args)


class Sleeper(BaseMoudle):
    def __init__(self):
        BaseMoudle.__init__(self, 'sleep')
        self.threads = {}

    def run(self, thread: Interpreter, args: list):
        if len(args) != 1:
            raise MoudleError('SLEEP takes 1 argument but {} were given'.format(len(args)))
        secs = args[0]
        if not (isinstance(secs, int) or isinstance(secs, float)):
            raise MoudleError(str(secs) + ' is not a number')
        if secs < 0:
            raise MoudleError(str(secs) + ' is negative')

        tid = thread.tid
        if tid not in self.threads.keys():
            self.api['block_thread'](tid)
            thread.pointer -= 1
            t = Thread(target=self._sleep_thread, args=(tid, secs))
            self.threads[tid] = t
            t.start()
            return

        del self.threads[tid]

    def _sleep_thread(self, tid, secs):
        sleep(secs)
        self.api['activate_thread'](tid)
