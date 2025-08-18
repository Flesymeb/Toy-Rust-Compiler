.data
a: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 32
	sw $s0, 0($sp)
	j end

end:
	li $v0, 10
	syscall