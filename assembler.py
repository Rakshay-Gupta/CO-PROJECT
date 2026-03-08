registers = {
"zero":"00000","ra":"00001","sp":"00010","gp":"00011","tp":"00100",
"t0":"00101","t1":"00110","t2":"00111",
"s0":"01000","fp":"01000","s1":"01001",
"a0":"01010","a1":"01011","a2":"01100","a3":"01101",
"a4":"01110","a5":"01111","a6":"10000","a7":"10001",
"s2":"10010","s3":"10011","s4":"10100","s5":"10101",
"s6":"10110","s7":"10111","s8":"11000","s9":"11001",
"s10":"11010","s11":"11011",
"t3":"11100","t4":"11101","t5":"11110","t6":"11111"
}

R_Type = {
"add":("0000000","000","0110011"),
"sub":("0100000","000","0110011"),
"sll":("0000000","001","0110011"),
"slt":("0000000","010","0110011"),
"sltu":("0000000","011","0110011"),
"xor":("0000000","100","0110011"),
"srl":("0000000","101","0110011"),
"or":("0000000","110","0110011"),
"and":("0000000","111","0110011")
}

I_Type = {
"addi":("000","0010011"),
"sltiu":("011","0010011"),
"lw":("010","0000011"),
"jalr":("000","1100111")
}

S_Type = {
"sw":("010","0100011")
}

B_Type = {
"beq":("000","1100011"),
"bne":("001","1100011"),
"blt":("100","1100011"),
"bge":("101","1100011"),
"bltu":("110","1100011"),
"bgeu":("111","1100011")
}

U_Type = {
"lui":"0110111","auipc":"0010111"
}

J_Type = {
"jal":"1101111"
}

# it is converting decimal numbers to binary numbers
def decimaltobinary(num):
    if num==0:
        return "0"
    bin=""
    while(num>0):
        bin=str(num%2)+bin
        num=num//2

    return bin

# it is converting signed numbers to binary with fixed number of bits
def SignedBinary(val, bits):
    if val < 0:  # converts a negative number into two's complement representation
        val = (2**bits) + val
    sb = decimaltobinary(val) # calling function that converts decimal to binary
    if val >= 0:
        while len(sb) < bits: # ensuring that the binary number has exactly bits length  
            sb = '0' + sb
    return sb # final binary value is returned

# it is checking  whether a register name is valid
def regChecking(r, line):
    if r not in registers:
        print("Error in line no.",line,":register",r,"doesn't exist")
        exit() # stops the entire program

# checking whether an immediate value is within the allowed bit range
def immChecking(val, bits, line):
    Min = -(2**(bits-1))  # calculating min
    Max = (2**(bits-1))-1  # calculating max
    if (val > Max or val < Min):  # checking the range and print error if val is outside allowed range
        print("Error in line no.",line,":immediate value not in range")
        exit() # stops the entire program

# reading the assembly program file 
with open("file.txt",'r') as f:
    lines = f.readlines()

# first pass : to find labels

labels = {}  # dictionary to store label  with their addresses
pc = 0  

for line in lines:
    line = line.strip() # Removes spaces and newline characters

    if line == "": # skip empty lines
        continue
    if ':' in line: # checking for labels
        lab = line.split(':')[0].strip()   # extracting label names
        labels[lab] = pc # store label address
        line = line.split(':')[1].strip()   # removing label part from instruction
        if line == "":
            continue
    pc+=4 # incrementing program counter by 4 bytes

# second pass : for encode instructions

binary = []  # stores generated binary codes
halt = False   #  checks if halt instruction appears
line_no = 0   #  tracks the line numbers
pc = 0

for line in lines:
    line_no += 1
    line = line.strip()  # Removes spaces and newline characters

    if line == "":  # skip empty lines
        continue
    if ':' in line:
        line = line.split(':')  #Splitting labels and instruction and then removing labels 
        line = line[1].strip()
        if line == "":
            continue

# replacing punctuations 
line=line.replace(',',' ')
line= line.replace('(',' ')
line = line.replace(')',' ')

instructions = line.split()   # spiltting instructions so that each part becomes accessible
opcode = instructions[0] # extracting opcode


