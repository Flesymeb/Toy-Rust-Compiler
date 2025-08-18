.data

.text
lui $sp, 0x1004
j main

main:
	j end

end:
	li $v0, 10
	syscall