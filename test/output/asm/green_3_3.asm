.data

.text
lui $sp, 0x1004
j main

foo:
	sw $ra, 4($sp)
	lw $ra, 4($sp)
	jr $ra

main:
	jal foo
	add $s0, $v0, $zero
	j end

end:
	li $v0, 10
	syscall