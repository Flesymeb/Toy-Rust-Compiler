.data
a: .word 0
b: .word 0
i: .word 0
t0: .word 0
t1: .word 0
t2: .word 0
t3: .word 0
t4: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 1
	sw $s0, 4($sp)
li $s1, 2
	sw $s1, b
li $s2, 0
	sw $s2, i
L0:
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
lw $s0, 20($sp)
li $s1, 0
	xor $s0, $s0, $s1
	sltiu $s0, $s0, 1
	beq $s0, $zero, L4
	j L0
L4:
L5:
lw $s0, 4($sp)
lw $s1, i
	add $s0, $s0, $s1
	sw $s0, 4($sp)
	j L0
L1:
li $s0, 10
	sw $s0, 4($sp)
lw $s1, 4($sp)
	sw $s1, b
	j end

end:
	li $v0, 10
	syscall