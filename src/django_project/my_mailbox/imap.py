import imaplib2
import email
from email.message import EmailMessage
from email import policy
import logging
import datetime
import ssl  # access to TLS encryption
import common
import MExcept
import re

######################## Initialize Mailbox ###################
logger = logging.getLogger(__name__)

class ImapTransport:
    def __init__( self, user_mail, app_password, security, hostname, port=None, folder=None): #ssl=False, tls=False, 
        self.user_mail = user_mail  # email
        self.password = app_password

        self.hostname = hostname # imap host server
        self.port = port
        self.security = security # SSL or TLS
        
        self.folder = folder
        
        if self.security == "SSL":
            self.connection = imaplib2.IMAP4_SSL
            if not self.port:
                self.port = 993 # Port 993 for encrypted
        else:
            self.connection = imaplib2.IMAP4
            if not self.port:
                self.port = 143 # Port 143 for unencrypted


    ################# Connects to imap over different security. ###############
    ############## Connecting to mail server for multiple users ###############
    def connect(self):
        self.imap_server = self.connection(host=self.hostname, port=int(self.port))
        if self.security == "TLS":
            # context = ssl.create_default_context()   # create SSL default context
            self.imap_server.starttls() # starttls(context) upgrades unencrypted into encrypted
        
        resp_code = self.imap_server.login(self.user_mail, self.password)
        if not resp_code[0] == 'OK':
            raise MExcept.IMAPError(resp_code[1])

        ############### Set Mailbox #############
        if self.folder:
            self.imap_server.select(self.folder)
        else:
            self.special_folders = self.get_special_folders()
            self.imap_server.select()



    #################### List Directories #####################
    ############### return list of mail directories ( Directories = folders) ##############
    ######## decode() method converts messages from bytes to string format ########
    def list_folders(self) -> list:
        # Directory of top-level mail folders
        directories = self.imap_server.list()  
        folders = []

        if not directories[0] == 'OK':
            raise MExcept.IMAPError(directories[1])

        for raw in directories[1]:
            if isinstance(raw, tuple):
                s = raw[0].decode('utf-8')
                folder_name = raw[1].decode('UTF-8')
            else:
                s = raw.decode('utf-8')
                folder_raw = s.split(' "/" ')[1]
                folder_name = folder_raw.replace('"', '')
            ## Get the flags, which are between brackets
            flags_str = s[s.find('(')+1:s.find(')')] 
            ## The flags are seperated by a space
            flags = flags_str.split(' ') 
            
            folder = {
                'folder' : folder_name,
                'flags' : flags
            }
            folders.append(folder)

        return folders

    def get_special_folders(self):
        """
        Returns a Directorie of special folders
        """
        folders = self.list_folders()
        # Special IMAP folders https://apple.stackexchange.com/a/201346
        specials = ['All', 'Archive', 'Drafts', 'Flagged', 'Junk', 'Sent', 'Trash']

        fol = {}

        for folder in folders:
            for special in specials:
                if '\\'+special in folder['flags']:
                    fol[special] = folder['folder']
        
        return fol


############### Retrieve Mail IDs for given Directory #############  
############## return: list of uids from specific Directory ##########
    def get_message_uids(self, folder, since_date_obj:datetime.date = None) -> list:
        self.imap_server.select(folder)
        search_string = 'ALL'
        if since_date_obj:
            since_date = since_date_obj.strftime('%d-%b-%Y') # Format: 28-Nov-2021
            search_string += " SINCE " + since_date

        # Fetch all the message uids
        # message_ids is one string of uids (of type bytes) in a list
        resp_code, message_ids = self.imap_server.uid('search', None, search_string)
        if not resp_code == 'OK':
            raise MExcept.IMAPError(message_ids)

        message_id_string = message_ids[0].strip()        
        # Usually `message_id_string` will be a list of space-separated
        # ids; we must make sure that it isn't an empty string before
        # splitting into individual UIDs.
        if message_id_string:
            return message_id_string.decode().split()
        return []
        
############### Retrieve specific email (based on uid) from specific folder ############# 
    def get_message(self, folder, uid) -> EmailMessage:
        resp_code, msg_folder = self.connection.select(folder)
        if not resp_code == 'OK':
            raise MExcept.IMAPError(msg_folder)
        ## fetches latest mail and its flags
        resp_code, msg_contents = self.imap_server.uid("fetch", str(uid), "(RFC822 FLAGS)")  
        if not resp_code == 'OK':
            raise MExcept.IMAPError(msg_contents)
        ## type is EmailMessage
        msg = email.message_from_bytes(msg_contents[0][1], policy=policy.default) 

        flags = []
        for flag in imaplib2.ParseFlags(msg_contents[1]):
            flags.append( flag.decode('UTF-8') )

        return msg, flags

################### Retrieve email's information ########################
############# return: date, sender, recipient, subject, importance ######
    def get_info(self, msg: EmailMessage):
        info = common.parse_email(msg)
        return info

############# Retrieve overview of all emails from specific folder ########
################### return: dictionary of the overview ####################
    def overview_of_emails(self, folder):
        message_list = self.get_message_uids(folder)
        overview = {}

        for uid in message_list:
            msg, flags = self.get_message(folder, uid) 
            info = self.get_info(msg)
            info['flags'] = flags
            overview[uid+1] = info

        return overview

####### Uploads the mail to the mail server. Used to save sent emails or drafts. ########
################### return: UID assigned on the server ####################    
    def upload_mail(self, folder, email : EmailMessage):
        date = common.parse_email(email)['Date']
        print(common.parse_email(email))
        resp_msg = self.imap_server.append(folder, None, date, email.as_string())
        if not resp_msg[0] == 'OK':
            raise MExcept.IMAPError(resp_msg[1])
        # Decode response message
        resp_str = resp_msg[1][0].decode('UTF-8') 
        # Get the string in square brackets
        s = re.findall("\[(.*?)\]", resp_str)[0]  
        # The 3rd index is the assigned UID
        return s.split(' ')[2]                    

#################### Delete an email from a folder #######################
    def delete_email(self, folder, uid):
        self.set_flag(folder, uid, '\\Deleted')

        resp_cod = self.imap_server.expunge()
        if not resp_cod[0] == 'OK':
            raise MExcept.IMAPError(resp_cod[1])

################## Copy mail from one folder to another ##################
    def copy(self, uid, from_folder, to_folder):
        resp_code = self.imap_server.select(to_folder)
        if not resp_code[0] == 'OK':
            raise MExcept.IMAPError(resp_code[1])
        
        today_search_term = 'ALL SINCE {}'.format(datetime.date.today().strftime('%d-%b-%Y'))
        emails_before = self.imap_server.uid('SEARCH', today_search_term)[1][0].decode('UTF-8').split(' ')

        resp_code = self.imap_server.select(from_folder)
        if not resp_code[0] == 'OK':
            raise MExcept.IMAPError(resp_code[1])

        resp_code = self.imap_server.uid('copy', str(uid), to_folder)
        if not resp_code[0] == 'OK':
            raise MExcept.IMAPError(resp_code[1])

        resp_code = self.imap_server.select(to_folder)
        if not resp_code[0] == 'OK':
            raise MExcept.IMAPError(resp_code[1])

        emails_after = self.imap_server.uid('SEARCH', today_search_term)[1][0].decode('UTF-8').split(' ')
        new = list(set(emails_after) - set(emails_before))
        
        if len(new) == 1:
            return new[0]
        else:
            return -1
################## Move mail from one folder to another ##################   
    def move(self, uid, from_folder, to_folder):
        resp_code = self.imap_server.select(to_folder)
        if not resp_code[0] == 'OK':
            raise MExcept.IMAPError(resp_code[1])
        
        today_search_term = 'ALL SINCE {}'.format(datetime.date.today().strftime('%d-%b-%Y'))
        emails_before = self.imap_server.uid('SEARCH', today_search_term)[1][0].decode('UTF-8').split(' ')


        resp_code = self.imap_server.select(from_folder)
        if not resp_code[0] == 'OK':
            raise MExcept.IMAPError(resp_code[1])

        resp_code = self.imap_server.uid('MOVE', str(uid), to_folder)
        if not resp_code[0] == 'OK':
            raise MExcept.IMAPError(resp_code[1])


        resp_code = self.imap_server.select(to_folder)
        if not resp_code[0] == 'OK':
            raise MExcept.IMAPError(resp_code[1])
        emails_after = self.imap_server.uid('SEARCH', today_search_term)[1][0].decode('UTF-8').split(' ')
        new = list(set(emails_after) - set(emails_before))
        
        if len(new) == 1:
            return new[0]
        else:
            return -1
    
    def get_flags(self, folder, uid):
        flags = self.get_message(folder, uid)
        return flags
    
    def set_flag(self, folder, uid, flag):
        self.imap_server.select(folder)
        if not flag in self.get_flags(folder, uid):
            self.imap_server.uid('store', str(uid), '+FLAGS', flag)
    
    def remove_flag(self, folder, uid, flag):
        self.imap_server.select(folder)
        if flag in self.get_flags(folder, uid):
            self.imap_server.uid('store', str(uid), '-FLAGS', flag)

        
    def test_connection(self):
        """
        The NOOP command is only allowed when logged in. If disconnected,
        imaplib2 will raise an error.
        """
        try:
            self.imap_server.noop()
        except:
            return False
        return True

    ############### Logout of Mailbox ######################
    def disconnect(self) -> None:
        try:
            self.imap_server.logout()
        except:
            pass

    def __del__(self) -> None:
        self.disconnect()

# TODO: GEMME MAIL PÅ IMAP SERVER
# TODO: ÆNDRE FLAG (IMPORTANCE)
# TODO: FLYTTE MAILS PÅ SERVEREN
# TODO: andre metoder (delete(), move(), flag() etc.) - kig på account test fil.





    ############### Display Message for given Directory #############
    #for mail_id in mails[0].decode().split()[-2:]:
    #    print("================== Start of Mail [{}] ====================".format(mail_id))
    #    resp_code, mail_data = imap_ssl.fetch(mail_id, '(RFC822)') ## Fetch mail data.
    #    message = email.message_from_bytes(mail_data[0][1]) ## Construct Message from mail data
    #    print("From       : {}".format(message.get("From")))
    #    print("To         : {}".format(message.get("To")))
    #    print("Bcc        : {}".format(message.get("Bcc")))
    #    print("Date       : {}".format(message.get("Date")))
    #    print("Subject    : {}".format(message.get("Subject")))
    #
    #    print("Body : ")
    #    for part in message.walk():
    #        if part.get_content_type() == "text/plain":
    #            body_lines = part.as_string().split("\n")
    #            print("\n".join(body_lines[:12])) ### Print first 12 lines of message
    #
    #    print("================== End of Mail [{}] ====================\n".format(mail_id))





    ############### Logout of Mailbox ######################
    ## print("\nLogging Out....")
    ## imap_server.close()