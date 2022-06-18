from moudle import BaseMoudle, MoudleError
from interpreter import Interpreter, InterpreterError
from random import choice, choices
from threading import Lock


class Cpu:
    def __init__(self, command_per_turn: int, time_slice_len=5, scheduler='random-with-waiting'):
        self._command_per_turn = command_per_turn
        self._time_slice_len = time_slice_len
        self._scheduling_thread = None
        if scheduler.lower() == 'round-robin':
            self._scheduling_thread = self._scheduler_round_robin
        elif scheduler.lower() == 'random':
            self._scheduling_thread = self._scheduler_random
        elif scheduler.lower() == 'random-with-waiting':
            self._scheduling_thread = self._scheduler_random_with_waiting
        else:
            print('Cpu Error: Unknow scheduler, it must be one of {round-robin, random, random-with-waiting}')
            return
        self._bus = Bus()
        self._codes = None  # Y语言代码，字符串列表
        self.cpu_api = {'codes': self._get_codes,
                        'global_vars': self._get_global_vars,
                        'module_commands': self._get_module_commands,
                        'create_thread': self._create_thread,
                        'activate_thread': self._activate_thread,
                        'block_thread': self._block_thread,
                        'wait_thread': self._wait_thread,
                        'kill_thread': self._kill_thread,
                        'is_blocked': self._is_blocked_thread}  # cpu暴露给线程的api
        self._global_vars = {}  # 全局变量
        self._module_commands = None  # 模块指令集

        self.lock = Lock()
        self._all_threads = {}  # 所有线程
        self._active_thread_ids = []  # 活动线程id
        self._blocked_thread_ids = set()  # 阻塞线程id

        self._next_id = 0
        self._round_idx = 0
        self._running_thread = None
        self._running_remain_time = 0
        self._cpu_remain_time = 0

    def install(self, moudle: BaseMoudle):
        moudle.set_api(self.cpu_api)
        self._bus.install(moudle)

    def uninstall(self, moudle: BaseMoudle):
        self._bus.uninstall(moudle)

    def boot(self, codestr: str):
        self._codes = codestr.split('\n')
        self._module_commands = {mod.command: mod.run for mod in self._bus.modules.values()}
        self._create_thread(0, {})

    def run(self):
        if not self._active_thread_ids:
            return len(self._all_threads) != 0
        self._cpu_remain_time = self._command_per_turn
        if self._running_thread:
            self._run_internal()
        while self._cpu_remain_time > 0:
            self._running_remain_time = self._time_slice_len
            if not self._active_thread_ids:
                return len(self._all_threads) != 0
            self.lock.acquire()
            self._running_thread = self._scheduling_thread()
            self.lock.release()
            self._run_internal()
        return True

    def print_thread_status(self, more_detail=False):
        rtid = -1
        if self._running_thread:
            rtid = self._running_thread.tid
        print('-------------------------------------------------------' * (1 + more_detail))
        for thread in self._all_threads.values():
            tid = thread.tid
            running = '* ' if tid == rtid else ''
            state = 'blocked' if self._is_blocked_thread(tid) else 'active'
            line = thread.pointer
            code = self._codes[line].strip() if 0 <= line < len(self._codes) else ''
            msg = '{}tid: {}, state: {}, next line {}: {}'.format(running, tid, state, line, code)
            if more_detail:
                msg += ' | ' + str(thread.local_vars)
            print(msg)

    def _run_internal(self):
        if self._cpu_remain_time >= self._running_remain_time:
            cost = self._run_running_thread(self._running_remain_time)
            if cost < self._running_remain_time and not self._is_blocked_thread(self._running_thread.tid):
                self._finish_thread(self._running_thread.tid)
            self._cpu_remain_time -= cost
            self._running_thread, self._running_remain_time = None, 0
        else:
            self._running_remain_time -= self._cpu_remain_time
            cost = self._run_running_thread(self._cpu_remain_time)
            if cost < self._cpu_remain_time and not self._is_blocked_thread(self._running_thread.tid):
                self._finish_thread(self._running_thread.tid)
                self._running_thread, self._running_remain_time = None, 0
            self._cpu_remain_time -= cost

    def _run_running_thread(self, num_exec):
        try:
            return self._running_thread.run(num_exec)
        except InterpreterError as e:
            tid = self._running_thread.tid
            line = self._running_thread.pointer
            code = self._codes[line].strip()
            print('(Thread-{}, Line {}: {})Interpreter Error: {}'.format(tid, line, code, e))
            return e.count
        except MoudleError as e:
            tid = self._running_thread.tid
            line = self._running_thread.pointer
            code = self._codes[line].strip()
            print('(Thread-{}, Line {}: {})Moudle Error: {}'.format(tid, line, code, e))
            # TODO: count for MoudleError
            return 0

    def _get_codes(self):
        return self._codes

    def _get_global_vars(self):
        return self._global_vars

    def _get_module_commands(self):
        return self._module_commands

    def _scheduler_round_robin(self):
        self._round_idx += 1
        self._round_idx %= len(self._active_thread_ids)
        return self._all_threads[self._active_thread_ids[self._round_idx]]

    def _scheduler_random(self):
        return self._all_threads[choice(self._active_thread_ids)]

    def _scheduler_random_with_waiting(self):
        tid = choices(self._active_thread_ids, [self._all_threads[tid].wait_time for tid in self._active_thread_ids])[0]
        for t in self._active_thread_ids:
            self._all_threads[t].wait_time += 1
        self._all_threads[tid].wait_time = 1
        return self._all_threads[tid]

    def _create_thread(self, pointer, local_vars, ans=0, call_stack=None):
        thread = Interpreter(self.cpu_api, self._next_id, pointer, local_vars, ans, call_stack)
        self._active_thread_ids.append(thread.tid)
        self._all_threads[thread.tid] = thread
        self._next_id += 1
        return thread.tid

    def _activate_thread(self, tid):
        assert tid in self._blocked_thread_ids
        self._blocked_thread_ids.remove(tid)
        self.lock.acquire()
        self._active_thread_ids.append(tid)
        self.lock.release()

    def _block_thread(self, tid):
        assert tid in self._active_thread_ids
        self._blocked_thread_ids.add(tid)
        self.lock.acquire()
        self._active_thread_ids.remove(tid)
        self.lock.release()
        self._round_idx -= 1

    def _finish_thread(self, tid):
        if tid not in self._all_threads.keys():
            return
        for t in self._all_threads[tid].wait_this_tids:
            self._activate_thread(t)
        del self._all_threads[tid]
        self._active_thread_ids.remove(tid)
        self._round_idx -= 1

    def _wait_thread(self, tid, wait_tid):
        if wait_tid in self._all_threads.keys():
            self._all_threads[wait_tid].wait_this_tids.add(tid)
            self._block_thread(tid)

    def _kill_thread(self, tid):
        assert tid in self._all_threads.keys()
        for t in self._all_threads[tid].wait_this_tids:
            self._activate_thread(t)
        del self._all_threads[tid]
        if tid in self._active_thread_ids:
            self._active_thread_ids.remove(tid)
            self._round_idx -= 1

    def _is_blocked_thread(self, tid):
        return tid in self._blocked_thread_ids


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
