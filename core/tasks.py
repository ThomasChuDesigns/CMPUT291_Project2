from core.util import *

def decomposeToBCNF(connection, cursor, debug=False):
    # R format => {attr: [a1, a2, ...], fd: [fd1, fd2, ...]}
    # decomp is a list of R decomposed using algorithm is CMPUT291 Slide 41

    tbl = input('Enter a table to decompose: ')
    result = cursor.execute('SELECT * FROM InputRelationSchemas WHERE Name = ?', (tbl,)).fetchone()

    # handle error
    if not result:
        print('Invalid Table: {}!'.format(tbl))
        return

    attributes = result['Attributes'].split(',')
    fd_list = get_func_dependencies(result['FDs'])

    decomp = [{'Attributes': list(attributes), 'FDs': dict(fd_list)}]
    isBCNF = False

    # decompose relations while not BCNF
    while not isBCNF:
        isBCNF = True

        # go through every relation until we find a violation
        for relation in decomp:
            relation_keys = findCandidateKeys(relation['Attributes'], relation['FDs'])
            # is BCNF if FDs LHS == relation_keys
            if set(relation_keys) == set(relation['FDs'].keys()): continue
            isBCNF = False

            # find a FD that is violating BCNF
            violation_key = None
            for fd_lhs in relation['FDs'].keys():
                # found FD that violates BCNF
                if fd_lhs not in relation_keys:
                    violation_key = fd_lhs
                    break
            
            # get violating attributes
            violation_attributes = set(violation_key.split(',')).union(set(relation['FDs'][violation_key].split(',')))
            rhs_diff = violation_attributes.difference(set(fd_lhs.split(',')))
            
            # prepare relation splitting
            orig_fd = dict(relation['FDs'])
            new_fd = {violation_key: orig_fd.pop(violation_key, None)}
            
            orig_attributes = relation['Attributes']
            new_attributes = violation_key.split(',')

            # update FD for original relation
            for lhs in relation['FDs']:
                # no lhs found continue
                if not orig_fd.get(lhs, None): continue
                
                # update attributes in FD accordingly
                fd_rhs = set(orig_fd[lhs].split(','))
                
                # FD RHS subset of violated attributes or FD LHS contains violated attributes
                if fd_rhs.issubset(rhs_diff) or set(lhs.split(',')).intersection(rhs_diff):
                    orig_fd.pop(lhs, None)
                # FD RHS contains violated attributes, just remove from RHS
                if fd_rhs.intersection(rhs_diff):
                    orig_fd[lhs] = ','.join(list(fd_rhs.difference(rhs_diff)))
                    if orig_fd[lhs] == '': orig_fd.pop(lhs, None)

            # move violated attributes into new list of attributes
            orig_attributes = list(set(orig_attributes).difference(rhs_diff))
            new_attributes = list(violation_attributes)

            # update original relation
            relation['Attributes'] = orig_attributes
            relation['FDs'] = orig_fd

            # add new relation
            decomp.append({'Attributes': new_attributes, 'FDs': new_fd})
            print(decomp)
            break
    # END OF DECOMPOSITION BCNF

    name_list = []
    # create new rows for relations in OutputRelationSchemas
    for relation in decomp:
        # create output name
        row_name = '{}_{}'.format(tbl, '_'.join(sorted(relation['Attributes'])))
        name_list.append(row_name)

        # parse new attributes of each relation into string
        row_attributes = ','.join(relation['Attributes'])

        # parse new fd of each relation into string
        row_fd = []
        for key in relation['FDs'].keys():
            row_fd.append( "{{{}}}=>{{{}}}".format(key, relation['FDs'][key]) )
        row_fd = '; '.join(row_fd)
        
        # insert new row into OutputRelationSchemas
        cursor.execute('INSERT OR REPLACE INTO OutputRelationSchemas VALUES(?, ?, ?)', (row_name, row_attributes, row_fd,))
        print('{} created in OutputRelationSchemas'.format(row_name))
        print('{}\t{}\t{}'.format(row_name, row_attributes, row_fd))
        
    # save changes if not debugging
    if not debug: connection.commit()

    # check if relations are dependency preserving
    if(checkEquivalence(cursor, tbl, ','.join(name_list))):
       print('Normalized Schema are dependency preserving!')
    else:
        print('Normalized Schema are not dependency preserving!')

    # no instance of table in database return
    if not result['hasInstance']: return

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
        
        # compute primary key for relation by union of FD
        primary_key = []
        if decomp_fd:
            # create a table using a primary key based on functional dependencies
            for lhs in decomp_fd.keys():
                for attr in lhs.split(','):
                    if attr not in primary_key:
                        primary_key.append(attr)
            
            primary_key = ','.join(primary_key)

        # no FD therefore all attributes make a key
        else : primary_key = results['Attributes']

        pk_comp = set(primary_key.split(','))
        for relations in decomp:
            if results['Attributes'] != ','.join(relations['Attributes']):
                for lhs in relations['FDs'].keys():
                    # if LHS of FD a subset of primary key add to foreign key
                    if set(lhs.split(',')).issubset(pk_comp):
                        foreign_tbl = '{}_{}'.format(tbl, '_'.join(sorted(relations['Attributes'])))
                        foreign_keys.append('FOREIGN KEY ({}) REFERENCES {}'.format(lhs, foreign_tbl))


        # query format: CREATE TABLE IF NOT EXISTS {table_name} ({attributes}, {primary keys}, {foreign keys})
        query_attr = []
        for attr in type_list.keys():
            query_attr.append('{} {}'.format(attr, type_list[attr]))
        query_attr = ','.join(query_attr)

        # create foreign key statements
        if foreign_keys: foreign_keys = ', ' + ','.join(foreign_keys) 
        else: foreign_keys = ''

        query = """
        CREATE TABLE IF NOT EXISTS {}({}, PRIMARY KEY ({}){});
        """.format(decomp_relation, query_attr, primary_key, foreign_keys)

        print(query)
        cursor.execute(query)
        cursor.execute('INSERT OR REPLACE INTO {} SELECT {} FROM {}'.format(decomp_relation, results['Attributes'],tbl))

    if not debug: connection.commit()

    return
    


def checkEquivalence(cursor, tbl1, tbl2):
    # compares the attribute closure of 2 input attributes
    # Ktotal = Kfd1 U Kfd2
    # compute closure for each key in fd1 and fd2
    # if a closure does not equal for fd1 and fd2 return false
    # return true if all closure are equal

    fd1 = []
    fd2 = []

    # parse input tables
    for table in tbl1.split(','):
        res = cursor.execute('SELECT FDs FROM InputRelationSchemas WHERE Name = ? UNION SELECT FDs FROM OutputRelationSchemas WHERE Name = ?', (table,table,)).fetchone()
        if not res: return print('{} is not a table!'.format(table))
        fd1.append(res['FDs'])
    
    for table in tbl2.split(','):
        res = cursor.execute('SELECT FDs FROM InputRelationSchemas WHERE Name = ? UNION SELECT FDs FROM OutputRelationSchemas WHERE Name = ?', (table,table,)).fetchone()
        if not res: return print('{} is not a table!'.format(table))
        fd2.append(res['FDs'])
        

    # get Fd's for input schemas
    fd1 = get_func_dependencies('; '.join(fd1))
    fd2 = get_func_dependencies('; '.join(fd2))

    # is fd1 < fd2 ?
    for fd1_key in fd1.keys():
        closure_fd1 = getClosure(fd1_key, fd1)
        closure_fd2 = getClosure(fd1_key, fd2)

        if(set(closure_fd1) != set(closure_fd2)):
            return False


    # is fd2 > fd1 ?
    for fd2_key in fd2.keys():
        closure_fd1 = getClosure(fd2_key, fd1)
        closure_fd2 = getClosure(fd2_key, fd2)

        if(set(closure_fd1) != set(closure_fd2)):
            return False

    # fd1 < fd2, fd2 > fd1 --> fd1 == fd2
    return True

def attributeClosures(cursor):
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
       print('{{{}}} -> {{{}}}'.format(attribute, ','.join(getClosure(attribute, func_dependencies))))
    return
