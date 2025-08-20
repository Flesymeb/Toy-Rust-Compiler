.data
t: .word 0
t0: .word 0
t1: .word 0
t2: .word 0
t3: .word 0
z: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 1
li $s1, 2
	mul $s2, $s0, $s1
li $s3, 3
	add $s2, $s2, $s3
	sw $s2, 16($sp)
li $s4, 4
li $s5, 5
	mul $s6, $s4, $s5
lw $s7, 16($sp)
	add $s7, $s7, $s6
	sw $s7, 16($sp)
li $s6, None
	sw $s6, z
	j end

end:
	li $v0, 10
	syscall