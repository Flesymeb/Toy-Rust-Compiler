.data
t0: .word 0
t1: .word 0
t10: .word 0
t11: .word 0
t12: .word 0
t13: .word 0
t14: .word 0
t2: .word 0
t3: .word 0
t4: .word 0
t5: .word 0
t6: .word 0
t7: .word 0
t8: .word 0
t9: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 1
li $s1, 2
	mul $s2, $s0, $s1
li $s3, 3
	div $s2, $s3
	mflo $s2
li $s4, 5
li $s5, 6
	div $s4, $s5
	mflo $s6
li $s7, 4
	add $s2, $s7, $s6
li $s6, 7
li $s2, 8
	slt $s2, $s6, $s2
li $s2, 9
li $s6, 10
	slt $s2, $s6, $s2
li $s2, 11
li $s2, 12
	xor $s2, $s2, $s2
	sltiu $s2, $s2, 1
li $s2, 13
li $s2, 14
	xor $s2, $s2, $s2
	sltu $s2, $zero, $s2
li $s2, 1
li $s2, 2
	mul $s2, $s2, $s2
li $s2, 3
li $s2, 4
	mul $s6, $s2, $s2
	add $s2, $s2, $s6
li $s6, 4
li $s2, 2
	div $s6, $s2
	mflo $s2
li $s2, 3
li $s6, 1
	div $s2, $s6
	mflo $s6
	sub $s6, $s2, $s6
	xor $s2, $s2, $s6
	sltu $s2, $zero, $s2
	j end

end:
	li $v0, 10
	syscall