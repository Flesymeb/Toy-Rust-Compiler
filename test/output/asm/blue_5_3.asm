.data

.text
lui $sp, 0x1004
j main

main:
L0:
	j L0
L1:
	j end

end:
	li $v0, 10
	syscall