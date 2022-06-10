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
    cpu.boot(fun_det + code_mt_test2)
    while cpu.run():
        pass


if __name__ == '__main__':
    # det_test()
    # mt_test()
    mt_test2()
