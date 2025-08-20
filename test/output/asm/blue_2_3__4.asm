.data
a: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 1
	sw $s0, 0($sp)
li $s1, 2
	sw $s1, 0($sp)
li $s2, 3
	sw $s2, 0($sp)
	j end

end:
	li $v0, 10
	syscall