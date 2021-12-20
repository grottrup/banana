import sqlite3
import os

class Database:
    _db : sqlite3.Connection
    _cur : sqlite3.Cursor

    def __init__(self, filename) -> None:
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        self._db = sqlite3.connect(filename)
        self._cur = self._db.cursor()

        self.create_table('^client_folders', "folder_name type UNIQUE, uid_counter INT, flags")

    def __del__(self):
        self.close()
    
    def close(self, commit : bool = True):
        '''
        Close connection to the database. 
        '''
        if commit:
            self._db.commit()
        self._db.close()

    def table_exists(self, table_name) -> bool:
        '''
        Returns true if given table exists. Assumes table_name is sanitised
        '''
        self._cur.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{table_name}';")

        return (self._cur.fetchone()[0]==1)
        

    def create_table(self, table_name : str, columns : str ):
        '''
        Creates a table in the database. Assumes table and column names are sanitised
        - table_name
        - columns : column names in the format: "col1, col2, col3"
        '''
        if not self.table_exists(table_name):
            expression = f"CREATE TABLE '{table_name}' ({columns})"
            #print(expression)
            self._cur.execute(expression)
            self._db.commit()
        pass

    def delete_table(self, table_name, is_folder = False):
        '''
        Deletes a table with the given name
        '''
        self._cur.execute(f"DROP TABLE IF EXISTS '{table_name}'")
        self._db.commit()
        
        if is_folder:
            self.delete_rows('^client_folders', f"folder_name = '{table_name}'")

    
    def get_column_names(self, table_name):
        self._cur.execute(f"PRAGMA table_info ('{table_name}')")
        cols = self._cur.fetchall()
        col_names = []
        for col in cols:
            col_names.append(col[1])
        return col_names

    def get_unique_row(self, table_name, unique_column_name, value):
        '''
        Returns the row from the table indicated by [table_name] with 
        [value] in the column [unique_column_name] in the form of a dict.
        Indices of the dict is the column names. If value is not unique, 
        the first occurrence is returned. 
        '''

        self._cur.execute(f"SELECT * FROM '{table_name}' WHERE {unique_column_name} = ? ", (value,))
        ret = self._cur.fetchone()

        if ret == None:
            return None

        col_names = self.get_column_names(table_name)
        ret_dict = dict(zip(col_names, ret))

        return ret_dict

    def get_rows(self, table_name, sql_condition = None, value_tuple : tuple = None):
        '''
        Returns a list of rows that satisfies a given SQL condition. If none 
        are given, it list all rows.

        table_name and sql_condition DOES NOT GET SANITISED and assuems 
        they already are.
        Each list element is a dict with column names as keys.
        '''
        if sql_condition == None:
            self._cur.execute(f"SELECT * FROM '{table_name}'")
        elif value_tuple == None:
            self._cur.execute(f"SELECT * FROM '{table_name}' WHERE {sql_condition}")
        else:
            self._cur.execute(f"SELECT * FROM '{table_name}' WHERE {sql_condition}", value_tuple)

        rows = self._cur.fetchall()
        
        col_names = self.get_column_names(table_name)

        return_list = []
        for row in rows:
            return_list.append( dict(zip(col_names, row)) )
        
        return return_list
    
    def add_row(self, table_name, values : tuple):
        '''
        Add a row to the specified table. The given values should be a tuple
        with each element corresponding to a collumn in the table.
        '''

        # Count number of columns in the table and check the given values match
        self._cur.execute(f"PRAGMA table_info ('{table_name}')")
        expected_values = self._cur.fetchall()
        if not len(values) == len(expected_values):
            raise Exception(f"{values} is of different length ({len(values)}) than there are columns: {len(expected_values)} {expected_values}")
        
        # Create placeholder list to pass the tuple parsing to the sql library
        qmarks = "?"
        for i in range(len(values)-1):
            qmarks += ", ?"

        sql_str = f"INSERT INTO '{table_name}' values ({qmarks})"

        self._cur.execute(sql_str, values)
        self._db.commit()
    
    def delete_rows(self, table_name, sql_condition):
        '''
        Deletes row from a table, that meets the given condition
        '''
        self._cur.execute(f"DELETE FROM '{table_name}' WHERE {sql_condition}")
        self._db.commit()
        return self._cur.rowcount

    def update_unique_row(self, table_name, unique_column, unique_value, updates : dict):
        '''
        Updates the specified row with data from the updates dict. Each key in the dict 
        should correspond to a column name.
        '''

        set_expression = ""
        for key in updates:
            #print(key)
            #print(updates[key])
            set_expression += f"{key} = '{updates[key]}', "

        if len(updates) > 0:
            set_expression = set_expression[0:-2] # Remove the last ", "

        sql_expression = f"UPDATE '{table_name}' SET {set_expression} WHERE {unique_column} = (?)"
        #print(sql_expression)

        self._cur.execute(sql_expression, (unique_value, ))

    def initialize_uid(self, key):
        '''
        Initialize a folder for storing uids. 
        '''
        row = self.get_unique_row('^client_folders', 'folder_name', key)
        if row == None:
            self.add_row('^client_folders', (key, -1, ''))
            #-1 means no ids have been assigned yet.

    def generate_uid(self, key) -> int:
        '''
        Increments a counter specific to a folder, and return its value
        '''
        row = self.get_unique_row('^client_folders', 'folder_name', key)
        if row == None:
            self.initialize_uid(key)
            uid = 0
        else:
            uid = row['uid_counter']
            uid += 1
        self.update_unique_row('^client_folders', 'folder_name', key, {'uid_counter': uid})
        return uid
