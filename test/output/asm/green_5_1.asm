.data
n: .word 0
t0: .word 0
t1: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 5
	sw $s0, 0($sp)
L0:
lw $s0, 0($sp)
li $s1, 0
	slt $s0, $s1, $s0
	beq $s0, $zero, L1
lw $s0, 0($sp)
li $s1, 1
	sub $s0, $s0, $s1
	sw $s0, 0($sp)
	j L0
L1:
	j end

end:
	li $v0, 10
	syscall