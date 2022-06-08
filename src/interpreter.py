class InterpreterError(Exception):
    """ 解释器内部异常 """
    pass


class Interpreter:
    """ Y语言解释器 """

    def __init__(self, codes: list, mod_cmds: dict):
        self.codes = codes  # Y语言代码，字符串列表

        self.ans = 0  # 特殊变量@
        self.call_stack = []  # 解释器栈
        self.global_vars = {}  # 全局变量
        self.local_vars = {}  # 局部变量
        self.pointer = 0  # 代码指针

        self.prime_commands = {name[4:]: self.__getattribute__(name) for name in self.__dir__()
                               if name.startswith('cmd_')}  # Y语言原生指令集
        self.module_commands = mod_cmds  # 模块指令集

    def run(self, cpt: int):
        """ 执行cpt条指令，顺利执行完毕返回True，已无指令可执行或执行出错返回False """
        count = 0
        while count < cpt:
            if self.pointer >= len(self.codes) or self.pointer < 0:
                return False
            code = self.codes[self.pointer].strip()
            try:
                count += self.exec(code)
            except InterpreterError as e:
                print('(line {}: {})Cpu Error: '.format(self.pointer, code) + str(e))
                return False
            self.pointer += 1
        return True

    def exec(self, code: str):
        """ 执行一条指令，执行成功返回1，否则返回0"""
        cmd, *args = code.split(' ')
        cmd = cmd.lower()
        if not cmd or cmd.startswith('//'):
            return 0
        try:
            self.prime_commands[cmd](args)
        except KeyError:
            try:
                val = self.module_commands[cmd]([self.get_value(arg) for arg in args])
                if val is not None:
                    self.set_value('@', val)
            except KeyError:
                raise InterpreterError('Unknow command ' + cmd)
        return 1

    def get_matched_end(self, ptr: int, start: str, end: str, step=1):
        """ 获取ptr行strat匹配的end所在行 """
        count = 1
        ptr += step
        while 0 <= ptr < len(self.codes):
            code = self.codes[ptr].upper().strip()
            if code.startswith(start):
                count += 1
            elif code.startswith(end):
                count -= 1
            if count == 0:
                return ptr
            ptr += step
        raise InterpreterError(end + ' not found')

    def get_matched_else_eif(self, ptr: int, elsed=False):
        """ 获取ptr行if或else匹配的else或eif所在行 """
        count = 1
        ptr += 1
        while ptr < len(self.codes):
            code = self.codes[ptr].upper().strip()
            if code.startswith('IF'):
                count += 1
            elif count == 1 and code.startswith('ELSE'):
                if elsed:
                    self.pointer = ptr
                    raise InterpreterError('ELSE is mismatched')
                return ptr
            elif code.startswith('EIF'):
                count -= 1
            if count == 0:
                return ptr
            ptr += 1
        raise InterpreterError('EIF not found')

    def get_array_index(self, var: str):
        """ 将var拆分为列表名和索引 """
        left = self.left_bracket_index(var)
        # TODO: support slice
        index = self.get_value(var[left + 1: -1])
        var = self.get_value(var[: left])
        if not isinstance(index, int):
            raise InterpreterError(str(index) + ' is not a int')
        if not isinstance(var, list):
            raise InterpreterError(str(var) + ' is not a list')
        return var, index

    def get_operands(self, args: list):
        """ 获取操作数 """
        oper1 = self.get_value(args[0])
        oper2 = self.get_value(args[1])
        if not (isinstance(oper1, int) or isinstance(oper1, float)):
            raise InterpreterError(str(oper1) + ' is not a number')
        if not (isinstance(oper2, int) or isinstance(oper2, float)):
            raise InterpreterError(str(oper2) + ' is not a number')
        return oper1, oper2

    @staticmethod
    def left_bracket_index(var: str):
        """ var为末尾为]的表达式，返回和末尾]匹配的[ """
        left = len(var) - 2
        count = 1
        while left != -1:
            if var[left] == '[':
                count -= 1
            elif var[left] == ']':
                count += 1
            if count == 0:
                break
            left -= 1
        else:
            raise InterpreterError(var + ' missing [')
        return left

    @staticmethod
    def parse_list(lst: str):
        """ 分析列表字符串，返回元素列表 """
        items = []
        count = 0
        tmp = ''
        for c in lst[1:-1]:
            if c == '[':
                count += 1
            elif c == ']':
                count -= 1
            elif count == 0 and c == ',':
                items.append(tmp)
                tmp = ''
                continue
            tmp += c
        if tmp:
            items.append(tmp)
        return items

    @staticmethod
    def return_number(var: str):
        """ var为数字字符串，返回var表示的数字 """
        try:
            return int(var)
        except ValueError:
            try:
                return float(var)
            except ValueError:
                raise InterpreterError(var + ' is not a number or identifier')

    def return_var(self, var: str):
        """ var为变量名，返回var的值，优先返回局部变量 """
        try:
            return self.local_vars[var]
        except KeyError:
            try:
                return self.global_vars[var]
            except KeyError:
                raise InterpreterError(var + ' is not defined')

    def get_value(self, var: str):
        """ var为变量名、立即数或者数组嵌套表达式字符串，获取数组嵌套表达式的值或者变量的值或者立即数本身 """
        if not var:
            raise InterpreterError('invalid syntax')
        if var.endswith(']'):
            if var.startswith('['):
                return [self.get_value(item) for item in self.parse_list(var)]
            if var.endswith('[]'):
                item = self.get_value(var[:-2])
                if isinstance(item, list):
                    return len(item)
                else:
                    return -1
            var, index = self.get_array_index(var)
            try:
                return var[index]
            except IndexError:
                raise InterpreterError(str(index) + ' out of range')
        if var == '@':
            return self.ans
        if var.isidentifier():
            return self.return_var(var)
        return self.return_number(var)

    def set_value(self, var: str, val, global_var=False):
        """ var为变量名或者数组嵌套表达式字符串，设置数组嵌套表达式的值或者变量的值为val """
        if var.endswith(']'):
            if var.startswith('['):
                raise InterpreterError(var + ' is not a variable')
            if var.endswith('[]'):
                raise InterpreterError(var + ' is not a variable')
            var, index = self.get_array_index(var)
            try:
                var[index] = val
            except IndexError:
                raise InterpreterError(str(index) + ' out of range')
            return
        if var == '@':
            self.ans = val
            return
        if var.isidentifier():
            if global_var:
                self.global_vars[var] = val
            else:
                self.local_vars[var] = val
            return
        raise InterpreterError(var + ' is not a variable')

    def cmp_expr(self, args: list):
        """ 计算比较表达式 """
        oper1 = self.get_value(args[0])
        op = args[1]
        oper2 = self.get_value(args[2])
        if op not in {'==', '!=', '<', '<=', '>', '>='}:
            raise InterpreterError(op + ' is not a cmp operator')
        if not (isinstance(oper1, int) or isinstance(oper1, float)):
            raise InterpreterError(str(oper1) + ' is not a number')
        if not (isinstance(oper2, int) or isinstance(oper2, float)):
            raise InterpreterError(str(oper2) + ' is not a number')
        return eval('oper1 {} oper2'.format(op))

    def cmd_at(self, args: list):
        if len(args) != 1:
            raise InterpreterError('AT takes 1 argument but {} were given'.format(len(args)))
        self.set_value(args[0], self.pointer)

    def cmd_go(self, args: list):
        if len(args) != 1:
            raise InterpreterError('GO takes 1 argument but {} were given'.format(len(args)))
        ptr = self.get_value(args[0])
        if not isinstance(ptr, int):
            raise InterpreterError(str(ptr) + ' is not a int')
        self.pointer = ptr

    def cmd_mov(self, args: list):
        if not 1 <= len(args) <= 2:
            raise InterpreterError('MOV takes 1 or 2 argument(s) but {} were given'.format(len(args)))
        self.set_value(args[0], self.get_value(args[1] if len(args) == 2 else '@'))

    def cmd_glb(self, args: list):
        if not 1 <= len(args) <= 2:
            raise InterpreterError('GLB takes 1 or 2 argument(s) but {} were given'.format(len(args)))
        self.set_value(args[0], self.get_value(args[1] if len(args) == 2 else '@'), global_var=True)

    def cmd_if(self, args: list):
        if len(args) != 1 and len(args) != 3:
            raise InterpreterError('IF takes 1 or 3 argument(s) but {} were given'.format(len(args)))
        if (len(args) == 1 and self.get_value(args[0]) == 0) \
                or (len(args) == 3 and not self.cmp_expr(args)):
            self.pointer = self.get_matched_else_eif(self.pointer)

    def cmd_else(self, args: list):
        if len(args) != 0:
            raise InterpreterError('ELSE takes no argument but {} were given'.format(len(args)))
        self.pointer = self.get_matched_else_eif(self.pointer, elsed=True)

    @staticmethod
    def cmd_eif(args: list):
        if len(args) != 0:
            raise InterpreterError('EIF takes no argument but {} were given'.format(len(args)))

    def cmd_def(self, args: list):
        if len(args) < 1:
            raise InterpreterError('DEF takes at least 1 argument but {} were given'.format(len(args)))
        self.set_value(args[0], self.pointer, global_var=False if self.call_stack else True)
        self.pointer = self.get_matched_end(self.pointer, 'DEF', 'EDEF')

    def cmd_edef(self, args: list):
        if len(args) != 0:
            raise InterpreterError('EDEF takes no argument but {} were given'.format(len(args)))
        if not self.call_stack:
            raise InterpreterError('EDEF is mismatched')
        self.pointer, self.local_vars = self.call_stack.pop()

    def cmd_ret(self, args: list):
        if len(args) > 1:
            raise InterpreterError('RET takes 0 or 1 argument but {} were given'.format(len(args)))
        if not self.call_stack:
            raise InterpreterError('RET outside function')
        if len(args) == 1:
            self.set_value('@', self.get_value(args[0]))
        self.pointer, self.local_vars = self.call_stack.pop()

    def cmd_call(self, args: list):
        if len(args) < 1:
            raise InterpreterError('CALL takes at least 1 argument but {} were given'.format(len(args)))
        ptr = self.get_value(args[0])
        if not isinstance(ptr, int):
            raise InterpreterError(args[0] + ' is not a function')
        cmd, *fun_args = self.codes[ptr].strip().split(' ')
        if cmd.lower() != 'def':
            raise InterpreterError(args[0] + ' is not a function')
        if len(args) != len(fun_args):
            raise InterpreterError(
                fun_args[0] + ' takes {} argument(s) but {} were given'.format(len(fun_args) - 1, len(args) - 1))
        for arg in fun_args:
            if not arg.isidentifier():
                raise InterpreterError(arg + ' is not a variable')
        self.call_stack.append((self.pointer, self.local_vars))
        self.local_vars = {var: self.get_value(args[i]) for i, var in enumerate(fun_args)}
        self.pointer = ptr

    def cmd_loop(self, args: list):
        if len(args) != 1 and len(args) != 3:
            raise InterpreterError('LOOP takes 1 or 3 argument(s) but {} were given'.format(len(args)))
        if (len(args) == 1 and self.get_value(args[0]) == 0) \
                or (len(args) == 3 and not self.cmp_expr(args)):
            self.pointer = self.get_matched_end(self.pointer, 'LOOP', 'ELOP')

    def cmd_elop(self, args: list):
        if len(args) != 0:
            raise InterpreterError('ELOP takes no argument but {} were given'.format(len(args)))
        self.pointer = self.get_matched_end(self.pointer, 'ELOP', 'LOOP', -1) - 1

    def cmd_brk(self, args: list):
        if len(args) > 1 and len(args) != 3:
            raise InterpreterError('BRK takes 0 or 1 or 3 argument(s) but {} were given'.format(len(args)))
        if (len(args) == 0) or \
                (len(args) == 1 and self.get_value(args[0]) != 0) or \
                (len(args) == 3 and self.cmp_expr(args)):
            self.pointer = self.get_matched_end(self.pointer, 'LOOP', 'ELOP')

    def cmd_ctn(self, args: list):
        if len(args) > 1 and len(args) != 3:
            raise InterpreterError('CTN takes 0 or 1 or 3 argument(s) but {} were given'.format(len(args)))
        if (len(args) == 0) or \
                (len(args) == 1 and self.get_value(args[0]) != 0) or \
                (len(args) == 3 and self.cmp_expr(args)):
            self.pointer = self.get_matched_end(self.pointer, 'ELOP', 'LOOP', -1) - 1

    def cmd_cpy(self, args: list):
        if not 1 <= len(args) <= 2:
            raise InterpreterError('CPY takes 1 or 2 argument(s) but {} were given'.format(len(args)))
        lst = self.get_value(args[1] if len(args) == 2 else '@')
        if not isinstance(lst, list):
            raise InterpreterError((args[1] if len(args) == 2 else '@') + ' is not a list')
        self.set_value(args[0], lst.copy())

    def cmd_push(self, args: list):
        if not 1 <= len(args) <= 3:
            raise InterpreterError('PUSH takes 1 or 2 or 3 argument(s) but {} were given'.format(len(args)))
        lst = self.get_value(args[0])
        if not isinstance(lst, list):
            raise InterpreterError(args[0] + ' is not a list')
        if len(args) == 3:
            index = self.get_value(args[2])
            if not isinstance(index, int):
                raise InterpreterError(str(index) + ' is not a int')
            lst.insert(index, self.get_value(args[1]))
        else:
            lst.append(self.get_value(args[1] if len(args) == 2 else '@'))

    def cmd_pop(self, args: list):
        if not 1 <= len(args) <= 3:
            raise InterpreterError('POP takes 1 or 2 or 3 argument(s) but {} were given'.format(len(args)))
        lst = self.get_value(args[0])
        if not isinstance(lst, list):
            raise InterpreterError(args[0] + ' is not a list')
        if len(args) == 3:
            index = self.get_value(args[2])
            if not isinstance(index, int):
                raise InterpreterError(str(index) + ' is not a int')
            try:
                self.set_value(args[1] if len(args) == 2 else '@', lst.pop(index))
            except IndexError:
                raise InterpreterError('{} is out of list {} range'.format(index, args[0]))
        else:
            self.set_value(args[1] if len(args) == 2 else '@', lst.pop())

    def cmd_idx(self, args: list):
        if not 1 <= len(args) <= 2:
            raise InterpreterError('IDX takes 1 or 2 argument(s) but {} were given'.format(len(args)))
        lst = self.get_value(args[0])
        if not isinstance(lst, list):
            raise InterpreterError(args[0] + ' is not a list')
        try:
            idx = lst.index(self.get_value(args[1] if len(args) == 2 else '@'))
        except ValueError:
            idx = -1
        self.set_value('@', idx)

    def cmd_revs(self, args: list):
        if len(args) != 1:
            raise InterpreterError('REVS takes 1 argument but {} were given'.format(len(args)))
        lst = self.get_value(args[0])
        if not isinstance(lst, list):
            raise InterpreterError(args[0] + ' is not a list')
        lst.reverse()

    def cmd_sort(self, args: list):
        if len(args) != 1:
            raise InterpreterError('SORT takes 1 argument but {} were given'.format(len(args)))
        lst = self.get_value(args[0])
        if not isinstance(lst, list):
            raise InterpreterError(args[0] + ' is not a list')
        try:
            lst.sort()
        except TypeError:
            raise InterpreterError(args[0] + ' have non comparable items')

    def cmd_int(self, args: list):
        if len(args) != 1:
            raise InterpreterError('INT takes 1 argument but {} were given'.format(len(args)))
        oper = self.get_value(args[0])
        if not (isinstance(oper, int) or isinstance(oper, float)):
            raise InterpreterError(str(oper) + ' is not a number')
        self.set_value(args[0], int(oper))

    def cmd_inc(self, args: list):
        if len(args) != 1:
            raise InterpreterError('INC takes 1 argument but {} were given'.format(len(args)))
        oper = self.get_value(args[0])
        if not (isinstance(oper, int) or isinstance(oper, float)):
            raise InterpreterError(str(oper) + ' is not a number')
        self.set_value(args[0], oper + 1)

    def cmd_dec(self, args: list):
        if len(args) != 1:
            raise InterpreterError('DEC takes 1 argument but {} were given'.format(len(args)))
        oper = self.get_value(args[0])
        if not (isinstance(oper, int) or isinstance(oper, float)):
            raise InterpreterError(str(oper) + ' is not a number')
        self.set_value(args[0], oper - 1)

    def cmd_add(self, args: list):
        if len(args) != 2:
            raise InterpreterError('ADD takes 2 arguments but {} were given'.format(len(args)))
        oper1, oper2 = self.get_operands(args)
        self.set_value('@', oper1 + oper2)

    def cmd_sub(self, args: list):
        if len(args) != 2:
            raise InterpreterError('SUB takes 2 arguments but {} were given'.format(len(args)))
        oper1, oper2 = self.get_operands(args)
        self.set_value('@', oper1 - oper2)

    def cmd_mul(self, args: list):
        if len(args) != 2:
            raise InterpreterError('MUL takes 2 arguments but {} were given'.format(len(args)))
        oper1, oper2 = self.get_operands(args)
        self.set_value('@', oper1 * oper2)

    def cmd_div(self, args: list):
        if len(args) != 2:
            raise InterpreterError('DIV takes 2 arguments but {} were given'.format(len(args)))
        oper1, oper2 = self.get_operands(args)
        if oper2 == 0:
            raise InterpreterError('division by zero')
        self.set_value('@', oper1 / oper2)

    def cmd_mod(self, args: list):
        if len(args) != 2:
            raise InterpreterError('MOD takes 2 arguments but {} were given'.format(len(args)))
        oper1, oper2 = self.get_operands(args)
        if oper2 == 0:
            raise InterpreterError('modulo by zero')
        self.set_value('@', oper1 % oper2)

    def cmd_pow(self, args: list):
        if len(args) != 2:
            raise InterpreterError('POW takes 2 arguments but {} were given'.format(len(args)))
        oper1, oper2 = self.get_operands(args)
        self.set_value('@', oper1 ** oper2)

    def cmd_eq(self, args: list):
        if len(args) != 2:
            raise InterpreterError('EQ takes 2 arguments but {} were given'.format(len(args)))
        oper1 = self.get_value(args[0])
        oper2 = self.get_value(args[1])
        self.set_value('@', 1 if oper1 == oper2 else 0)

    def cmd_neq(self, args: list):
        if len(args) != 2:
            raise InterpreterError('NEQ takes 2 arguments but {} were given'.format(len(args)))
        oper1 = self.get_value(args[0])
        oper2 = self.get_value(args[1])
        self.set_value('@', 1 if oper1 != oper2 else 0)

    def cmd_gt(self, args: list):
        if len(args) != 2:
            raise InterpreterError('GT takes 2 arguments but {} were given'.format(len(args)))
        oper1, oper2 = self.get_operands(args)
        self.set_value('@', 1 if oper1 > oper2 else 0)

    def cmd_ls(self, args: list):
        if len(args) != 2:
            raise InterpreterError('LS takes 2 arguments but {} were given'.format(len(args)))
        oper1, oper2 = self.get_operands(args)
        self.set_value('@', 1 if oper1 < oper2 else 0)

    def cmd_ge(self, args: list):
        if len(args) != 2:
            raise InterpreterError('GE takes 2 arguments but {} were given'.format(len(args)))
        oper1, oper2 = self.get_operands(args)
        self.set_value('@', 1 if oper1 >= oper2 else 0)

    def cmd_le(self, args: list):
        if len(args) != 2:
            raise InterpreterError('LE takes 2 arguments but {} were given'.format(len(args)))
        oper1, oper2 = self.get_operands(args)
        self.set_value('@', 1 if oper1 <= oper2 else 0)

    def cmd_and(self, args: list):
        if len(args) != 2:
            raise InterpreterError('AND takes 2 arguments but {} were given'.format(len(args)))
        oper1 = self.get_value(args[0])
        oper2 = self.get_value(args[1])
        self.set_value('@', 1 if oper1 != 0 and oper2 != 0 else 0)

    def cmd_or(self, args: list):
        if len(args) != 2:
            raise InterpreterError('OR takes 2 arguments but {} were given'.format(len(args)))
        oper1 = self.get_value(args[0])
        oper2 = self.get_value(args[1])
        self.set_value('@', 1 if oper1 != 0 or oper2 != 0 else 0)

    def cmd_not(self, args: list):
        if len(args) != 1:
            raise InterpreterError('NOT takes 1 argument but {} were given'.format(len(args)))
        oper = self.get_value(args[0])
        self.set_value('@', 0 if oper != 0 else 1)
