import sys

class RISCVSimulator:
    def __init__(self): # initializing the simulator
        self.registers=[0]*32
        self.pc=0
        self.data_memory=[0]*32 # simulated data memory
        self.stack_memory=[0]*32 # seperate stack memory
        self.program_memory=[] # stores instructions
        self.registers[2]=0x0000017C
        self.trace=[] #stores execution history for output
        self._output_file=None

# converts smaller signed no. into 32 bit signed no.
    def signExtending(self,value,bits): 
        signedBit = 2 ** (bits-1)
        if value & signedBit: # checking if no. is negative
            value = value - (2 ** bits)
        return value

# converts a 32 bit number into signed representation
    def signed_32(self,value): 
        if value & 0x80000000:
            return value-0x100000000
        return value

# keeps value with 32 bit range
    def unsigned_32(self,value): 
        return value & 0xFFFFFFFF

# reads instructions from file
    def programLoading(self,filename): 
        try:
            with open(filename,'r') as f:
                for line in f:
                    line=line.strip() # removes spaces and newlines
                    if line:
                        if len(line)!=32:
                            raise SystemExit(f"Error: invalid instruction length: '{line}'")
                        self.program_memory.append(line)
        except FileNotFoundError:
            raise SystemExit(f"Error: file not found: {filename}")

# converts binary string to integers and extracts instructions using bit masking
    def instructionDecoding(self,instruction): #breaks instructions into fields
        instr=int(instruction,2)
        opcode = instr & 0x7F
        rd = (instr>> 7) & 0x1F
        funct3 = (instr>>12) & 0x07
        rs1 = (instr>>15) & 0x1F
        rs2 = (instr>>20) & 0x1F
        funct7 = (instr>>25) & 0x7F
        return {
            'instr': instr,
            'opcode': opcode,
            'rd': rd,
            'funct3': funct3,
            'rs1': rs1,
            'rs2': rs2,
            'funct7': funct7
        }

# Ensures memory operations are valid and safe
    def checkMem(self,addr,op): # validate memory access
        addr=self.unsigned_32(addr)
        if addr%4 != 0:
            sys.stderr.write(f"Error: unaligned memory {op} at address 0x{addr:08X} (PC=0x{self.pc:08X})\n")
            self.terminate()
        memData=0x00010000<=addr<=0x0001007C
        memStack=0x00000100<=addr<=0x0000017F
        if not (memData or memStack):
            sys.stderr.write(f"Error: invalid memory {op} at address 0x{addr:08X} (PC=0x{self.pc:08X})\n")
            self.terminate()

# writes current trace to file and stops program execution
    def terminate(self):
        self.write_trace(self._output_file)
        sys.exit(1)

# Loads a 32 bit word from memory
    def lw(self,addr):
        addr=self.to_unsigned_32(addr)
        if 0x00010000<=addr<=0x0001007C:
            return self.data_memory[(addr-0x00010000)//4]
        if 0x00000100<=addr<=0x0000017F:
            return self.stack_memory[(addr-0x00000100)//4]
        return 0
    def sw(self,addr,value):
        addr =self.unsigned_32(addr) #making addr 32 bit
        value=self.unsigned_32(value) #making value 32 bit 
        if 0x00010000<=addr<=0x0001007C: # checking if address within data memory range 
            self.data_memory[(addr-0x00010000)//4]=value
        elif 0x00000100<=addr<=0x0000017F: # checking if address within stack memory range 
            self.stack_memory[(addr-0x00000100)//4]=value

    def execute_r_type(self,decoded):
        rs1,rs2,rd=decoded['rs1'],decoded['rs2'],decoded['rd']
        f3,f7=decoded['funct3'],decoded['funct7']
        v1=self.registers[rs1]
        v2=self.registers[rs2]
        #operations 
        if   f3==0x0 and f7==0x00: result=self.unsigned_32(v1+v2) #add
        elif f3==0x0 and f7==0x20: result=self.unsigned_32(v1-v2) #sub 
        elif f3==0x1 and f7==0x00: result=self.unsigned_32(v1<<(v2 & 0x1F)) #sll
        elif f3==0x2 and f7==0x00: result=1 if self.signed_32(v1)<self.signed_32(v2) else 0 #slt
        elif f3==0x3 and f7==0x00: result=1 if v1<v2 else 0 #sltu
        elif f3==0x4 and f7==0x00: result=v1 ^ v2 #xor
        elif f3==0x5 and f7==0x00: result=v1>>(v2 & 0x1F) #srl
        elif f3==0x5 and f7==0x20: result=self.unsigned_32(self.signed_32(v1)>>(v2 & 0x1F))#sra
        elif f3==0x6 and f7==0x00: result=v1 | v2 #or
        elif f3==0x7 and f7==0x00: result=v1 & v2 #and
        else:
            raise SystemExit(f"Error: unknown R-type f3={f3} f7={f7} at PC=0x{self.pc:08X}")
        
        if rd!=0:
            self.registers[rd]=result
        self.pc+=4 #pc increment 

    def execute_i_type(self,decoded):
        rs1,rd,f3=decoded['rs1'],decoded['rd'],decoded['funct3']
        instr=decoded['instr']
        imm=self.signExtending((instr>>20) & 0xFFF,12)  # extending the last 12 bits 
        v1=self.registers[rs1]
        opcode=decoded['opcode']
        if opcode==0x03: #load instructions 
            if f3==0x2:
                addr=self.unsigned_32(v1+imm)
                self.checkMem(addr,'load')
                val=self.lw(addr)
                if rd!=0:
                    self.registers[rd]=val

        elif opcode==0x13: #arithmetic immediates
            if f3==0x0: 
                result=self.unsigned_32(v1+imm)
                if rd!=0:
                    self.registers[rd]=result
            elif f3==0x3:
                result=1 if v1<self.unsigned_32(imm) else 0
                if rd!=0:
                    self.registers[rd]=result
       
        elif opcode==0x67:#jalr
            if f3==0x0:
                ret_addr=self.unsigned_32(self.pc+4)
                target=self.unsigned_32(v1+imm) & 0xFFFFFFFE
                if rd!=0:
                    self.registers[rd]=ret_addr
                self.pc=target
                return
        else:
            raise SystemExit(f"Error: unknown I-type opcode 0x{opcode:02X} at PC=0x{self.pc:08X}")
        self.pc+=4
