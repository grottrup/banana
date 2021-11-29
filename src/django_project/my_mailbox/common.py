from email.message import EmailMessage
import datetime

####### Functions that are being used in more than one file ########

def priority_int(s : str):
    if s == "High":
        return 1
    elif s == "Low":
        return 5
    else:
        return 3

def priority_str(i : int):
    if i == 1 or i == 2:
        return "High"
    elif i == 4 or i == 5:
        return "Low"
    else:
        return "Normal"

####### Takes a parameter msg of type EmailMessage and gets parsed HTML ########
####### dictionary with all information about mail ########
def parse_email(msg: EmailMessage):
    sender = msg.get('From')
    recipient = msg.get('To')
    subject = msg.get('Subject')
    
    ## Find priority from X-Priority, X-MSMail-Priority or Importance header (https://www.chilkatsoft.com/p/p_471.asp)
    x_priority = msg.get('X-Priority')
    ms_priority = msg.get('X-MSMail-Priority')
    importance = msg.get('Importance')

    priority = 3
    if x_priority:
        priority = x_priority
    elif importance:
        priority = priority_int(importance)
    elif ms_priority:
        priority = priority_int(ms_priority)
    

    # Date
    date_str = msg.get('date')
    if date_str == None:
        date_str = date_to_mail_format(datetime.datetime.fromtimestamp(0))
    
    date_obj = date_from_mail_format(date_str)

    info = {
        "Date": date_obj,
        "Sender": sender,
        "Recipient": recipient,
        "Subject": subject,
        "Importance": priority
    }

    return info

def date_from_mail_format(date_str: str) -> datetime.datetime:
    date_str = date_str.split('(')[0]  # Remove timezone name
    date_str = date_str.strip()  # Remove padding spaces

    date_obj = datetime.datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")  # "Mon, 01 Mar 2021 13:31:10 +0200"

    return date_obj

def date_to_mail_format(date_obj : datetime.datetime) -> str:
    # Format: Mon, 1 Nov 2021 12:01:43 +0100
    date_str = date_obj.strftime("%a, %d %b %Y %H:%M:%S %z")
    return date_str


def change_flag(flag : str, new_flag : str, flags : list) -> list:
    print(flags)
    if flag in flags:
        i = flags.index(flag)
        flags[i] = new_flag
    return flags