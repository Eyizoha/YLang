class MoudleError(Exception):
    """ 外部模块异常 """
    pass


class BaseMoudle:
    def __init__(self, command: str, level=1):
        self.command = command
        self.level = level

    def run(self, args: list):
        pass


class Inputer(BaseMoudle):
    def __init__(self):
        BaseMoudle.__init__(self, 'in')

    def run(self, args: list):
        if len(args) > 0:
            raise MoudleError('IN takes no argument but {} were given'.format(len(args)))
        ret = input()
        try:
            return int(ret)
        except ValueError:
            try:
                return float(ret)
            except ValueError:
                raise MoudleError(ret + ' is not a number')


class Outputer(BaseMoudle):
    def __init__(self):
        BaseMoudle.__init__(self, 'out')

    def run(self, args: list):
        print(*args)


class InStream(BaseMoudle):
    def __init__(self):
        BaseMoudle.__init__(self, 'ins')
        self.object = None

    def run(self, args: list):
        return self.object

    def set(self, obj):
        self.object = obj


class OutStream(BaseMoudle):
    def __init__(self):
        BaseMoudle.__init__(self, 'outs')
        self.object = None

    def run(self, args: list):
        self.object = args

    def get(self):
        return self.object


class RandomInt(BaseMoudle):
    def __init__(self):
        BaseMoudle.__init__(self, 'randint')
        from random import randint
        self.op = randint

    def run(self, args: list):
        if len(args) != 2:
            raise MoudleError('randint takes 2 arguments but {} were given'.format(len(args)))
        try:
            return self.op(*args)
        except Exception as e:
            raise MoudleError(str(e))
