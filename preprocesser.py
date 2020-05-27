#Should filter and remove everything just like godbolt but leave
#some of the assembly directives like .type .bss .text .cfi_startproc .cfi_endproc
#.globl etc...
#COPY HOW GODBOLT DOES
#(everything needed is in asm-parser.js and whitespace normalizing is in asmregex.js)

import re
#Taken direct from godbolt asmregex
labelDef = re.compile("^(?:.proc\s+)?([.a-z_$@][a-z0-9$_@.]*):", re.IGNORECASE)

#Taken direct from godbolt asm-parser
labelFindNonMips = re.compile("[.a-zA-Z_][a-zA-Z0-9$_.]*") #should be regex global search
dataDefn = re.compile("^\s*\.(string|asciz|ascii|[1248]?byte|short|x?word|long|quad|value|zero)")
hasOpcodeRe = re.compile("^\s*[a-zA-Z]")
instructionRe = re.compile("^\s*[a-zA-Z]+")
identifierFindRe = re.compile("[.a-zA-Z_$@][a-zA-z0-9_]*") #should be regex global search
definesFunction = re.compile("^\s*\.(type.*,\s*[@%]function|proc\s+[.a-zA-Z_][a-zA-Z0-9$_.]*:.*)$")
definesGlobal = re.compile("^\s*\.globa?l\s*([.a-zA-Z_][a-zA-Z0-9$_.]*)")
indentedLabelDef = re.compile("^\s*([.a-zA-Z_$][a-zA-Z0-9$_.]*):")
assignmentDef = re.compile("^\s*([.a-zA-Z_$][a-zA-Z0-9$_.]+)\s*=")
directive = re.compile("^\s*\..*$")

asmOpcodeRe = re.compile("^\s*([0-9a-f]+):\s*(([0-9a-f][0-9a-f] ?)+)\s*(.*)")
lineRe = re.compile("^(\/[^:]+):([0-9]+).*")


#matchLocalLabelDef = 


#Python version of godbolt asm-parser (MODIFIED)
def hasOpcode(line):
    match = labelDef.match(line)
    if (match):
        line = line[len(match[0]):]
    #remove comments
    line = line.split("#")[0].rstrip()
    if (assignmentDef.match(line)):
        return False
    return hasOpcodeRe.match(line)


def findUsedLabels(asmLines):
    labelsUsed = {}
    weakUsages = {}
    
    currentLabelSet = []
    inLabelGroup = False

    for line in asmLines:
        #This is a dodgy fix for $local (NOT IMPLEMENTED)
        #Implement by just skipping over the second label (ONLY WORKS IF ITS label then next line is .Llabel$local)
        
        label = labelDef.match(line)
        if(label):
            if (inLabelGroup):
                currentLabelSet.append(label[1])
                
            else:
                currentLabelSet = [label[1]]
            inLabelGroup = True
        else:
            inLabelGroup = False

        globals = definesGlobal.match(line)
        if(globals):
            labelsUsed[globals[1]] = True
        
        
        defines_function = definesFunction.match(line)
        if ((not defines_function) and ((not line) or line[0] == '.')):
            continue

        #Fix cause this regex is super shit and matches non labels
        labels = labelFindNonMips.findall(line)
        if (not labels):
            continue

        #print(labels,defines_function)
        
        #MIGHT HAVE TO MODIFY THIS !filterDirectives || this.hasOpcode(line, false) || definesFunction
        if (hasOpcode(line) or defines_function):
            for label in labels:
                labelsUsed[label] = True
        else:
            if (dataDefn.match(line) or hasOpcode(line)):
                for currentLabel in currentLabelSet:
                    if (not currentLabel in weakUsages):
                        weakUsages[currentLabel] = []
                    for label in labels:
                        weakUsages[currentLabel].append(label)
    #Generated a label map
    for iteration in range(50): #50 is the MaxLabelIterations
        toAdd = []
        for label in labelsUsed:
            if(not label in weakUsages):
                #print("wat",label)
                continue
            for nowused in weakUsages[label]:
                if (nowused in labelsUsed):
                    continue
                toAdd.append(nowused)
                
        if(len(toAdd)==0):
            break
        for used in toAdd:
            labelsUsed[used] = True
            
    #print(labelsUsed)
    return list(labelsUsed.keys())
















findHashComment = re.compile(" *#.*")
matchWhiteSpace = re.compile("(  +)|\t")
matchWhiteSpaceStart = re.compile("^(  +)|\t")





#The assembly pre parser
class ASMPreParser:
    def __init__(self, file_name):
        self.raw_asm = list(i.rstrip() for i in open(file_name).readlines())
        
        #Convert the comment version of custom asm deleration, to a directive
        #Do this here as to not break shit later
        self.raw_asm = list(line.replace("#APP",".begin_custom_asm") for line in self.raw_asm)
        self.raw_asm = list(line.replace("#NO_APP",".end_custom_asm") for line in self.raw_asm)
        self.raw_asm = list(matchWhiteSpaceStart.sub(' ', line) for line in self.raw_asm)
    def parse(self):
        #Shallow copy the array
        asm = self.raw_asm[::]
        
        #normalize tabs to spaces
        asm = list(matchWhiteSpace.sub(' ', line) for line in asm)

        #Get all the labels used by the program
        labels_used = findUsedLabels(asm)

        #This is the data that the preprocesser will output
        outasm = []

        globls = []
        labels = []
        sizes = {}
        types = {}
        labelsInFunctions = {}
        labelsInProgramAreas = {}



        #Process the input asm (Assumed to be raw, non preprocessed)
        currentLableUsed = False

        currentlyInFunction = False
        currentFunctionLabel = None

        currentProgramSection=None

        currentlyInCustomASM = False

        for index, line in enumerate(asm):
            #If its a custom asm block, just chuck EVERYTHING directly, no parsing or tab setting out
            if (line.startswith(" .begin_custom_asm")):
                currentlyInCustomASM = True
                
            if (currentlyInCustomASM):
                outasm.append(self.raw_asm[index])
                if (line.startswith(" .end_custom_asm")):
                    currentlyInCustomASM = False
                continue


            
            
            
            #Strip all comments from the asm
            line = findHashComment.sub("", line)
            #if its a blank line, ignore it
            if(line==""):
                continue

            #If it is a label definition
            if(line[0]!=" "):
                #It has to be a function definition
                assert line[-1] == ":"
                #There where 2 consecutave labels (this is to get rid of .Llabel$local:)
                #So ignore the second one
                if (asm[index - 1][:-1] in labels_used):
                    assert not line[:-1] in labels_used
                    if (line.startswith(".L") and line.endswith("$local:")):
                        continue

                #If the label was detected to be used
                if (line[:-1] in labels_used):#replace line[:-1] with regex
                    #Add it to the asm and labels
                    outasm.append(line)
                    labels.append(line[:-1])
                    currentLableUsed = True
                    #If the label is defined between cfi_startproc and cfi_endproc then it is part of a function
                    if (currentlyInFunction):
                        labelsInFunctions[currentFunctionLabel].append(line[:-1])

                    #Add the label to the corrasponding program area/section list
                    labelsInProgramAreas[currentProgramSection].append(line[:-1])
                    
                #the label isnt being used, so ignore all directives and data definitions inside it
                else:
                    currentLableUsed = False
            #Its not a label definition
            else:
                if (dataDefn.match(line)):
                    if (currentLableUsed):
                        outasm.append(line)
                elif (hasOpcodeRe.match(line)):
                    outasm.append(line)
                else:
                    #These are the assembly directives
                    line_ = line.lstrip()
                    assert line_[0]=='.'
                    directive = line_[1:].split(" ")[0]
                    
                    if (directive in ["cfi_startproc", "cfi_endproc"]):
                        
                        if (directive == "cfi_startproc"):
                            currentlyInFunction = True
                            currentFunctionLabel = labels[-1]
                            labelsInFunctions[currentFunctionLabel] = []
                        
                        if (directive == "cfi_endproc"):
                            currentlyInFunction = False
                            currentFunctionLabel = None

                        #outasm.append(line)
                    else:
                        
                        if (directive == "globl"):
                            globl_label = line_.split(" ")[1]
                            globls.append(globl_label)
                            
                        if (directive == "type"):
                            type_def = line_.split(" ")[1]
                            label, type = type_def.split(",")
                            types[label] = type
                            
                        if (directive == "size"):
                            label, size = line_.replace(".size ",'').rsplit(", ")
                            
                            #If its not a static size definition, discard it
                            if (not size.isalnum()):
                                continue
                            
                            sizes[label] = int(size)
                        
                        if (directive in ["section", "bss", "data", "text"]):
                            program_area = None
                            if (directive=="section"):
                                section = '.' + line_.split(' ')[1].split(',')[0].split('.')[1]
                                
                                if (section in [".rodata", ".sbss", ".sdata"]):
                                    program_area = section
                                else:
                                    print("Discarding .section of type " + section)
                                    continue
                            else:
                                program_area = line_
                                
                            assert program_area[0] == "."
                            program_area = program_area[1:]
                            #Add the new program area to the list
                            if (not program_area in labelsInProgramAreas):
                                labelsInProgramAreas[program_area] = []
                            currentProgramSection = program_area

        #Propergate the function type definition to inner function labels, store a record of the orinal definitions
        defined_types = types.copy()

        #Propergate the function type to function sub labels
        for label in types.copy(): #Must make a copy as types is being modified in the for loop
            if (types[label] == "@function"):
                if (label in labelsInFunctions):
                    for innerLabel in labelsInFunctions[label]:
                        assert not innerLabel in types
                        types[innerLabel] = "@innerFunction"
                else:
                    raise Exception("Getting here should be impossible")


        #verify the labels are in the correct program area and that each label has a defined type
        for label in labels:
            assert label in types.keys()
        for label in types:
            if (types[label] in ["@function", "@innerFunction"]):
                #All program code must be in the .text section
                assert label in labelsInProgramAreas["text"]
            elif (types[label] == "@object"):
                #All objects must be in the data section
                assert any(label in labelsInProgramAreas[section] for section in labelsInProgramAreas if section in ['data', 'bss', 'sbss', 'sdata', 'rodata'])
            else:
                raise Exception("UNKNOWN LABEL TYPE, for label: "+label)
        

        #Store the results
        self.asm = outasm
        
        self.globls = globls
        self.labels = labels
        self.sizes = sizes
        self.defined_types = defined_types
        self.types = types
        self.labelsInFunctions = labelsInFunctions
        self.labelsInProgramAreas = labelsInProgramAreas






if (__name__=="__main__"):
    Parser = ASMPreParser("asm.s")
    Parser.parse()
    







































































