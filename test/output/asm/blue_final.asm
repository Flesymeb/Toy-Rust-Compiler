.data
i: .word 0
result: .word 0
sum1: .word 0
sum2: .word 0
t: .word 0
t0: .word 0
t1: .word 0
t10: .word 0
t11: .word 0
t12: .word 0
t13: .word 0
t14: .word 0
t16: .word 0
t2: .word 0
t3: .word 0
t4: .word 0
t5: .word 0
t6: .word 0
t7: .word 0
t8: .word 0
t9: .word 0
x: .word 0
y: .word 0
z: .word 0

.text
lui $sp, 0x1004
j main

test_group5:
	sw $ra, 4($sp)
li $s0, 0
	sw $s0, sum1
li $s1, 1
	sw $s1, 64($sp)
L0:
lw $s0, 64($sp)
li $s1, 10
	slt $s0, $s0, $s1
	beq $s0, $zero, L1
lw $s0, 64($sp)
	sw $s0, i
lw $s1, sum1
lw $s2, i
	add $s3, $s1, $s2
	sw $s3, sum1
L2:
li $s4, 1
	add $s0, $s0, $s4
	j L0
L1:
li $s0, 0
	sw $s0, sum2
li $s1, 0
	sw $s1, i
L3:
lw $s0, i
li $s1, 1
	add $s2, $s0, $s1
	sw $s2, i
li $s3, 10
	slt $s4, $s3, $s0
	beq $s4, $zero, L5
	j L4
L5:
L6:
lw $s0, i
li $s1, 5
	xor $s2, $s0, $s1
	sltiu $s2, $s2, 1
	beq $s2, $zero, L7
	j L3
L7:
L8:
lw $s0, sum2
lw $s1, i
	add $s2, $s0, $s1
	sw $s2, sum2
	j L3
L4:
	lw $ra, 4($sp)
	jr $ra
	lw $ra, 4($sp)
	jr $ra

test_group7:
	sw $ra, 4($sp)
lw $s0, x
	mul $s1, $s0, $s0
	add $s1, $s1, $s0
	sw $s1, 52($sp)
lw $s2, y
	mul $s3, $s0, $s2
lw $s4, 52($sp)
	add $s4, $s4, $s3
	sw $s4, 52($sp)
li $s3, None
	sw $s3, z
lw $s5, z
li $s6, 10
	slt $s7, $s6, $s5
	beq $s7, $zero, L10
L9:
lw $s0, z
li $s1, 5
	sub $s2, $s0, $s1
li $s3, None
	sw $s3, 8($sp)
	j L11
L10:
lw $s0, z
li $s1, 5
	add $s2, $s0, $s1
li $s3, None
	sw $s3, 8($sp)
L11:
lw $s0, 8($sp)
	sw $s0, result
	lw $v0, result
	lw $ra, 4($sp)
	jr $ra
	lw $ra, 4($sp)
	jr $ra

main:
	jal test_group5
	add $s0, $v0, $zero
li $s1, 4
	sw $s1, 76($sp)
li $s2, 3
	sw $s2, 80($sp)
	sw $sp, 68($sp)
	addi $sp, $sp, 68
	jal test_group7
	lw $sp, 0($sp)
	add $s3, $v0, $zero
	sw $s3, result
	j end
	j end

end:
	li $v0, 10
	syscall