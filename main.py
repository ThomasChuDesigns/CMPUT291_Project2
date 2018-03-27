
import sqlite3

def test():
    global connection, cursor
    #db_file = input('Enter input database file: ')
    db_file = 'mini-project2-Example.sqliteDB'
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.row_factory = sqlite3.Row

    cursor.execute('SELECT Name FROM InputRelationSchemas')
    for row in cursor.fetchall():
        print(row['Name'])

    attributeClosures()

    return

def main():
    global connection, cursor
    db_file = input('Enter input database file:')
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.row_factory = sqlite3.Row
    

    print("Select an option given below:")
    print('-'*36)
    print('Enter (1) to normalize and decompose to BCNF')
    print('Enter (2) to get attribute closures')
    print('Enter (3) to check equivalence of 2 relations')
    print('Enter \'exit\' to leave program')
    print('-'*36)

    isExit = False
    choice = input('')
    while(not isExit):
        if(choice == 1):
            convertToBCNF()
            continue
        elif(choice == 2):
            pass
            
            continue
        elif(choice == 3):
            tbl_1 = input('Enter a table name to check: ')
            tbl_2 = input('Enter a table to compare to: ')
            #checkEquivalence(tbl1, tbl2)
            continue
        elif(choice == 'exit'):
            isExit = True
            continue
    return

def convertToBCNF():
    pass

def checkEquivalence(tbl1, tbl2):
    # compares the attribute closure of 2 input attributes
    # if F1+ == F2+ then return true else false
    pass

def attributeClosures():
    # get input schema and attributes to calculate
    schema_input = input('Enter schemas for FD: ')
    attr_input = input('Enter attributes to compute closure: ')

    # parses attribute and converts to a list
    attr_input = parseAttributesInput(attr_input)
    print(attr_input)

    schema_input = schema_input.split(',')
    fd_input = []
    for schema in schema_input:
        cursor.execute('SELECT FDs FROM InputRelationSchemas WHERE Name = ?', (schema,))
        fd_input.append(cursor.fetchone()['FDs'])
    
    # join all FD's into a string to parse
    fd_input = '; '.join(fd_input)

    # parse FDs from database to dictionary and list attributes
    func_dependencies = get_func_dependencies(fd_input)

    # for every attribute calculate its closure
    for attribute in attr_input:
       print('{} -> {}'.format(attribute, getClosure(attribute, func_dependencies)))
    return

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
    return sorted(closure, key = lambda x: ord(x))

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

        
        




if __name__ == "__main__":
    test()
    #main()