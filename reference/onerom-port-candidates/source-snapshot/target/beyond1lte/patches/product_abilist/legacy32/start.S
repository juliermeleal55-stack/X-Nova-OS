    .syntax unified
    .arm
    .text
    .globl _start
    .type _start, %function
_start:
    mov r11, #0
    mov lr, #0
    mov r0, sp
    mov r1, #0
    ldr r2, .Lmain_offset
.Lmain_base:
    add r2, pc, r2
    ldr r3, .Lstructors_offset
.Lstructors_base:
    add r3, pc, r3
    b __libc_init
.Lmain_offset:
    .word main - (.Lmain_base + 8)
.Lstructors_offset:
    .word .Lstructors - (.Lstructors_base + 8)
    .section .rodata
    .align 2
.Lstructors:
    .word 0, 0, 0, 0
    .section .note.GNU-stack,"",%progbits