.data
i: .word 0
n: .word 0
t0: .word 0
t1: .word 0
t2: .word 0
t3: .word 0

.text
lui $sp, 0x1004
j main

program_5_2:
	sw $ra, 4($sp)
lw $s0, 8($sp)
li $s1, 1
	add $s0, $s0, $s1
li $s2, 1
	sw $s2, 16($sp)
L0:
lw $s0, 16($sp)
lw $s1, 20($sp)
	slt $s0, $s0, $s1
	beq $s0, $zero, L1
lw $s0, 16($sp)
	sw $s0, i
lw $s1, 8($sp)
li $s2, 1
	sub $s1, $s1, $s2
	sw $s1, 8($sp)
L2:
li $s3, 1
	add $s0, $s0, $s3
	j L0
L1:
	lw $ra, 4($sp)
	jr $ra

end:
	li $v0, 10
	syscall