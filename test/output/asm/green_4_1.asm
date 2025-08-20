.data
a: .word 0
t0: .word 0

.text
lui $sp, 0x1004
j main

main:
lw $s0, 0($sp)
li $s1, 0
	slt $s0, $s1, $s0
	beq $s0, $zero, L0
	li $v0, 1
	j end
	j L1
L0:
	li $v0, 0
	j end
L1:
	j end

end:
	li $v0, 10
	syscall