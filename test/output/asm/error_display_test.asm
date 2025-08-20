.data
a: .word 0
c: .word 0
x: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 42
	sw $s0, 0($sp)
li $s1, 10
	sw $s1, 0($sp)
li $s2, 5
	sw $s2, 0($sp)
li $s3, 15
	sw $s3, c
li $s4, 100
	sw $s4, x
	j end

end:
	li $v0, 10
	syscall