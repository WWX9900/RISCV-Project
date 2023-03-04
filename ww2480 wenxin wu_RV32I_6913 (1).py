#wenxin wu ww2480
import os
import argparse
import copy

# memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.
MemSize = 1000

# source: https://cysecguide.blogspot.com/2017/12/converting-binarydecimal-of-twos.html
def signedbinStrtoDec(bString):
    if bString[0] == '0':
        return int(bString, 2)
    else:
        return -1 * (int(''.join('1' if x == '0' else '0' for x in bString), 2) + 1)

def binStrtoInt(bString):
    return int(bString, 2)


def binStrtoHex(bString):
    return hex(binStrtoInt(bString))


def parseOp(inst):
    return inst[25:(31+1)]

# R-type parser


def parseRd(inst):
    return inst[20:(24+1)]


def parseRs1(inst):
    return inst[12:(16+1)]


def parseRs2(inst):
    return inst[7:(11+1)]


def parseFuct3(inst):
    return inst[17:(19+1)]


def parseFuct7(inst):
    return inst[0:(6+1)]

# I-type parse


def parseImmI(inst):
    return inst[0] * 20 + inst[0:(11+1)]

# S-type parse


def parseImmS(inst):
    return parseFuct7(inst) + parseRd(inst)

# SB-type parse


def parseImmSB(inst) -> str:
    return inst[0] + inst[24] + inst[1:6+1] + inst[20:(23+1)] + "0"

# UJ-type parse


def parseImmUJ(inst):
    return inst[0] + inst[12:(19+1)] + inst[12] + inst[1:(10+1)] + "0"


class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name

        with open(ioDir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress: int) -> str:

        instbin = ""
        for i in range(0, 4, 1):
            instbin += self.IMem[ReadAddress + i]

        return instbin

class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]
        length_off = MemSize - len(self.DMem)
        if length_off > 0:
            ext_list = length_off * ["0"*8]
            self.DMem.extend(ext_list)

    def readData(self, ReadAddress: int) -> str:
        # read data memory
        # return 32 bit hex val
        databin = ""
        for i in range(0, 4, 1):
            databin += self.DMem[ReadAddress + i]
        # databin 32 str convert int decimal 2's complement
        return databin

    def writeDataMem(self, Address: int, WriteData: int):

        self.DMem[Address] = format(int(WriteData,base=16), "08b")
        
        return

    def outputDataMem(self):
        resPath = self.ioDir + "/" + self.id + "_DMEMResult.txt"
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])


class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = [0x0 for i in range(32)]

    def readRF(self, Reg_addr: int) -> int:
        # self.Registers[Reg_addr] str convert to int 2's com
        return self.Registers[Reg_addr]

    def writeRF(self, Reg_addr: int, Wrt_reg_data: hex):
        Wrt_reg_data = Wrt_reg_data & 0xffffffff
        if Reg_addr == 0:
            return
        self.Registers[Reg_addr] = Wrt_reg_data
        return


    def outputRF(self, cycle):
        op = ["-"*70+"\n", "State of RF after executing cycle:" +
              str(cycle) + "\n"]
        op.extend([bin(val)[2:].zfill(32)+"\n" for val in self.Registers])
        if(cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)


class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0}
        self.ID = {"nop": False, "Instr": 0}
        self.EX = {"JAL_rd": 0,"alu_to_reg": 0, "nop": False, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False, "rd_mem": 0,
                   "wrt_mem": 0, "alu_op": "", "wrt_enable": 0}
        self.MEM = {"alu_to_reg": 0, "nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0, "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0,
                   "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}


class Core(object):
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem


class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "/SS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_SS.txt"
        self.state.IF["PC"] = 0

    def step(self):
        # print("IF NOP: " + str(self.state.IF["nop"]))
        instr = self.ext_imem.readInstr(self.state.IF["PC"])
        if instr == None:
                self.state.IF["nop"] = True
                self.state.ID["nop"] = True
        if not self.state.IF["nop"]:
            # print('TEST TO WORK')
            self.nextState.IF["PC"] = self.state.IF["PC"] + 4
            opcode = parseOp(instr)
            print(opcode)
            if opcode == "0110011":  # R-type
                print("is r-type")
                funct7 = parseFuct7(instr)
                rs1 = parseRs1(instr)
                rs2 = parseRs2(instr)
                funct3 = parseFuct3(instr)
                rd = binStrtoInt(parseRd(instr))
                rs1_value = self.myRF.readRF(
                    binStrtoInt(rs1))
                rs2_value = self.myRF.readRF(
                    binStrtoInt(rs2))

                # EXECUTE
                if funct7 == "0100000":  # SUB
                    var1 = rs1_value - rs2_value

                    self.myRF.writeRF(rd,var1)
                    # self.myRF.writeRF(rd, rs1_value - rs2_value)
                elif funct3 == "000":  # ADD

                    var1 = rs1_value + rs2_value

                    self.myRF.writeRF(rd,var1)

                elif funct3 == "111":  # AND
                    var1 = rs1_value & rs2_value

                    self.myRF.writeRF(rd,var1)


                elif funct3 == "110":  # OR
                    var1 = rs1_value | rs2_value
                    # var1 = bin(var1)[2:].zfill(32)
                    self.myRF.writeRF(rd,var1)


                elif funct3 == "100":  # XOR
                    var1 = rs1_value^rs2_value
                    # var1 = bin(var1)[2:].zfill(32)
                    self.myRF.writeRF(rd,var1)
                else:
                    self.nextState.IF["nop"] = True
                    print("Invalid operation for R-type")
            elif opcode == "0010011":  # I-type
                print("is I-type")
                imm = parseImmI(instr)
                # print(imm)
                immi_value = signedbinStrtoDec(imm)
                rs1 = parseRs1(instr)
                rs1_value = self.myRF.readRF(binStrtoInt(rs1))
                funct3 = parseFuct3(instr)
                rd = binStrtoInt(parseRd(instr))

                # EXECUTE
                if funct3 == "000":  # ADDI
                    print("rs1: " + str(rs1_value))
                    print("immi_value: " + str(immi_value))

                    print("SO TEH VALEU ISIS：%s" %(immi_value))
                    
                    print("SO TEH VALEU ISIS：%s" %type(immi_value))
                    print("SO TEH VALEU OF RS1 ISIS：%s"%(rs1_value))
                    print("SO TEH VALEU ISIS：%s" %type(rs1_value))
                    var1 = rs1_value + immi_value
                    # var1 = bin(var1)[2:].zfill(32)
                    self.myRF.writeRF(rd,var1)
                    # self.myRF.writeRF(rd, rs1_value + immi_value)
                elif funct3 == "100":  # XORI
                    var1 = rs1_value^immi_value
                    # var1 = bin(var1)[2:].zfill(32)
                    self.myRF.writeRF(rd,var1)
                    # self.myRF.writeRF(rd, rs1_value ^ immi_value)
                elif funct3 == "110":  # ORI
                    var1 = rs1_value | immi_value
                    # var1 = bin(var1)[2:].zfill(32)
                    self.myRF.writeRF(rd,var1)
                    # self.myRF.writeRF(rd, rs1_value | immi_value)
                elif funct3 == "111":  # ANDI
                    var1 = rs1_value & immi_value
                    # var1 = bin(var1)[2:].zfill(32)
                    self.myRF.writeRF(rd,var1)
                    # self.myRF.writeRF(rd, rs1_value & immi_value)
                else:
                    self.nextState.IF["nop"] = True
                    print("Invalid operation for I-type")
            elif opcode == "1100011":  # SB-type
                print("is SB type")
                print(instr)
                rs1 = parseRs1(instr)
                rs2 = parseRs2(instr)
                funct3 = parseFuct3(instr)
                rs1_value = self.myRF.readRF(binStrtoInt(rs1))
                rs2_value = self.myRF.readRF(binStrtoInt(rs2))
                imm = signedbinStrtoDec(parseImmSB(instr))
                
                if funct3 == "000":  # BEQ
                    if rs1_value == rs2_value:
                        self.nextState.IF["PC"] += imm - 4
                elif funct3 == "001":  # BNE
                    if rs1_value != rs2_value:
                        self.nextState.IF["PC"] += imm - 4
                else:
                    self.nextState.IF["nop"] = True
                    print("Invalid operation for SB-type")

            elif opcode == "1101111":  # UJ-type: JAL instruction
                print("is JAL instruction")
                rd = binStrtoInt(parseRd(instr))
                imm = signedbinStrtoDec(parseImmUJ(instr))
                self.myRF.writeRF(rd, self.state.IF["PC"] + 4) #rd = PC + 4
                self.nextState.IF["PC"] += imm - 4                   #PC = PC + sign_ext(imm)
            elif opcode == "0000011":  # I-type: LW instruction
                print("is LW instruction")
                if not parseFuct3(instr) == "000":
                    # Invalid funct3 for I-type: LW
                    self.nextState.IF["nop"] = True
                    print("Invalid funct3 for LW")
                else:
                    # Load 32-bit value at memory address [rs1 + signPext(imm)] and store it in rd.
                    rs1 = parseRs1(instr)
                    rs1_value = self.myRF.readRF(binStrtoInt(rs1))
                    rd = binStrtoInt(parseRd(instr))
                    imm = signedbinStrtoDec(parseImmI(instr))
                    # need to read four times
                    rs1_offset_value_str = dmem_ss.readData(rs1_value + imm)
                    rs1_offset_value = int(rs1_offset_value_str,2)
                    self.myRF.writeRF(rd, rs1_offset_value) #rd = mem[rs1 + sign_ext(imm)][31:0]
            elif opcode == "0100011":  # S-type: SW instruction
                print("is SW instruction")
                if not parseFuct3(instr) == "010":
                    # Invalid funct3 for S-type: SW
                    print("Invalid funct3 for SW")
                    self.nextState.IF["nop"] = True
                else:
                    # Store the 32 bits of rs2 to memory address [rs1 value + sign_ext(imm)].
                    rs1 = parseRs1(instr)
                    rs2 = parseRs2(instr)
                    rs1_value = self.myRF.readRF(binStrtoInt(rs1))
                    rs2_value = self.myRF.readRF(binStrtoInt(rs2))
                    imm = signedbinStrtoDec(parseImmS(instr))

                    rs2_value = bin(rs2_value)[2:].zfill(32)
                    for i in range(3, -1, -1):
                        dmem_ss.writeDataMem(rs1_value + imm + 3, binStrtoHex(rs2_value[(3-i)*8:(4-i)*8])) #data[rs1 + sign_ext(imm)][31:0] = rs2
            elif opcode == "1111111":  # Halt
                self.nextState.IF["nop"] = True
            else:
                print("Invalid opcode")
                self.nextState.IF["nop"] = True

        if self.state.IF["nop"]:
            self.halted = True

        self.myRF.outputRF(self.cycle)  # dump RF
        # print states after executing cycle 0, cycle 1, cycle 2 ...
        self.printState(self.nextState, self.cycle)
        self.state = self.nextState
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n",
                      "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")

        if(cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "/FS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_FS.txt"

        # Initialization for states' nop to be true
        self.state.ID["nop"] = True
        self.state.EX["nop"] = True
        self.state.MEM["nop"] = True
        self.state.WB["nop"] = True

    def step(self):
        # Your implementation
        # --------------------- WB stage --------------------- #
        if (self.state.WB["nop"] == False):
            if (self.state.WB["wrt_enable"] == 1):
                self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], self.state.WB["Wrt_data"])

        # --------------------- MEM stage --------------------- #
        if (self.state.MEM["nop"] == False):
            self.nextState.WB["nop"] = self.state.MEM["nop"]

            self.nextState.WB["Rs"] = self.state.MEM["Rs"]
            self.nextState.WB["Rt"] = self.state.MEM["Rt"]
            self.nextState.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]
            self.nextState.WB["wrt_enable"] = self.state.MEM["wrt_enable"]
            if (self.state.MEM["rd_mem"] == 1): # lw instruction
                self.nextState.WB["Wrt_data"] = dmem_fs.readData(self.state.MEM["ALUresult"])
            elif (self.state.MEM["wrt_mem"] == 1): # sw instruction
                dmem_fs.writeDataMem(self.state.MEM["ALUresult"], self.state.MEM["Store_data"])
                self.nextState.WB["nop"] = True
            elif self.state.MEM["alu_to_reg"] == 1:
                self.nextState.WB["Wrt_data"] = self.state.MEM["ALUresult"]
            
            # MEM stage forward
            if self.nextState.WB["wrt_enable"] == 1 and self.nextState.WB["Wrt_reg_addr"] != 0 and\
               not(self.nextState.MEM["alu_to_reg"] == 1 and self.nextState.MEM["Wrt_reg_addr"] != 0 and\
                (self.nextState.MEM["Wrt_reg_addr"]==self.nextState.EX["Rs"])) and \
                    self.nextState.WB["Wrt_reg_addr"] == self.nextState.EX["Rs"]:
                        self.nextState.EX["Read_data1"] = self.nextState.WB["Wrt_data"]
            
            elif self.nextState.WB["wrt_enable"] == 1 and self.nextState.WB["Wrt_reg_addr"] != 0 and\
               not(self.nextState.MEM["alu_to_reg"] == 1 and self.nextState.MEM["Wrt_reg_addr"] != 0 and\
                (self.nextState.MEM["Wrt_reg_addr"]==self.nextState.EX["Rt"])) and \
                    self.nextState.WB["Wrt_reg_addr"] == self.nextState.EX["Rt"]:
                        self.nextState.EX["Read_data2"] = self.nextState.WB["Wrt_data"]

        # --------------------- EX stage --------------------- #
        if (self.state.EX["nop"] == False):
            self.nextState.MEM["nop"] = self.state.EX["nop"]

            self.nextState.MEM["Rs"] = self.state.EX["Rs"]
            self.nextState.MEM["Rt"] = self.state.EX["Rt"]
            self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
            self.nextState.MEM["rd_mem"] = self.state.EX["rd_mem"]
            self.nextState.MEM["wrt_mem"] = self.state.EX["wrt_mem"]
            self.nextState.MEM["wrt_enable"] = self.state.EX["wrt_enable"]
            self.nextState.MEM["alu_to_reg"] = self.state.EX["alu_to_reg"] 
            # sw
            if self.state.EX["wrt_mem"] == 1:
                self.nextState.MEM["Store_data"] = self.state.EX["Read_data2"]
            rs1 = self.state.EX["Read_data1"]
            if (self.state.EX["is_I_type"]): # I-type, use Imm instead of Read_data2
                rs2 = self.state.EX["Imm"]
            else:
                rs2 = self.state.EX["Read_data2"]

            if (self.state.EX["alu_op"] == "add"):
                self.nextState.MEM["ALUresult"] = rs1 + rs2
            elif self.state.EX["alu_op"] == "sub":
                self.nextState.MEM["ALUresult"] = rs1 - rs2
            elif self.state.EX["alu_op"] == "xor":
                self.nextState.MEM["ALUresult"] = rs1 ^ rs2
            elif self.state.EX["alu_op"] == "or":
                self.nextState.MEM["ALUresult"] = rs1 | rs2
            elif self.state.EX["alu_op"] == "and":
                self.nextState.MEM["ALUresult"] = rs1 & rs2

            # Load use stall
            if self.nextState.MEM["rd_mem"] == 1 and \
                (self.nextState.MEM["Wrt_reg_addr"]==self.nextState.EX["Rs"]) or\
                    (self.nextState.MEM["Wrt_reg_addr"]==self.state.EX["Rt"]):
                    self.nextState.IF["PC"] = self.state.IF["PC"]
                    self.nextState.ID["Instr"] = self.state.ID["Instr"]
                    self.nextState.EX["nop"] = True
                    print("Load use stall")
            # EX state forward
            elif self.nextState.MEM["alu_to_reg"] == 1 and self.nextState.MEM["Wrt_reg_addr"] != 0 and\
                (self.nextState.MEM["Wrt_reg_addr"]==self.nextState.EX["Rs"]):
                self.nextState.EX["Read_data1"] = self.nextState.MEM["ALUresult"]
                print("EX state forward")
            elif self.nextState.MEM["wrt_enable"] == 1 and self.nextState.MEM["Wrt_reg_addr"] != 0 and\
                (self.nextState.MEM["Wrt_reg_addr"]==self.nextState.EX["Rt"]):
                self.nextState.EX["Read_data2"] = self.nextState.MEM["ALUresult"]
                print("EX state forward")
        # --------------------- ID stage --------------------- #
        if (self.state.ID["nop"] == False):
            self.nextState.EX["nop"] = self.state.ID["nop"]
            instr = self.state.ID["Instr"]
            opcode = parseOp(instr)
            print(opcode)
            if opcode == "0110011":  # R-type
                print("is r-type")
                funct7 = parseFuct7(instr)
                self.nextState.EX["Rs"] = parseRs1(instr)
                self.nextState.EX["Rt"] = parseRs2(instr)
                funct3 = parseFuct3(instr)
                self.nextState.EX["Wrt_reg_addr"] = binStrtoInt(parseRd(instr))
                self.nextState.EX["Read_data1"] = self.myRF.readRF(
                    binStrtoInt(rs1))
                self.nextState.EX["Read_data2"] = self.myRF.readRF(
                    binStrtoInt(rs2))
                # control signal
                self.nextState.EX["rd_mem"] = 0
                self.nextState.EX["wrt_mem"] = 0
                self.nextState.EX["wrt_enable"] = 1
                self.nextState.EX["alu_to_reg"] = 1
                # EXECUTE
                if funct7 == "0100000":  # SUB
                    # var1 = rs1_value - rs2_value
                    self.nextState.EX["alu_op"] = "sub"
                elif funct3 == "000":  # ADD
                    self.nextState.EX["alu_op"] = "add"
                    

                elif funct3 == "111":  # AND
                    self.nextState.EX["alu_op"] = "and"
                    

                elif funct3 == "110":  # OR
                     self.nextState.EX["alu_op"] = "or"
                    

                elif funct3 == "100":  # XOR
                    self.nextState.EX["alu_op"] = "xor"
                    
                else:
                    self.nextState.IF["nop"] = True
                    print("Invalid operation for R-type")
            elif opcode == "0010011":  # I-type
                print("is I-type")
                imm = parseImmI(instr)
                # print(imm)
                self.nextState.EX["Imm"] = signedbinStrtoDec(imm)
                self.nextState.EX["Rs"] = parseRs1(instr)
                self.nextState.EX["Read_data1"] = self.myRF.readRF(binStrtoInt(rs1))
                funct3 = parseFuct3(instr)
                self.nextState.EX["Wrt_reg_addr"] = binStrtoInt(parseRd(instr))
                # control signal
                self.nextState.EX["rd_mem"] = 0
                self.nextState.EX["wrt_mem"] = 0
                self.nextState.EX["wrt_enable"] = 1
                self.nextState.EX["alu_to_reg"] = 1
                # EXECUTE
                if funct3 == "000":  # ADDI
                    self.nextState.EX["alu_op"] = "add"
                    

                elif funct3 == "111":  # ANDI
                    self.nextState.EX["alu_op"] = "and"
                    

                elif funct3 == "110":  # ORI
                     self.nextState.EX["alu_op"] = "or"
                    

                elif funct3 == "100":  # XORI
                    self.nextState.EX["alu_op"] = "xor"
                else:
                    self.nextState.IF["nop"] = True
                    print("Invalid operation for I-type")

            elif opcode == "1100011":  # SB-type
                print("is SB type")
                print(instr)
                self.nextState.EX["Rs"] = parseRs1(instr)
                self.nextState.EX["Rt"] = parseRs2(instr)
                funct3 = parseFuct3(instr)
                self.nextState.EX["Read_data1"] = self.myRF.readRF(binStrtoInt(rs1))
                self.nextState.EX["Read_data2"] = self.myRF.readRF(binStrtoInt(rs2))
                imm = signedbinStrtoDec(parseImmSB(instr))
                # control signal
                self.nextState.EX["rd_mem"] = 0
                self.nextState.EX["wrt_mem"] = 0
                self.nextState.EX["wrt_enable"] = 0
                self.nextState.EX["alu_to_reg"] = 0
                self.nextState.EX["nop"] = True
                if funct3 == "000":  # BEQ
                    if self.nextState.EX["Rs"] == self.nextState.EX["Rt"]:
                        self.nextState.IF["PC"] = self.state.IF["PC"]+imm - 4
                        self.nextState.ID["nop"] = True
                elif funct3 == "001":  # BNE
                    if self.nextState.EX["Rs"] != self.nextState.EX["Rt"]:
                        self.nextState.IF["PC"] = self.state.IF["PC"]+imm - 4
                        self.nextState.ID["nop"] = True
                else:
                    self.nextState.IF["nop"] = True
                    print("Invalid operation for SB-type")

            elif opcode == "1101111":  # UJ-type: JAL instruction
                print("is JAL instruction")
                self.nextState.EX["Wrt_reg_addr"] = binStrtoInt(parseRd(instr))
                imm = signedbinStrtoDec(parseImmUJ(instr))
                # self.myRF.writeRF(rd, self.state.IF["PC"] + 4) #rd = PC + 4
                self.nextState.IF["PC"] = self.state.IF["PC"]+imm - 4                 #PC = PC + sign_ext(imm)
                self.nextState.EX["Read_data1"] =  self.state.IF["PC"] - 4
                self.nextState.EX["Read_data2"] = 4
                # control signal
                self.nextState.EX["rd_mem"] = 0
                self.nextState.EX["wrt_mem"] = 0
                self.nextState.EX["wrt_enable"] = 1
                self.nextState.EX["alu_to_reg"] = 1
                self.nextState.ID["nop"] = True
            elif opcode == "0000011":  # I-type: LW instruction
                print("is LW instruction")
                if not parseFuct3(instr) == "000":
                    # Invalid funct3 for I-type: LW
                    self.nextState.IF["nop"] = True
                    print("Invalid funct3 for LW")
                else:
                    # Load 32-bit value at memory address [rs1 + signPext(imm)] and store it in rd.
                    self.nextState.EX["Rs"] = parseRs1(instr)
                    self.nextState.EX["Read_data1"] = self.myRF.readRF(binStrtoInt(rs1))
                    self.nextState.EX["Wrt_reg_addr"] = binStrtoInt(parseRd(instr))
                    self.nextState.EX["Imm"] = signedbinStrtoDec(parseImmI(instr))
                     # control signal
                    self.nextState.EX["rd_mem"] = 1
                    self.nextState.EX["wrt_mem"] = 0
                    self.nextState.EX["wrt_enable"] = 1
                    self.nextState.EX["alu_to_reg"] = 0

            elif opcode == "0100011":  # S-type: SW instruction
                print("is SW instruction")
                if not parseFuct3(instr) == "010":
                    # Invalid funct3 for S-type: SW
                    print("Invalid funct3 for SW")
                    self.nextState.IF["nop"] = True
                else:
                    # Store the 32 bits of rs2 to memory address [rs1 value + sign_ext(imm)].
                    self.nextState.EX["Rs"] = parseRs1(instr)
                    self.nextState.EX["Rt"] = parseRs2(instr)
                    self.nextState.EX["Read_data1"] = self.myRF.readRF(binStrtoInt(rs1))
                    self.nextState.EX["Read_data2"] = self.myRF.readRF(binStrtoInt(rs2))
                    self.nextState.EX["Imm"] = signedbinStrtoDec(parseImmS(instr))
                     # control signal
                    self.nextState.EX["rd_mem"] = 0
                    self.nextState.EX["wrt_mem"] = 1
                    self.nextState.EX["wrt_enable"] = 0
                    self.nextState.EX["alu_to_reg"] = 0
                    self.nextState.EX["nop"] = True

            elif opcode == "1111111":  # Halt
                self.nextState.IF["nop"] = True
                self.nextState.ID["nop"] = True
                self.nextState.EX["nop"] = True
                self.state.IF["nop"] = True
                self.state.ID["nop"] = True
                self.state.EX["nop"] = True
            else:
                print("Invalid opcode")
                self.nextState.IF["nop"] = True
        # --------------------- IF stage --------------------- #
        if (self.state.IF["nop"] == False):
            self.nextState.ID["nop"] = self.state.IF["nop"]

            self.nextState.ID["Instr"] = self.ext_imem.readInstr(self.state.IF["PC"])
            self.nextState.IF["PC"] += 4

        self.halted = True
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True

        self.myRF.outputRF(self.cycle)  # dump RF
        # print states after executing cycle 0, cycle 1, cycle 2 ...
        self.printState(self.nextState, self.cycle)
        self.state = copy.deepcopy(self.nextState)
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n",
                      "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) +
                          "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) +
                          "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) +
                          "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) +
                          "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) +
                          "\n" for key, val in state.WB.items()])

        if(cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)
        # --------------------- ID stage ---------------------
        
            
if __name__ == "__main__":

    # parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str,
                        help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)
    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while(True):
        if not ssCore.halted:
            ssCore.step()

        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break

    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()
