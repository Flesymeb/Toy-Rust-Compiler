.data
a: .word 0
b: .word 0
t0: .word 0
t1: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 1
	sw $s0, 8($sp)
lw $s1, 8($sp)
li $s2, 0
	slt $s1, $s2, $s1
	beq $s1, $zero, L1
L0:
li $s0, None
	sw $s0, 0($sp)
	j L2
L1:
li $s0, None
	sw $s0, 0($sp)
L2:
lw $s0, 0($sp)
	sw $s0, b
	j end

end:
	li $v0, 10
	syscall