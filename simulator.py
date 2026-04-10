import sys
#original
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
        addr=self.unsigned_32(addr)
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
        elif f3==0x4 and f7==0x00: result=self.unsigned_32(v1 ^ v2) #xor
        elif f3==0x5 and f7==0x00: result=v1>>(v2 & 0x1F) #srl
        elif f3==0x5 and f7==0x20: result=self.unsigned_32(self.signed_32(v1)>>(v2 & 0x1F))#sra
        elif f3==0x6 and f7==0x00: result=self.unsigned_32(v1 | v2) #or
        elif f3==0x7 and f7==0x00: result=self.unsigned_32(v1 & v2) #and
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
        if opcode == 0x03:
            if f3 == 0x2:                                   # LW
                addr = self.unsigned_32(v1 + imm)
                self.checkMem(addr, 'load')
                val = self.lw(addr)
                if rd != 0:
                    self.registers[rd] = val
            else:
                raise SystemExit(
                    f"Error: unsupported load funct3={f3} at PC=0x{self.pc:08X}"
                )

        elif opcode == 0x13:
            shamt = (instr >> 20) & 0x1F   # used by shift instructions
            f7    = (instr >> 25) & 0x7F

            if   f3 == 0x0:                                 # ADDI
                result = self.unsigned_32(v1 + imm)
            elif f3 == 0x2:                                 # SLTI
                result = 1 if self.signed_32(v1) < imm else 0
            elif f3 == 0x3:                                 # SLTIU
                result = 1 if v1 < self.unsigned_32(imm) else 0
            elif f3 == 0x4:                                 # XORI
                result = self.unsigned_32(v1 ^ imm)
            elif f3 == 0x6:                                 # ORI
                result = self.unsigned_32(v1 | imm)
            elif f3 == 0x7:                                 # ANDI
                result = self.unsigned_32(v1 & imm)
            elif f3 == 0x1 and f7 == 0x00:                 # SLLI
                result = self.unsigned_32(v1 << shamt)
            elif f3 == 0x5 and f7 == 0x00:                 # SRLI
                result = v1 >> shamt
            elif f3 == 0x5 and f7 == 0x20:                 # SRAI
                result = self.unsigned_32(self.signed_32(v1) >> shamt)
            else:
                raise SystemExit(
                    f"Error: unknown I-type arith funct3={f3} funct7={f7} at PC=0x{self.pc:08X}"
                )

            if rd != 0:
                self.registers[rd] = result

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
#now s type
    def execute_s_type(self,decoded):
        rs1,rs2,f3=decoded['rs1'],decoded['rs2'],decoded['funct3']
        instr=decoded['instr']
        imm_lo=(instr>> 7) & 0x1F
        imm_hi=(instr>>25) & 0x7F
        imm=self.signExtending((imm_hi<<5) | imm_lo,12)
        v1=self.registers[rs1]
        v2=self.registers[rs2]
        if f3==0x2:
            addr=self.unsigned_32(v1+imm)
            self.checkMem(addr,'store')
            self.sw(addr,v2)
        else:
            raise SystemExit(f"Error: unknown S-type f3={f3} at PC=0x{self.pc:08X}")
        self.pc+=4
#the branch type code
    def execute_b_type(self,decoded):
        rs1,rs2,f3=decoded['rs1'],decoded['rs2'],decoded['funct3']
        instr=decoded['instr']
        imm_11  =(instr>> 7) & 0x1
        imm_4_1 =(instr>> 8) & 0xF
        imm_10_5=(instr>>25) & 0x3F
        imm_12  =(instr>>31) & 0x1
        imm=self.signExtending(
            (imm_12<<12) | (imm_11<<11) | (imm_10_5<<5) | (imm_4_1<<1),13
        )
        v1=self.registers[rs1]
        v2=self.registers[rs2]
        if   f3==0x0: taken=(v1==v2)
        elif f3==0x1: taken=(v1!=v2)
        elif f3==0x4: taken=self.signed_32(v1)< self.signed_32(v2)
        elif f3==0x5: taken=self.signed_32(v1)>=self.signed_32(v2)
        elif f3==0x6: taken=v1<v2
        elif f3==0x7: taken=v1>=v2
        else:
            raise SystemExit(f"Error: unknown B-type f3={f3} at PC=0x{self.pc:08X}")
        if taken:
            self.pc=self.unsigned_32(self.pc+imm)
        else:
            self.pc+=4
#u tyoe wala code
    def execute_u_type(self,decoded):
        rd=decoded['rd']
        instr=decoded['instr']
        imm=instr & 0xFFFFF000
        if decoded['opcode']==0x37:
            if rd!=0:
                self.registers[rd]=imm
        elif decoded['opcode']==0x17:
            if rd!=0:
                self.registers[rd]=self.unsigned_32(self.pc+imm)
        else:
            raise SystemExit(f"Error: unknown U-type opcode at PC=0x{self.pc:08X}")
        self.pc+=4
#the j type
    def execute_j_type(self,decoded):
        rd=decoded['rd']
        instr=decoded['instr']
        imm_19_12=(instr>>12) & 0xFF
        imm_11   =(instr>>20) & 0x1
        imm_10_1 =(instr>>21) & 0x3FF
        imm_20   =(instr>>31) & 0x1
        imm=self.signExtending((imm_20<<20) | (imm_19_12<<12) | (imm_11<<11) | (imm_10_1<<1),21)
        if rd!=0:
            self.registers[rd]=self.unsigned_32(self.pc+4)
        self.pc=self.unsigned_32(self.pc+imm)

#now starting the virtual halt function 
    def is_virtual_halt(self,instruction): 
        d=self.instructionDecoding(instruction)
        if d['opcode']!=0x63 or d['funct3']!=0x0:
            return False
        if d['rs1']!=0 or d['rs2']!=0:
            return False
        n=d['instr']
        return (((n>> 7) & 0x01)==0 and 
                ((n>> 8) & 0x0F)==0 and 
                ((n>>25) & 0x3F)==0 and 
                ((n>>31) & 0x01)==0)

    def record_state(self):
        parts=[f"0b{self.pc:032b}"]
        for i in range(32):
            val=0 if i==0 else self.registers[i]
            parts.append(f"0b{val:032b}")
        self.trace.append(" ".join(parts)+" ")

    def dump_memory(self):
        for i in range(32):
            addr=0x00010000+i*4
            value=self.data_memory[i]
            self.trace.append(f"0x{addr:08X}:0b{value:032b}")

    def execute(self,output_file):
        self._output_file=output_file
        halted=False
        #now onto the hardware part
        for _ in range(10_000_000):
            instr_index=self.pc//4
            if instr_index>=len(self.program_memory):
                sys.stderr.write(f"Error: PC 0x{self.pc:08X} is outside program memory.\n")
                self.terminate()
            instruction=self.program_memory[instr_index]
            if self.is_virtual_halt(instruction):
                self.record_state()
                halted=True
                break
            #binary to dictionary stuff
            decoded=self.instructionDecoding(instruction)
            opcode=decoded['opcode']
            #cchecking konsa function hai opcode ka
            if   opcode==0x33:               self.execute_r_type(decoded)
            elif opcode in (0x03,0x13,0x67): self.execute_i_type(decoded)
            elif opcode==0x23:               self.execute_s_type(decoded)
            elif opcode==0x63:               self.execute_b_type(decoded)
            elif opcode in (0x37,0x17):       self.execute_u_type(decoded)
            elif opcode==0x6F:               self.execute_j_type(decoded)
            else:
                sys.stderr.write(f"Error hai : unknown opcode 0b{opcode:07b} at PC=0x{self.pc:08X}\n")
                self.terminate()
                #x0 cant be changed from its hardwired to 0.
            self.registers[0]=0
            self.record_state()

        if halted:
            self.dump_memory()

    def write_trace(self,filename):
        try:
            with open(filename,'w') as f:
                for line in self.trace:
                    f.write(line+'\n')
        except IOError as e:
            raise SystemExit(f"Error writing trace to '{filename}': {e}")

def main():
    sim=RISCVSimulator()
    sim.programLoading(sys.argv[1])
    sim.execute(sys.argv[2])
    sim.write_trace(sys.argv[2])

if __name__=="__main__":
    main()
