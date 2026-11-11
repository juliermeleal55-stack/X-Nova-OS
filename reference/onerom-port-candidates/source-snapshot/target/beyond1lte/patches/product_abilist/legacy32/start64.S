    .text
    .globl _start
    .type _start, %function
_start:
    mov x29, xzr
    mov x30, xzr
    mov x0, sp
    mov x1, xzr
    adrp x2, main
    add x2, x2, :lo12:main
    adrp x3, .Lstructors
    add x3, x3, :lo12:.Lstructors
    b __libc_init
    .section .rodata
    .align 3
.Lstructors:
    .xword 0, 0, 0, 0
    .section .note.GNU-stack,"",%progbits