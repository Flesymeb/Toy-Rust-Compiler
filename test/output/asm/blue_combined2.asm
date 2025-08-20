.data
a: .word 0
b: .word 0
c: .word 0
d: .word 0
i: .word 0
t: .word 0
t0: .word 0
t1: .word 0
t2: .word 0
t3: .word 0
t4: .word 0
t5: .word 0
t6: .word 0
t7: .word 0
t8: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 1
	sw $s0, 40($sp)
li $s1, 2
	sw $s1, b
li $s2, 0
	sw $s2, i
L0:
lw $s0, i
li $s1, 1
	add $s2, $s0, $s1
	sw $s2, i
li $s3, 10
	slt $s4, $s3, $s0
	beq $s4, $zero, L2
	j L1
L2:
L3:
lw $s0, i
li $s1, 5
	xor $s2, $s0, $s1
	sltiu $s2, $s2, 1
	beq $s2, $zero, L4
	j L0
L4:
L5:
	j L0
L1:
lw $s0, 40($sp)
	mul $s0, $s0, $s0
	sw $s0, 36($sp)
lw $s1, 36($sp)
lw $s2, b
	add $s1, $s1, $s2
	sw $s1, 36($sp)
li $s3, None
	sw $s3, c
lw $s4, c
li $s5, 10
	slt $s6, $s5, $s4
	beq $s6, $zero, L7
L6:
lw $s0, c
li $s1, 5
	sub $s2, $s0, $s1
li $s3, None
	sw $s3, 16($sp)
	j L8
L7:
lw $s0, c
li $s1, 5
	add $s2, $s0, $s1
li $s3, None
	sw $s3, 16($sp)
L8:
lw $s0, 16($sp)
	sw $s0, d
	j end

end:
	li $v0, 10
	syscall