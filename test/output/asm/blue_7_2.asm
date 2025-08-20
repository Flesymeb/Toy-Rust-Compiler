.data
t: .word 0
t0: .word 0
t1: .word 0
t2: .word 0
t3: .word 0
x: .word 0
y: .word 0

.text
lui $sp, 0x1004
j main

program_7_2:
	sw $ra, 4($sp)
lw $s0, x
	mul $s1, $s0, $s0
	add $s1, $s1, $s0
	sw $s1, 20($sp)
lw $s2, y
	mul $s3, $s0, $s2
lw $s4, 20($sp)
	add $s5, $s4, $s3
	sw $s5, 20($sp)
	add $v0, $s4, $zero
	lw $ra, 4($sp)
	jr $ra
	lw $ra, 4($sp)
	jr $ra

end:
	li $v0, 10
	syscall