
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
            decomposeToBCNF()
            continue
        elif(choice == '2'):
            attributeClosures()
            continue
        elif(choice == '3'):
            tbl1 = input('Enter a relation name to check: ')
            tbl2 = input('Enter a relation to compare to: ')
            if(checkEquivalence(tbl1, tbl2)):
                print('The two relations are equal!')
            else:
                print('The two relations are not equal...')
            continue
        elif(choice == 'exit'):
            isExit = True
            continue
    return

def decomposeToBCNF():
    # R format => {attr: [a1, a2, ...], fd: [fd1, fd2, ...]}
    # decomp is a list of R decomposed using algorithm is CMPUT291 Slide 41

    tbl = input('Enter a table to decompose: ')
    result = cursor.execute('SELECT Attributes, FDs FROM InputRelationSchemas WHERE Name = ?', (tbl,)).fetchone()

    # handle error
    if not result:
        print('Invalid Table: {}!'.format(tbl))
        return

    attributes = result['Attributes'].split(',')
    fd_list = get_func_dependencies(result['FDs'])

    decomp = [{'attributes': list(attributes), 'fd': dict(fd_list)}]
    
    # compute closures for each functional dependecy lhs
    # retrieve the lhs that are candidate keys or superkeys
    keys = []
    for candid in fd_list.keys():
        candid_closure = getClosure(candid, fd_list)
        if candid_closure == set(attributes):
            keys.append(candid)

    for fd_lhs in fd_list.keys():

        # lhs of function dependency is not key, decompose
        if fd_lhs not in keys:
            # calculate set difference of Y-X
            set_lhs = fd_lhs.split(',')
            set_rhs = fd_list[fd_lhs].split(',')
            fd_diff = set(set_rhs).difference(set(set_lhs))

            # compute new relation attributes and fd
            new_attr = set_lhs
            for item in set_rhs:
                if item not in new_attr:
                    new_attr.append(item)
            
            new_fd = decomp[0]['fd'].pop(fd_lhs, None)

            # update FD in original R st S - (Y-X)
            for lhs in decomp[0]['fd'].keys():
                new_rhs = decomp[0]['fd'][lhs].split(',')
                for item in decomp[0]['fd'][lhs].split(','):
                    if item in fd_diff:
                        new_rhs.remove(item)
                decomp[0]['fd'][lhs] = ','.join(new_rhs)
            
            # prepare new dictionary relation for decomposition list
            newR = {
                'attributes': new_attr,
                'fd': {fd_lhs: new_fd}
            }

            # decompose original R, creating new schema for Y-X
            for item in fd_diff:
                if item in decomp[0]['attributes']:
                    decomp[0]['attributes'].remove(item)

            decomp.append(newR)

    name_list = []
    # create new rows for relations in OutputRelationSchemas
    for relation in decomp:
        # create output name
        row_name = '{}_{}'.format(tbl, '_'.join(relation['attributes']))
        name_list.append(row_name)

        # parse new attributes of each relation into string
        row_attributes = ','.join(relation['attributes'])

        # parse new fd of each relation into string
        row_fd = []
        for key in relation['fd'].keys():
            row_fd.append( "{{{}}}=>{{{}}}".format(key, relation['fd'][key]) )
        row_fd = '; '.join(row_fd)
        
        # insert new row into OutputRelationSchemas
        cursor.execute('INSERT OR REPLACE INTO OutputRelationSchemas VALUES(?, ?, ?)', (row_name, row_attributes, row_fd,))
        print('{} created in OutputRelationSchemas'.format(row_name))

    # save changes
    connection.commit()
    # check if relations are dependency preserving
    if(checkEquivalence(tbl, ','.join(name_list))):
       print('Normalized Schema are dependency preserving!')
    else:
        print('Normalized Schema are not dependency preserving!')

    # create tables for new decomposed relations
    for decomp_relation in name_list:
        cursor.execute('SELECT Attributes, FDs FROM OutputRelationSchemas WHERE Name = ?', (decomp_relation,))
        results = cursor.fetchone()

        decomp_fd = get_func_dependencies(results['FDs'])
        type_list = {}
        foreign_keys = []
        table_info = cursor.execute('PRAGMA table_info({})'.format(tbl)).fetchall()

        # relation does not exist
        if not results: 
            print('No new tables to create!')
            return 

        # find the types of each attribute
        for attr in results['Attributes'].split(','):
            # get attribute types
            for row in table_info:
                if attr == row['name']:
                    type_list[attr] = str(row['type'])

        # find foreign keys
        for fd_lhs in decomp_fd:
            for attr in fd_lhs.split(','):

                # check every relation except for itself and find key == FD lhs
                for relations in decomp:
                    if results['Attributes'] != ','.join(relations['attributes']):
                        if attr in relations['fd'].keys():
                            foreign_tbl = '{}_{}'.format(tbl, '_'.join(relations['attributes']))
                            foreign_keys.append('FOREIGN KEY ({}) REFERENCES {}'.format(attr, foreign_tbl))


        # query format: CREATE TABLE IF NOT EXISTS {table_name} ({attributes}, {primary keys}, {foreign keys})
        query_attr = []
        for attr in type_list.keys():
            query_attr.append('{} {}'.format(attr, type_list[attr]))
        query_attr = ','.join(query_attr)

        # create foreign key statements
        if foreign_keys: foreign_keys = ', ' + ','.join(foreign_keys)
        else: foreign_keys = ''
        
        # create a table
        query = """
        CREATE TABLE IF NOT EXISTS {}({}, PRIMARY KEY ({}){});
        """.format(decomp_relation, query_attr, ','.join(decomp_fd.keys()), foreign_keys,)

        cursor.execute(query)
        cursor.execute('INSERT OR REPLACE INTO {} SELECT {} FROM {}'.format(decomp_relation, results['Attributes'],tbl))

    connection.commit()

    return
    


def checkEquivalence(tbl1, tbl2):
    # compares the attribute closure of 2 input attributes
    # Ktotal = Kfd1 U Kfd2
    # compute closure for each key in fd1 and fd2
    # if a closure does not equal for fd1 and fd2 return false
    # return true if all closure are equal

    fd1 = []
    fd2 = []

    # parse input tables
    for table in tbl1.split(','):
        fd1.append(cursor.execute('SELECT FDs FROM InputRelationSchemas WHERE Name = ? UNION SELECT FDs FROM OutputRelationSchemas WHERE Name = ?', (table,table,)).fetchone()['FDs'])
    for table in tbl2.split(','):
        fd2.append(cursor.execute('SELECT FDs FROM InputRelationSchemas WHERE Name = ? UNION SELECT FDs FROM OutputRelationSchemas WHERE Name = ?', (table,table,)).fetchone()['FDs'])

    # get Fd's for input schemas
    fd1 = get_func_dependencies('; '.join(fd1))
    fd2 = get_func_dependencies('; '.join(fd2))

    # is fd1 < fd2 ?
    for fd1_key in fd1.keys():
        closure_fd1 = getClosure(fd1_key, fd1)
        closure_fd2 = getClosure(fd1_key, fd2)

        if(closure_fd1 != closure_fd2):
            return False


    # is fd2 > fd1 ?
    for fd2_key in fd2.keys():
        closure_fd1 = getClosure(fd2_key, fd1)
        closure_fd2 = getClosure(fd2_key, fd2)

        if(closure_fd1 != closure_fd2):
            return False

    # fd1 < fd2, fd2 > fd1 --> fd1 == fd2
    return True

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
    return set(sorted(closure, key = lambda x: x))

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
    #test()
    main()