.data
i: .word 0
sum: .word 0
t0: .word 0
t1: .word 0
t2: .word 0
t3: .word 0
t4: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 0
	sw $s0, i
li $s1, 0
	sw $s1, sum
L0:
lw $s0, i
li $s1, 10
	slt $s2, $s0, $s1
	beq $s2, $zero, L1
lw $s0, i
li $s1, 1
	add $s2, $s0, $s1
	sw $s2, i
lw $s3, 0($sp)
li $s4, 0
	xor $s3, $s3, $s4
	sltiu $s3, $s3, 1
	beq $s3, $zero, L2
	j L0
L2:
L3:
lw $s0, sum
lw $s1, i
	add $s2, $s0, $s1
	sw $s2, sum
	j L0
L1:
	j end

end:
	li $v0, 10
	syscall