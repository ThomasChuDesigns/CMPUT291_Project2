
import sqlite3

def test():
    global connection, cursor
    db_file = input('Enter input database file: ')
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.row_factory = sqlite3.Row

    cursor.execute('SELECT FDs FROM InputRelationSchemas WHERE Name = "Person"')
    result = get_func_dependencies(cursor.fetchone()['FDs'])
    print(result)
    print(getClosure('SSN', result))

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
            # get inputs
            attr_input = input('Enter attribute to calculate closure: ')
            tables = input('Enter tables to compute attribute closures: ')
            tables.split(',')
            for table in tables:
                cursor.execute('SELECT FD FROM ?', (table,))
                result = getAttrClosure(attr_input, cursor.fetchone()['FD'])

            
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

def getClosure(attribute, func_dependencies):
    closure = set(attribute.split(','))
    explored = set()

    while(explored != closure):
        explored = closure

        for lhs in func_dependencies.keys():
            if(set(lhs.split(',')).issubset(closure)):
                # closure = closure U RHS
                closure = closure.union(func_dependencies[lhs].split(','))
  
    return closure

def get_func_dependencies(FD_list):

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





if __name__ == "__main__":
    test()
    #main()