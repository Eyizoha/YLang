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
