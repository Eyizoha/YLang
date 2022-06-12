# YLang
The interpreter of Y Language.
## 简介
 前身：[Y语言1.0](https://blog.csdn.net/Eyizoha/article/details/107273301)，相比Y1.0版本主要做了以下改动：
 - **真正的函数**：新版解释器加入了调用栈，现在的Y语言函数支持了传参和返回值功能，同时可以进行复杂的嵌套调用和递归调用了，函数仍然支持嵌套定义；
 - **变量域**：新增了变量域的概念，现在变量区分局部变量和全局变量了，在使用CALL语句调用函数和RET语句返回时会有局部变量域的切换发生；
 - **特殊变量@**：新增了一个特殊的全局变量@，绝大部分运算指令和函数返回值都会在运行结束后存入该变量；
 - **更自然的列表**：删除了v1.0中反人类的idx、set和len等列表操作指令，现在可以用中括号[]来索引列表中的元素了，创建列表也可以采用[1,2,3]这种方式了，同时还支持了列表嵌套索引、嵌套定义和多维列表；
 - **更简洁的if语句**：现在if语句支持if 1 < 2这种书写方式了，此外还加入了else语句； 
 - **循环语句**：新增了loop语句，类似高级语言中while的用法，写循环不再需要危险的at和go了；
 - **移除字符串**：暂时移除了字符串的支持和相关操作，后续会支持；
 
 v2.1
 - **支持多线程**：新增了多线程的相关支持，像使用call指令一样使用run指令便可开启新线程执行函数；

 一段代码片段示例：
 Python：
```python
# 函数flatten可以将一个多层嵌套列表list压平成一维列表
def flatten(lst):
	tmp = []
	for item in lst:
		if isinstance(item, list):
			for it in flatten(item):
				tmp.append(it)
		else:
			tmp.append(item)
	return tmp

x = [1, [2, [3, [4, [5], 6, [[7, 8], 9]]]], 10, 11, 12]
print(x, len(x))
y = flatten(x)
print(y, len(y))
```
翻译成Y语言：
```y
// 函数flatten可以将一个多层嵌套列表list压平成一维列表
def flatten list
    mov tmp []
    mov i 0
    // list[] 返回list的长度，对于非列表则返回-1
    loop i < list[]
        if list[i][] == -1
            push tmp list[i]
        else
        	// 激动人心的递归调用
            call flatten list[i]
            mov res
            mov j 0
            loop j < res[]
                push tmp res[j]
                inc j
            elop
        eif
        inc i
    elop
    ret tmp
edef

// 定义复杂的嵌套列表x
mov x [1,[2,[3,[4,[5],6,[[7,8],9]]]],10,11,12]
out x x[]
call flatten x
// 返回值放入特殊变量@，此时@ = [1,2,3,4,5,6,7,8,9,10,11,12]
out @ @[]
```

## 详细介绍
###### 1.空格、换行、注释以及缩进
空格是Y语言语句中唯一的分隔符，指令与变量与常量之间均以空格分隔。
语句与语句之间用换行分隔，一行只能有一条语句。
注释以//或#打头，运行时跳过，空行同理。
缩进对代码运行无影响。
###### 2.变量
变量名为非数字打头的下划线数字字母串，变量自身无类型，可存储Y语言支持的三种数据类型：整数，浮点数，列表。
变量分为全局变量和局部变量，取变量时优先搜索局部变量域，即定义局部变量会屏蔽同名全局变量。存变量时除非使用glb指令，否则都存入局部变量域（局部变量不存在时会被创建）。调用函数和函数返回时会发生局部变量域切换。全局变量域始终可见。
另外@为一个特殊的全局变量，用于存储一些指令的结果。
**数据类型支持整数、浮点数、列表三种**
数字皆以自然方式定义，如：1、0、1.5、-1.5、+6皆为有效定义；
列表以[]括起来的一组元素定义，元素间以逗号分隔，支持嵌套定义列表和包含变量，如：[1,2,3,[1,2,3],var1,var2]。空[]表示空列表。
列表的索引也采用[]，list[x]表示列表list的x项，若list是多维列表也支持list[x]\[y]来多维索引，list[x[y]]的嵌套索引也支持。此外变量名后接空括号[]表示求长度，如array = [1,2,3] 则array[]为3，若array为非列表则array[] = -1。
###### 3.行号和指令
Y语言的代码从头开始逐行运行，每行代码都对应一个行号，行号从0开始。每行语句的第一个单词即指令，其后都为指令需要的参数，指令指示解释器的行为，具体见下文。
## 指令和语法
指令可以分为控制指令、操作指令、逻辑指令和外部指令四类，所有指令运行时均不分大小写。其中外部指令由解释器外挂了哪些模块决定，并非通用的指令。
###### 1.控制指令
 - **at**：定位指令，不推荐使用，接受一个变量名，将当前行号存入该变量。如 at var。
 - **go**：跳转指令，不推荐使用，接受一个参数，可以是整数常量或变量，将当前运行行跳转到数字对应行的**下一行**。如 go target。
 - **mov**：赋值指令，接受一个变量名和一个可选参数，将第二个常量或变量的值存入第一个变量，第一个变量（除@外）在局部变量域不存在时会被创建，若无第二个参数则默认为@。如 mov list [1,2,3]或 mov @ 1.234，此外mov x 等效于 mov x @。
 - **glb**：全局赋值指令，用法与mov相同，但对第一个参数的操作变量域为全局变量域。
 - **if**：条件指令，接受1或3个参数，接受1个参数时，若该参数为**0**则跳转到匹配的**else**（如果有）或**eif**，否则继续运行，如：if flag。接受三个参数时需要满足if a op b 的形式，其中a、b皆为数字量，op为<、<=、>、>=、==、!=中的一种，a op b表达成立时继续运行否则跳转，如 if var <= 999。
 - **else**：否则条件指令，不接受参数，与**if**配对使用，当**if**条件不满足时会跳转到该指令（如果有），若**if**条件满足遇到该指令则会跳转到匹配的**eif**。
 - **eif**：结束条件指令，不接受参数，与**if**配对使用，用于**if**和**else**的跳转定位，**eif**会匹配之前最近一个未被匹配的**if**。
 - **def**：函数定义指令，接受一个变量名和若干可选变量名，将当前行号存入该变量（定义于最外层的函数会被存入全局变量），可选变量名将作为函数调用时的局部变量被传入参数创建，随后跳转到对应**edef**语句，用于定义函数。如 def fun a b。
 - **edef**：结束定义指令，不接受参数，与**def**配对使用，用于结束**def**的定义范围。
 - **call**：调用指令，接受一个变量名和该变量对应函数对应的参数个数，储存当前位置和局部变量进入调用栈，以传入参数创建新的局部变量域并跳转至函数定义行的下一行，如 call fun 1 2。
 - **ret**：返回指令，接受一个可选参数，仅能在调用函数内使用，从调用栈中弹出上一层的**call**的调用位置和局部变量域并跳转，如果接受了参数还会将该参数值存入变量@，如 ret a。
 - **loop**：循环指令，接受参数与**if**相同，与**elop**配对使用，满足条件时继续运行，否则跳转到对应**elop**指令的下一行，如 loop i < array[]。
 - **elop**：循环结束指令，不接受参数，与**loop**配对使用，跳转回对应的**loop**。
 - **brk**：跳出指令，接受参数时接受参数与**if**相同，用于循环内部，跳转到对应**elop**指令的下一行，不接受参数时相当于brk 1。
 - **ctn**：继续指令，接受参数时接受参数与**if**相同，用于循环内部，跳转到对应**loop**指令，不接受参数时相当于ctn 1。
###### 2.操作指令
 - **cpy**：拷贝指令，接受一个变量名和一个可选列表参数，将第二个列表值拷贝进第一个变量，若无第二个参数则默认为@，如 cpy list1 list2。
 - **push**：压入指令，接受一个列表和一个可选参数和一个可选位置，无位置参数时将第二个参数追加到列表末尾（否则插入到对应位置），如 push list var 或 push list var index。无可选参数时 push list 相当于 push list @。
 - **pop**：弹出指令，接受一个列表和一个可选参数和一个可选位置，无位置参数时将列表末尾元素（否则弹出该位置元素）弹出放入第二个参数，如 pop list var 或 pop list var index。无可选参数时 pop list 相当于 pop list @。
 - **idx**：索引指令，接受一个列表和一个可选参数，求第二个参数在列表中的索引（不存在则为-1），若无第二个参数则默认为@，如 idx list item。
 - **revs**：反转指令，接受一个列表，将其反转，如 revs list。
 - **sort**：排序指令，接受一个列表，将其排序，如 sort list。
 - **int**：取整指令，接受一个数字变量，将其值的小数部分舍去，如 int num。
 - **inc**：自增指令，接受一个数字变量，将其值增加1，如 inc x。
 - **dec**：自减指令，接受一个数字变量，将其值减少1，如 dec x。
 - **add**：加法指令，接受两个数字量，求和存入@，如 add n 1。
 - **sub**：减法指令，接受两个数字量，求差存入@，如 sub n 2。
 - **mul**：乘法指令，接受两个数字量，求积存入@，如 mul n 3。
 - **div**：除法指令，接受两个数字量，求商存入@，如 div n 4。
 - **mod**：模指令，接受两个数字量，求模存入@，如 mod n 5。
 - **pow**：幂指令，接受两个数字量，求幂存入@，如 pow n 0.5。
###### 3.逻辑指令
 - **eq**：相等指令，接受两个参数，两个参数相等时将1存入@，否则将0存入@，如 eq i [1,2,3]。
 - **neq**：不等指令，接受两个参数，两个参数相等时将0存入@，否则将1存入@，如 neq i 22。
 - **gt**：大于指令，接受两个数字量，满足前者大于后者时将1存入@，否则将0存入@，如 gt x 0。
 - **ls**：小于指令，接受两个数字量，满足前者小于后者时将1存入@，否则将0存入@，如 ls x 0。
 - **ge**：大于等于指令，接受两个数字量，满足前者大于等于后者时将1存入@，否则将0存入@，如 ge x 0。
 - **le**：小于等于指令，接受两个数字量，满足前者小于等于后者时将1存入@，否则将0存入@，如 le x 0。
 - **and**：逻辑与指令，接受两个参数，两个参数都不为0时将1存入@，否则将0存入@，如 and a b。
 - **or**：逻辑或指令，接受两个参数，两个参数任意一个不为0时将1存入@，否则将0存入@，如 or a b。
 - **not**：逻辑与指令，接受一个参数，参数为0时将1存入@，否则将0存入@，如 not a。
###### 4.多线程指令
 - **tid**：线程id指令，接受一个变量名，将当前线程id存入该变量。如 tid var。
 - **run**：异步调用指令，接受参数与**call**相同，但是会创建一个新线程执行目标函数，同时将新线程id存入@，如 run fun 1 2。
 - **fork**：线程分支指令，不接受参数，为调用进程复制一个完全相同的新线程，同时将新线程id存入@，在新线程中则是将-1存入@，如 fork。
 - **wait**：等待线程指令，接受一个数字量作为线程id，若目标id线程存在则阻塞自身直到目标id线程结束，如 wait tid。
 - **kill**：结束线程指令，接受一个数字量作为线程id，若目标id线程存在则强制结束目标id线程，如 kill tid。
 - **lock**：加锁指令，接受一个列表量作为互斥锁，尝试加锁，加锁成功继续执行，否则阻塞等待锁释放，如 lock mutex。
 - **ulck**：解锁指令，接受一个列表量作为互斥锁，只有成功加锁后才能调用，释放该锁并唤醒等待该锁的下一个线程，如 ulck mutex。
###### 5.外部指令
 - **out**：输出指令，来自模块Outputer，接受任意个参数，将其依次输出到屏幕，如 out 1 x y。
 - **in**：输入指令，来自模块Inputer，不接受参数，从键盘输入一个数字存入@。
- **sleep**：睡眠指令，接受一个非负数字量，使当前线程阻塞对应秒，如 sleep 1。
 - **……**

## 案例代码和运行效果
###### 1、质数输出
```y
def isprime n
    pow n 0.5
    mov t
    mov i 2
    loop i <= t
        mod n i
        if @ == 0
            ret 0
        eif
        inc i
    elop
    ret 1
edef

def print_prime n
    mov primes []
    mov i 2
    loop i <= n
        call isprime i
        if
            push primes i
        eif
        inc i
    elop
    ret primes
edef

call print_prime 1000
out @
```
> 输出：[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691, 701, 709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, 811, 821, 823, 827, 829, 839, 853, 857, 859, 863, 877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947, 953, 967, 971, 977, 983, 991, 997]
###### 2、快速排序
```y
def Qsort array
    sub array[] 1
    call quick_sort array 0 @
edef

def quick_sort array low high
    loop low < high
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
        call quick_sort array low @
        add i 1
        mov low
    elop
edef

mov array [3,5,6,8,3,1,2,5,7,9,5,6,8,6,5]
call Qsort array
out array
```

> 输出：[1, 2, 3, 3, 5, 5, 5, 5, 6, 6, 6, 7, 8, 8, 9]
###### 3、多线程报数
```y
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
```
