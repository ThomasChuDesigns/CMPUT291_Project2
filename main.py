
import sqlite3

def main():
    global connection, cursor
    db_file = input('Enter input database file:')
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    
    

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
            getAttrClosure()
            continue
        elif(choice == 3):

            checkEquivalence()
            continue
        elif(choice == 'exit'):
            isExit = True
            continue
    return

def convertToBCNF():
    pass

def getAttrClosure():
    pass

def checkEquivalence():
    pass


if __name__ == "__main__":
    main()