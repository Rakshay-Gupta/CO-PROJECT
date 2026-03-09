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
    if(val<0):  # converts a negative number into two's complement representation
        val = (2**bits) + val
    sb=decimaltobinary(val) # calling function that converts decimal to binary
    if(val>=0):
        while(len(sb) < bits): # ensuring that the binary number has exactly bits length  
            sb = '0' + sb
    return sb # final binary value is returned

# it is checking  whether a register name is valid
def regChecking(r, line):
    if r not in registers:
        print("Error in line no.",line,":register",r,"doesn't exist")
        exit() # stopcodes the entire program

# checking whether an immediate value is within the allowed bit range
def immChecking(val, bits, line):
    low=-(2**(bits-1))  # calculating min
    high = (2**(bits-1))-1  # calculating max
    if (val > high or val < low):  # checking the range and print error if val is outside allowed range
        print("Error in line no.",line,":immediate value not in range")
        exit() # stopcodes the entire program

# reading the assembly program file 
with open("file.txt",'r') as f:
    lines = f.readlines()

# first pass : to find labels

labels= {}  # dictionary to store label  with their addresses
pc =0  

for line in lines:
    line=line.strip() # Removes spaces and newline characters

    if(line==""): # skip empty lines
        continue
    if ':' in line: # checking for labels
        lab = line.split(':')[0].strip()   # extracting label names
        labels[lab] = pc # store label address
        line = line.split(':')[1].strip()   # removing label part from instructionsion
        if(line==""):
            continue
    pc+=4 # incrementing program counter by 4 bytes

# second pass : for encode instructionsions

binary=[]  # stores generated binary codes
halt=0   #  checks if halt instructionsion appears
line_no=0   #  tracks the line numbers
pc=0

for line in lines:
    line_no += 1
    line = line.strip()  # Removes spaces and newline characters

    if(line == ""):  # skip empty lines
        continue
    if ':' in line:
        line = line.split(':')  #Splitting labels and instructionsion and then removing labels 
        line = line[1].strip()
        if(line == ""):
            continue

    # replacing punctuations 
    line=line.replace(',',' ')
    line= line.replace('(',' ')
    line = line.replace(')',' ')
    
    instructions = line.split()   # spiltting instructionsions so that each part becomes accessible
    operation = instructions[0] # extracting operations to be implemented on operands

    if operation in R_Type:          

        rd=instructions[1]     # location where to store the final value after operation on both rs1 and rs2 
        rs1=instructions[2]    # assigning operands from instruction
        rs2=instructions[3]  

        regChecking(rd,line_no)    # checking error in rd whether it is in valid range or not
        regChecking(rs1,line_no)
        regChecking(rs2,line_no)

        funct7,funct3,opcode=R_Type[operation]    # to get values of funct7 and funct3 for particular value of opcode in R-Type

        code = funct7 + registers[rs2] + registers[rs1] + funct3 + registers[rd] + opcode # converting R-Type instructions into 32-bit binary

    elif operation in I_Type:

        if(operation=="lw"):     # need to check whether operation is lw or jalr  or something else because for these operations 
                                   # position for immediate is different in some instructions
            rd=instructions[1]
            imm=int(instructions[2])
            rs1=instructions[3]
        elif(operation=="jalr"):
            rd=instructions[1]
            if(instructions[2]=="zero"):      # if operand is zero instead of absolute zero then convert it to absolute zero                
                instructions[2]=0         # as zero is hard wired to 0
            imm=int(instructions[2])
            rs1=instructions[3]
        else:
            rd = instructions[1]
            rs1 = instructions[2]
            imm = int(instructions[3])

        regChecking(rd,line_no)
        regChecking(rs1,line_no)     
        regChecking(imm,12,line_no)     # checking error in immediate value whether it is in required bits or not

        funct3,opcode=I_Type[operation]   # To get values of funct3 for particular value of opcode in R-Type


        code = SignedBinary(imm,12)+registers[rs1]+funct3+registers[rd]+opcode  # converting I-Type instructions into 32-bit binary 

    elif operation in S_Type:

        rs2=instructions[1]
        imm=int(instructions[2])
        rs1=instructions[3]

        regChecking(rs1,line_no)
        regChecking(rs2,line_no)     # checking error in rs2 whether it is in required bits or not
        regChecking(imm,12,line_no)

        funct3,opcode=S_Type[operation]

        imm_bin=SignedBinary(imm,12)   # to further break value of immediate into 7 and 5 bits

        code = imm_bin[:7]+registers[rs2]+registers[rs1]+funct3+imm_bin[7:]+opcode   # converting S-Type instructions into 32-bit binary 

    elif operation in B_Type:

        rs1=instructions[1]
        rs2=instructions[2]
        label=instructions[3].strip()   # to remove white spcae from label so as to avoid errors

        regChecking(rs1,line_no)
        regChecking(rs2,line_no)

        if label.lstrip("-").isdigit():   # if number is given instead of string(label) then it means it is offset 
                                            # to jump PC by that value after neglecting -ve sign
            offset=int(label)

        else:
            if label not in labels:     # to handle error if that label(string) does not exist in list of labels then it should print error
                print("Error in line",line_no,": label is not defined")
                exit()          #  and immediately exit the code from that point and stop the program

            offset = labels[label] - pc    # to get the required no. of bytes to jump from that PC to wanted location(label)

        immChecking(offset,12,line_no)

        imm=SignedBinary(offset,13)   # to further break value of immediate into required no. of bits to make 32-bits binary for
                                               # B-Type instruction in its semantic
        funct3,opcode=B_Type[operation]

        code = imm[0]+imm[2:8]+registers[rs2]+registers[rs1]+funct3+imm[8:12]+imm[1]+opcode   # converting B-Type instructions into 32-bit binary after after 
                                                                                                # combining the bits obtained by splitting bits(immediate)

    