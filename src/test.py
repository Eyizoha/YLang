from cpu import Cpu
from moudle import *
from random import randint
from numpy.linalg import det
from time import perf_counter as pc

code = '''
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

def gen_mat n
    mov mat []
    mov i 0
    loop i < n
        mov row []
        mov j 0
        loop j < n
            randint -1000 1000
            div @ 100
            push row
            inc j
        elop
        push mat row
        inc i
    elop
    ret mat
edef

mov mat {}
call det mat
out @
'''

n = 6
mat = [[randint(-9, 9) for _ in range(n)] for _ in range(n)]
print('mat:', mat)

cpu = Cpu(1)
cpu.bus.install(Inputer())
cpu.bus.install(Outputer())
cpu.boot(code.format(str(mat).replace(' ', '')))

t1 = pc()
print(det(mat))
print('np det cost:', pc() - t1)

count = 1
t2 = pc()
while cpu.run():
    count += 1
print('YLang det cost:', pc() - t2)
print('YLang cmd exec count:', count)
