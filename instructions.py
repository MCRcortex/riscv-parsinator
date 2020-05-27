def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        pass
import inspect

instruction_parsers = {}


#define instruction
def DefInst(function):
    #uses the function name without any beginning _ as the instruction_name
    instruction_name = function.__name__.lstrip("_")
    
    FullArgSpec = inspect.getfullargspec(function)
    
    args = FullArgSpec.args
    annotations = FullArgSpec.annotations
    
    #Specificaly remove the first arg from the args list if `function` is a class/class initalizer
    if(inspect.isclass(function)):
        #Check that the first arg isnt annotated, just to be on the safe side
        if not args[0] in annotations:
            args = args[1:]


    #MAYBE
    #TODO make it so that if an arg doesnt have an annotation it is ignored from the parser
            
    
    #Each arg must have an annotation
    assert len(args) == len(annotations)

    #cast all the args to there types
    arg_annotations = list(annotations[arg] for arg in args)

    #Takes the argumens specified by the only argument and resolves then with the arg_annotations and then calls the instruction definition function
    def ParseInstructionInternal(instruction_args):
        instruction_args = list(arg.lstrip().rstrip() for arg in instruction_args.split(","))
        
        #Remove any empty args
        instruction_args = list(arg for arg in instruction_args if arg!="")

        #Check that the correct number of arguements are there
        if (len(instruction_args) != len(arg_annotations)):
            raise ValueError("Instruction %s did not recieve the correct number of arguments\nGot %s, expected %s"%(instruction_name, len(instruction_args), len(arg_annotations)))
        
        #Parse the instruction_args with the arg_annotations types
        #This gives args with class repersentations of the args
        parsed_args = list(arg_type(arg_value) for arg_type, arg_value in zip(arg_annotations, instruction_args))

        #Actually call the instruction parser with the parsed args
        parsed_inst = function(*parsed_args)
        return parsed_inst


    #Make sure that the instruction parser with a given name isnt already in the parser dictionary
    assert not instruction_name in instruction_parsers
    
    #Add the internal instruction parser to the list of instruction parsers
    instruction_parsers[instruction_name] = ParseInstructionInternal
    
    return function


def ParseInstruction(instruction):
    instruction = instruction.lstrip().rstrip()
    while "  " in instruction:
        instruction = instruction.replace("  ", " ")
    inst_name = instruction.split(" ")[0]
    if (not inst_name in instruction_parsers):
        raise Exception("Unimplementd instruction: %s" % inst_name)
    #Call the instruction specific parser, with the instruction name removed and return the value
    return instruction_parsers[inst_name](" ".join(instruction.split(" ")[1:]))






#WILL NEED TO BE ABLE TO PARSE STUFF LIKE THIS "sw zero, %lo(LABLE+4)(a0)"

class Label:
    def __init__(self, name):
        self.name = name




#Not only a number, could be e.g. %hi(lable) or even %lo(LABLE+4)
class Immediate:
    #isConstant cannot be true with hasLabel true or hasAddin true
    def __init__(self, raw_value):
        self.isConstant = False
        self.hasLabel = False
        self.hasAddin = False
        self.hasRelocationFunction = False
        if(is_int(raw_value)):
            self.isConstant = True
            self.value = int(raw_value)
            return


        #SOME ASSUMPTIONS HAVE BEEN MADE BELOW
        assert "(" in raw_value
        self.hasRelocationFunction = True
        
        if("+" in raw_value):
            self.hasAddin = True
            self.addinValue = int(raw_value.split("+")[1].split(")")[0])
            raw_value = raw_value.split("+")[0] + ")"

        if(is_int(raw_value.split("(")[1][0])):
            raise Exception("Invaild immediate: %s"%raw_value)

        self.hasLabel = True

        self.relocationFunction = raw_value.split("(")[0]
        
        label_name = raw_value.split("(")[1].split(")")[0] 
        self.label = Label(label_name)

        

        







#NEED TO VERIFY THAT ANY lw on ra has an accompanying sw ra
#E.g.
#lw ra, 44(sp)
#sw ra, 44(sp)

Registers = ["zero", "ra", "sp", "gp", "tp",
             "t0", "t1", "t2",
             "s0", "s1"]
Registers.extend("a" + str(i) for i in range(0, 8))
Registers.extend("s" + str(i) for i in range(2, 12))
Registers.extend("t" + str(i) for i in range(3, 7))


#Note there is a register called zero which is a constant of zero
class Register:
    #Find better var name for name, cause name is the unparsed thing of the register
    def __init__(self, name):
        assert name in Registers
        self.name = name






#NOTE, the offset is an Immediate value (meaning it can be e.g. %lo(lable))
class OffsetRegister:
    def __init__(self, raw_value):
        assert "(" in raw_value
        parts =  raw_value.split("(")
        
        register = parts[-1].replace(")", '')
        immediate = "(".join(parts[:-1])
        
        self.register = Register(register)
        self.immediate = Immediate(immediate)









##add
##addi
##and
##andi
##beqz
##bge
##bgeu
##bgez
##blt
##bltu
##bltz
##bne
##bnez
##call
##j
##lui
##lw
##mul
##mv
##neg
##or
##ret
##seqz
##sll
##slli
##slt
##sltu
##sra
##srai
##srli
##sub
##sw
##tail
##xor






class InstructionBase:
    pass



#These should return instruction classes or be instruction classes or something


@DefInst
class add(InstructionBase):
    def __init__(self, dest: Register, a: Register, b: Register):
        self.dest = dest
        self.a = a
        self.b = b
        pass
    
@DefInst
class addi(InstructionBase):
    def __init__(self, dest: Register, a: Register, b: Immediate):
        self.dest = dest
        self.a = a
        self.b = b
        pass





@DefInst
class _and(InstructionBase):
    def __init__(self, dest: Register, a: Register, b: Register):
        self.dest = dest
        self.a = a
        self.b = b
        pass

@DefInst
class andi(InstructionBase):
    def __init__(self, dest: Register, a: Register, b: Immediate):
        self.dest = dest
        self.a = a
        self.b = b
        pass






@DefInst
class beqz(InstructionBase):
    def __init__(self, condition: Register, jump: Label):
        self.condition = condition
        self.jump = jump
        pass

@DefInst
class bnez(InstructionBase):
    def __init__(self, condition: Register, jump: Label):
        self.condition = condition
        self.jump = jump
        pass


@DefInst
class bge(InstructionBase):
    def __init__(self, rs1: Register, rs2: Register, jump: Label):
        self.rs1 = rs1
        self.rs2 = rs2
        self.jump = jump
        pass

@DefInst
class bgeu(InstructionBase):
    def __init__(self, rs1: Register, rs2: Register, jump: Label):
        self.rs1 = rs1
        self.rs2 = rs2
        self.jump = jump
        pass






@DefInst
class call(InstructionBase):
    def __init__(self, location: Label):
        self.location = location
        pass





@DefInst
class lbu(InstructionBase):
    def __init__(self, rd: Register, address: OffsetRegister):
        self.rd = rd
        self.address = address
        pass


@DefInst
class lui(InstructionBase):
    def __init__(self, rd: Register, value: Immediate):
        self.rd = rd
        self.value = value
        pass




@DefInst
class lw(InstructionBase):
    def __init__(self, rd: Register, address: OffsetRegister):
        self.rd = rd
        self.address = address
        pass




@DefInst
class mv(InstructionBase):
    def __init__(self, rd: Register, rs: Register):
        self.rd = rd
        self.rs = rs
        pass



@DefInst
class ret(InstructionBase):
    def __init__(self):
        pass


@DefInst
class sb(InstructionBase):
    def __init__(self, rs: Register, address: OffsetRegister):
        self.rs = rs
        self.address = address
        pass


@DefInst
class sw(InstructionBase):
    def __init__(self, rs: Register, address: OffsetRegister):
        self.rs = rs
        self.address = address
        pass

#ParseInstruction("addi a1, zero, 2")
#ParseInstruction("sw zero, %lo(LABLE+4)(a0)")























































