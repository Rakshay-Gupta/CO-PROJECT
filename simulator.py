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
