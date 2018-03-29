
import sqlite3
from core.tasks import *


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

    decomposeToBCNF()

    return

def main():
    global connection, cursor
    db_file = input('Enter input database file: ')
    connection = sqlite3.connect(db_file)
    cursor = connection.cursor()
    cursor.row_factory = sqlite3.Row
    cursor.execute('PRAGMA foreign_keys = ON')

    isExit = False

    while(not isExit):
        print("\nSelect an option given below:")
        print('-'*36)
        print('Enter (1) to normalize and decompose to BCNF')
        print('Enter (2) to get attribute closures')
        print('Enter (3) to check equivalence of 2 relations')
        print('Enter \'exit\' to leave program')
        print('-'*36)
        choice = input('Enter option here: ')
        if(choice == '1'):
            decomposeToBCNF(connection, cursor)
            continue
        elif(choice == '2'):
            attributeClosures(cursor)
            continue
        elif(choice == '3'):
            tbl1 = input('Enter a relation name to check: ')
            tbl2 = input('Enter a relation to compare to: ')
            if(checkEquivalence(cursor, tbl1, tbl2)):
                print('The two relations are equal!')
            else:
                print('The two relations are not equal...')
            continue
        elif(choice == 'exit'):
            isExit = True
            continue
    return


if __name__ == "__main__":
    #test()
    main()