from cpu import Cpu
from moudle import *
from random import randint
from numpy.linalg import det
from time import perf_counter as pc

fun_det = '''
def det mat
    mov ans 0
    mov n mat[]
    if n == 1
        ret mat[0][0]
    eif
    if n == 2
        mul mat[0][0] mat[1][1]
        mov ans
        mul mat[0][1] mat[1][0]
        sub ans @
        mov ans
    else
        mov k 0
        loop k < n
            if mat[0][k]
                mov minor []
                sub n 1
                mov nsub1
                mov i 0
                loop i < nsub1
                    mov j 0
                    mov row []
                    loop j < nsub1
                        mov newi i
                        mov newj j
                        inc newi
                        if newj >= k
                            inc newj
                        eif
                        push row mat[newi][newj]
                        inc j
                    elop
                    push minor row
                    inc i
                elop
                call det minor
                mov tmp @
                pow -1 k
                mul @ tmp
                mul @ mat[0][k]
                add ans @
                mov ans
            eif
            inc k
        elop
    eif
    ret ans
edef
'''

code_det_test = '''
mov mat {}
call det mat
out @
'''

code_mt_test = """
def loop_out res mutex
    out res
    mov len res[]
    loop 1
        lock mutex
        if res[] != len
            mov len res[]
            out res
        eif
        ulck mutex
    elop
edef

def loop_in res mutex
    loop 1
        lock mutex
        in
        if @ == -1
            ret
        eif
        push res
        mod res[] 3
        if @ == 0
            ulck mutex
        eif
    elop
edef

mov res []
mov mutex []
run loop_out res mutex
mov tid1
run loop_in res mutex
mov tid2
wait tid2
kill tid1
out 0
"""

code_mt_test2 = """
def gen_prime primes
    def is_prime num
        pow num 0.5
        mov sqrt_num @
        mov i 2
        loop i <= sqrt_num
            mod num i
            if @ == 0
                ret 0
            eif
            inc i
        elop
        ret 1
    edef
    
    mov i 2
    loop 1
        call is_prime i
        if @
            push primes i
        eif
        inc i
    elop
edef

def get_prime primes ids
    mov id 0
    loop 1
        if ids[]
            pop ids id 0
            if id < primes[]
                out [id,primes[id]]
            else
                push ids id
            eif
        eif
    elop
edef

mov primes [1]
mov ids []
run gen_prime primes
mov tid1 @
run get_prime primes ids
mov tid2 @

loop 1
    in
    brk @ < 0
    push ids @
elop
kill tid1
kill tid2
out primes[]
"""


def det_test():
    n = 6
    mat = [[randint(-9, 9) for _ in range(n)] for _ in range(n)]
    print('mat:', mat)

    cpt = 1
    cpu = Cpu(cpt)
    cpu.install(Inputer())
    cpu.install(Outputer())
    cpu.boot(fun_det + code_det_test.format(str(mat).replace(' ', '')))

    t1 = pc()
    print(det(mat))
    print('np det cost:', pc() - t1)

    count = 0
    t2 = pc()
    while cpu.run():
        count += cpt
        # cpu.print_thread_status(True)
    print('YLang det cost:', pc() - t2)
    print('YLang cmd exec count:', count)


def mt_test():
    cpt = 10
    cpu = Cpu(cpt, 3)
    cpu.install(Inputer())
    cpu.install(Outputer())
    cpu.boot(code_mt_test)
    while cpu.run():
        pass


def mt_test2():
    cpt = 10
    cpu = Cpu(cpt, 3)
    cpu.install(Inputer())
    cpu.install(Outputer())
    cpu.boot(code_mt_test2)
    while cpu.run():
        pass


def mt_test3():
    cpt = 10
    cpu = Cpu(cpt, 3)
    cpu.install(Inputer())
    cpu.install(Outputer())
    code = '''
    def async_add num step mutex
        loop 1
            lock mutex
            add num[0] step
            mov num[0] @
            ulck mutex
        elop
    edef

    mov tids []
    mov num [0]
    mov mutex []
    run async_add num 1 mutex
    push tids
    run async_add num 2 mutex
    push tids
    run async_add num 3 mutex
    push tids
    loop 1
        lock mutex
        brk num[0] > 1000
        out num[0]
        ulck mutex
    elop
    mov i 0
    loop i < tids[]
        kill tids[i]
        inc i
    elop
    '''
    cpu.boot(code)
    while cpu.run():
        cpu.print_thread_status(True)


def fork_test():
    cpt = 1
    cpu = Cpu(cpt, 1)
    cpu.install(Inputer())
    cpu.install(Outputer())
    code = '''
    def forkn n
        mov i 0
        loop i < n
            inc i
            fork
        elop
    edef
    
    mov id 0
    call forkn 3
    tid id
    out id
    '''
    cpu.boot(code)
    while cpu.run():
        cpu.print_thread_status()
        pass


def sleep_test():
    cpt = 10
    cpu = Cpu(cpt, 3)
    cpu.install(Inputer())
    cpu.install(Outputer())
    cpu.install(Sleeper())
    code = '''
    def inc_per_sec num
        loop 1
            sleep 1
            inc num[0]
            out num[0]
        elop
    edef

    mov num [0]
    run inc_per_sec num
    mov tid
    loop num[0] >= 0
        in
        mov num[0]
    elop
    kill tid
    '''
    cpu.boot(code)
    while cpu.run():
        pass


def multi_qsort_test():
    cpt = 1
    cpu = Cpu(cpt, 3)
    cpu.install(Inputer())
    cpu.install(Outputer())
    cpu.install(Sleeper())
    code = '''
    def Qsort array ids
    sub array[] 1
    call quick_sort array 0 @ ids
    edef
    
    def quick_sort array low high ids
        if low >= high
            ret
        eif
        mov i low
        mov j high
        mov key array[low]
        loop i < j
            loop key <= array[j]
                brk i >= j
                dec j
            elop
            mov array[i] array[j]
            loop key >= array[i]
                brk i >= j
                inc i
            elop
            mov array[j] array[i]
        elop
        mov array[i] key
        sub i 1
        run quick_sort array low @ ids
        push ids
        add i 1
        run quick_sort array @ high ids
        push ids
    edef
    
    def wait ids signal
        loop ids[] > 0
            pop ids @ 0
            wait @
        elop
        mov signal[0] 0
    edef
    
    mov array {}
    mov ids []
    mov sig [1]
    run Qsort array ids
    push ids
    call wait ids sig
    # loop sig[0]
    #     out array
    #     sleep 0.001
    # elop
    out array
    '''

    cpu.boot(code.format(str([randint(0, 99) for _ in range(1000)]).replace(' ', '')))
    while cpu.run():
        cpu.print_thread_status()
        pass


if __name__ == '__main__':
    # det_test()
    # mt_test()
    # mt_test2()
    # mt_test3()
    # fork_test()
    # sleep_test()
    multi_qsort_test()
