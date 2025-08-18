.data

.text
lui $sp, 0x1004
j main

main:
	li $v0, 1
	j end
	j end

end:
	li $v0, 10
	syscall