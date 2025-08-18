.data
a: .word 0
b: .word 0
t0: .word 0
t1: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 10
	sw $s0, 8($sp)
li $s1, 20
	sw $s1, b
lw $s2, b
li $s3, 2
	mul $s4, $s2, $s3
lw $s5, 8($sp)
	add $s5, $s5, $s4
	sw $s5, 8($sp)
	j end
	j end

end:
	li $v0, 10
	syscall