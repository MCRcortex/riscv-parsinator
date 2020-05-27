import subprocess
#clang-10 -g -S -target riscv32 -march=rv32im -mabi=ilp32 -O2 -fno-asynchronous-unwind-tables -fno-exceptions -fno-rtti -masm=intel -o- test.c




#Combine the too into a full instruction set

#http://web.archive.org/web/20200408122345/https://rv8.io/asm
#http://web.archive.org/web/20200415095745/https://rv8.io/isa.html

#MISSING, tail
#found on page 110
#https://content.riscv.org/wp-content/uploads/2017/05/riscv-spec-v2.2.pdf





#very good resource
#https://compil-lyon.gitlabpages.inria.fr/compil-lyon/CAP1920_ENSL/riscv_isa.pdf




#TODO:
#trip extra whitespace
#filter out assembly directives
#then filter out unused blocks







from preprocesser import ASMPreParser
import instructions



class Block:
    def __init__(self, label_name):
        self.name = label_name

        
class ProgramBlock(Block):
    
    def __init__(self, label_name):
        Block.__init__(self, label_name)
        self.instructions = []
        
    def add(self, instruction):
        self.instructions.append(instruction)


    
class InnerProgramBlock(ProgramBlock):
    
    def __init__(self, label_name):
        ProgramBlock.__init__(self, label_name)



#TODO: Parse the data
class DataBlock(Block):
    
    def __init__(self, label_name):
        Block.__init__(self, label_name)
        self.data = []
    
    def add(self, data):
        self.data.append(data)








class AssemblyFile:
    def __init__(self, file_name):
        self.preparser = ASMPreParser(file_name)
        self.file_name = file_name
        
    def parse(self):
        self.preparser.parse()


        blocks = []
        currentBlock = None


        
        for index, line in enumerate(self.preparser.asm):
            #TODO: make it parse the begin_custom_asm and end_custom_asm into a raw_asm instruction
            if (line[0]!=" "):
                label = line.split(":")[0].rstrip()
                currentBlock = None


                #Make a new block segment of the type specified for the label
                if (self.preparser.types[label] == "@object"):
                    currentBlock = DataBlock(label)
                elif (self.preparser.types[label] == "@function"):
                    currentBlock = ProgramBlock(label)
                elif (self.preparser.types[label] == "@innerFunction"):
                    currentBlock = InnerProgramBlock(label)
                else:
                    raise Exception("None recognised type for label " + label)
                blocks.append(currentBlock)
            
            else:
                #If the current block is a program block, it means that it must contain only instructions
                if (isinstance(currentBlock, ProgramBlock)):
                    parsed_instruction = instructions.ParseInstruction(line.lstrip())
                    currentBlock.add(parsed_instruction)
                    
                #If the current block is a data block, it means that it must contain only data definitions
                elif (isinstance(currentBlock, DataBlock)):
                    assert (line.lstrip()[0] == ".")
                    #TODO: Parse the data
                    line = line.lstrip()
                    currentBlock.add(line)
                else:
                    raise Exception("idk what happened to get here")


        self.raw_blocks = blocks
        self.named_blocks = dict((block.name, block) for block in blocks)
        self.program_blocks = []
        self.data_blocks = []
        
        for block in blocks:
            if (self.preparser.types[block.name] == "@object"):
                self.data_blocks.append(block)
            #If its not an object its program data
            else:
                self.program_blocks.append(block)

        self.functions = {}
        for block in self.program_blocks:
            if block.name in self.preparser.labelsInFunctions:
                self.functions[block.name] = [block]
                for label in self.preparser.labelsInFunctions[block.name]:
                    self.functions[block.name].append(self.named_blocks[label])
                
















    


asm_file = AssemblyFile("asm.s")
asm_file.parse()

#asm_file is now parse, all the commands are objects
#asm_file has functions object which is a dictionary of all the functions with a list of all the labels in that function
#data_blocks is an array containing all the unparsed data
#raw_blocks is the raw order that the labels came in the assembly
#named_blocks is a dictionary with there labels to objects

















#pre_parsed_asm = ASMPreParser("asm.s")
#pre_parsed_asm.parse()













































