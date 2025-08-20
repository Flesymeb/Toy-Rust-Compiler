.data
i: .word 0
t0: .word 0
t1: .word 0
t2: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 0
	sw $s0, i
L0:
lw $s0, i
li $s1, 10
	slt $s2, $s0, $s1
	beq $s2, $zero, L1
lw $s0, i
li $s1, 1
	add $s2, $s0, $s1
	sw $s2, i
li $s3, 5
	slt $s4, $s3, $s0
	beq $s4, $zero, L2
	j L1
L2:
L3:
	j L0
L1:
	j end

end:
	li $v0, 10
	syscall