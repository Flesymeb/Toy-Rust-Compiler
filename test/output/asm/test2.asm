.data

.text
lui $sp, 0x1004
j main

end:
	li $v0, 10
	syscall