from datetime import datetime
import email
import os
from email.message import EmailMessage
from . import storage
from . databaseConnector import Database
from . import common

class LocalMailbox:
    db : Database
    db_path : str
    mailbox_path : str
    attachment_path : str
    account_name : str

    def __init__(self, account_name : str, storage_path : str) -> None:
        self.account_name = account_name
        self.mailbox_path = os.path.join(storage_path, 'mailbox')
        self.attachment_path = os.path.join(storage_path, 'attachments')
        self.db_path = os.path.join(storage_path, account_name + ".sqlite")
    
    def __del__(self) -> None:
        pass

    def _generate_filename(self, folder, uid, with_extension = True):
        '''
        Generates the filename for a given folder and uid.
        '''
        filename = str(uid)
        if with_extension:
            filename += '.eml'

        path = os.path.join(self.mailbox_path, folder, filename)
        path = os.path.normpath(path)
        return path


    def connect(self):
        self.db = Database(self.db_path)

    def disconnect(self):
        self.db.close()

    def list_folders(self) -> list:
        '''
        Returns list of dicts with names of the folders and their tags
        '''
        folders = self.db.get_rows('^client_folders') 

        ret = []
        for folder in folders:
            flags_str = folder['flags']
            flags = flags_str.split(' ')

            ret.append({
                'folder': folder['folder_name'],
                'flags' : flags
            })
        
        return ret

    def create_folder(self, folder_name : str, flags : list = None, parent = None):
        '''
        Initialize a new folder
        '''

        full_path = folder_name
        if parent:
            full_path = f'{parent}/{folder_name}'
            #parent_flags = self.folder_flags(parent)

            #if '\\HasNoChildren' in parent_flags:
            #    parent_flags = common.change_flag('\\HasNoChildren', '\\HasChildren', parent_flags)
            #
            #    flags_str = ' '.join(parent_flags)
            #    self.db.update_unique_row('^client_folders', 'folder_name', parent, {'flags': flags_str})
        
        if flags == None:
            flags = []
        #flags.append('\\HasNoChildren')
        self.db.initialize_uid(full_path)
        flags_str = ' '.join(flags)
        self.db.update_unique_row('^client_folders', 'folder_name', full_path, {'flags': flags_str})

        columns= """uid INT type UNIQUE,
                    remote_uid INT,
                    date,
                    sender,
                    recipient,
                    subject,
                    flags,
                    importance,
                    attachments
                    """
        self.db.create_table(full_path,columns)
    
    def delete_folder(self, folder_name : str):
        '''
        Deletes a folder and all mail in it
        '''
        if self.db.table_exists(folder_name):
            emails = self.list_emails(folder_name)
            for email in emails:
                filename = self._generate_filename(folder_name, email['uid'])
                storage.delete_email(filename)
        
        self.db.delete_table(folder_name, is_folder = True)
    
    def folder_exists(self, folder_name: str) -> bool:
        '''
        Returns wether a given folder exists
        '''
        return not self.db.get_unique_row('^client_folders', 'folder_name', folder_name) == None

    def folder_flags(self, folder_name) -> list:
        '''
        Gets all flags for a given folder
        '''
        flags = self.db.get_unique_row('^client_folders', 'folder_name', folder_name)['flags']
        return flags.split(' ')

    def get_info(self, email : EmailMessage):
        '''
        Get metadata from an email
        '''
        return common.parse_email(email)
    
    def list_emails(self, folder):
        '''
        List uids of all emails in a folder
        '''
        if not self.db.table_exists(folder):
            return []
        rows = self.db.get_rows(folder)
        for row in rows:
            row['date'] = datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S%z')

        return rows

    def put_email(self, folder, email : EmailMessage, flags : list = None, remote_uid = -1) -> int:
        '''
        Store an email in the given folder. 
        '''
        uid = self.db.generate_uid(folder)
        path = self._generate_filename(folder, uid)
        storage.store_email(email, path)

        info = self.get_info(email)

        if flags == None:
            flags = []
        
        has_attachment = any(True for _ in email.iter_attachments())

        if not self.db.table_exists(folder):
            self.create_folder(folder)

        self.db.add_row(folder, (
            uid,
            remote_uid,
            info['Date'], # A datetime object
            info['Sender'],
            info['Recipient'],
            info['Subject'],
            ' '.join(flags), 
            info["Importance"], 
            int(has_attachment)
        ))

        return uid
    
    def set_remote_uid(self, folder, local_uid, remote_uid):
        row = self.db.get_unique_row(folder, 'uid', local_uid)
        if row['remote_uid'] >= 0:
            raise Exception("Email is already linked to a remote email: " + str(row['remote_uid']))
        self.db.update_unique_row(folder, 'uid', local_uid, {
            'remote_uid' : remote_uid
        })
    
    def get_remote_uid(self, folder, local_uid):
        row = self.db.get_unique_row(folder, 'uid', local_uid)
        if row['remote_uid'] >= 0:
            return row['remote_uid']
        raise Exception(f"Email {local_uid} in {folder} is not linked to a remote UID")
    
    def delete_email(self, folder, uid):
        '''
        Permanently delete an email
        '''
        filename = self._generate_filename(folder, uid)
        storage.delete_email(filename)
        self.db.delete_rows(folder, f'uid = {uid}')

    def copy(self, uid, from_folder, to_folder):
        '''
        Copy an email from one folder to another
        '''
        name_from = self._generate_filename(from_folder, uid)
        uid_new = self.db.generate_uid(to_folder)
        name_to = self._generate_filename(to_folder, uid_new)

        # Copy email phisically
        storage.copy_email(name_from, name_to)

        # Copy email in the database
        data = self.db.get_unique_row(from_folder, 'uid', uid)
        data['uid'] = uid_new
        data['remote_uid'] = -1
        self.db.add_row(to_folder, tuple(data.values()))

        return uid_new

    def move(self, uid, from_folder, to_folder):
        '''
        Move an email from one folder to another
        '''
        name_from = self._generate_filename(from_folder, uid)
        uid_new = self.db.generate_uid(to_folder)
        name_to = self._generate_filename(to_folder, uid_new)

        storage.move_email(name_from, name_to)

        # Copy email in the database
        data = self.db.get_unique_row(from_folder, 'uid', uid)
        data['uid'] = uid_new
        data['remote_uid'] = -1
        self.db.add_row(to_folder, tuple(data.values()))

        # Delete original row
        self.db.delete_rows(from_folder, f'uid = {uid}')

        return uid_new
    
    def get_flags(self, folder, uid):
        row = self.db.get_unique_row(folder, 'uid', uid)
        flags = row['flags'].split(' ')
        return flags
    
    def set_flag(self, folder, uid, flag):
        flag_list = self.get_flags(folder, uid)
        if not flag in flag_list:
            flag_list.append(flag)
            flags_str = ' '.join(flag_list)
            self.db.update_unique_row(folder, 'uid', uid, {'flags': flags_str})
    
    def remove_flag(self, folder, uid, flag):
        flag_list:list = self.get_flags(folder, uid)
        if flag in flag_list:
            flag_list.remove(flag)
            flags_str = ' '.join(flag_list)
            self.db.update_unique_row(folder, 'uid', uid, {'flags': flags_str})

    def update_importance(self, folder, uid, value):
        self.db.update_unique_row(folder, 'uid', uid, {'importance': value})
        filename = self._generate_filename(folder, uid)
        msg = storage.read_email(filename)
        result = msg.get('Priority')
        if result == None:
            msg.add_header('Priority', value)
        else:
            msg.replace_header('Priority', value)
        storage.update_email(filename, msg)
            
    def folder_set_flag(self, folder, flag):
        '''
        Set a flag on a folder
        '''
        row = self.db.get_unique_row('^client_folders', 'folder_name', folder)
        current_flags = row['flags']
        if len(current_flags) == 0:
            new_flags = flag
        else:
            new_flags = current_flags + " " + flag
        self.db.update_unique_row('^client_folders', 
                                  'folder_name', 
                                  folder, 
                                    {
                                        'flags' : new_flags
                                    }
                                  )

    def get_email(self, folder, uid):
        '''
        Returns the email object of the specified mail
        '''
        email_obj = storage.read_email(self._generate_filename(folder, uid))
        return email_obj

