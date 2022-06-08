from moudle import BaseMoudle
from interpreter import Interpreter


class Cpu:
    def __init__(self, command_per_turn: int):
        self.cpt = command_per_turn
        self.bus = Bus()
        self.interpreter = None

    def boot(self, codestr: str):
        codes = codestr.split('\n')
        mod_cmds = {mod.command: mod.run for mod in self.bus.modules.values()}
        self.interpreter = Interpreter(codes, mod_cmds)

    def run(self):
        return self.interpreter.run(self.cpt)


class Bus:
    def __init__(self):
        self.modules = {}

    def install(self, moudle: BaseMoudle):
        if moudle.command in self.modules.keys():
            raise RuntimeError('Moudle Access Conflict: ' + moudle.command)
        self.modules[moudle.command] = moudle

    def uninstall(self, moudle: BaseMoudle):
        if moudle.command in self.modules.keys():
            del self.modules[moudle.command]
        raise RuntimeError('Moudle Access Not Existent: ' + moudle.command)
