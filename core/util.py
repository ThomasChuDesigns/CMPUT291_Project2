def getClosure(attribute, func_dependencies):
    # given an attribute and a functional dependencies list return a list of the attributes closure
    closure = set(attribute.split(','))
    explored = set()

    # once we cant find any unique closures exit loop
    while(explored != closure):
        explored = closure

        for lhs in func_dependencies.keys():
            if(set(lhs.split(',')).issubset(closure)):
                # closure = closure U RHS
                closure = closure.union(func_dependencies[lhs].split(','))
    
    # returns sorted closure alphabetically
    return sorted(closure, key = lambda x: str(x))

def get_func_dependencies(FD_list):
    # given a string of FDs from database, return a dictionary of the parsed FD

    # create a dictionary to store function dependencies
    func_dependencies = {}

    # convert FDs string into a list of FD
    FD_list = FD_list.split('; ')

    for FD in FD_list:
        # remove curly brackets
        FD = FD.replace('{', '')
        FD = FD.replace('}', '')

        # split LHS and RHS
        FD = FD.split('=>')

        # convert FD to a dictionary format
        func_dependencies[FD[0]] = FD[1]

    return func_dependencies

def parseAttributesInput(attr_input):
    # given a string of attr_input convert to a list
    
    # replace inner comma with ; as placeholder
    # split string into list
    attr_input = attr_input.replace(', ', ';')
    attr_input = attr_input.split(',')
    out = []

    for attr in attr_input:
        # remove {, }, ; keeping only attributes
        attr = attr.replace('{', '')
        attr = attr.replace('}', '')
        attr = attr.replace(';', ',')
        out.append(attr)
    
    # returns a list of attributes from input string
    return out