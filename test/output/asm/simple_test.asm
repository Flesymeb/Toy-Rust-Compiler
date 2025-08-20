.data
a: .word 0
b: .word 0
t0: .word 0
t1: .word 0
x: .word 0
y: .word 0

.text
lui $sp, 0x1004
j main

main:
li $s0, 42
	sw $s0, x
li $s1, 10
	sw $s1, y
lw $s2, x
li $s3, 5
	add $s4, $s2, $s3
	sw $s4, y
	j end

add:
	sw $ra, 4($sp)
lw $s0, 12($sp)
lw $s1, b
	add $s0, $s0, $s1
	add $v0, $s0, $zero
	lw $ra, 4($sp)
	jr $ra
	lw $ra, 4($sp)
	jr $ra

end:
	li $v0, 10
	syscall