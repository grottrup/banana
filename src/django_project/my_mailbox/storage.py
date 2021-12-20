from email import parser, policy, generator
from email.message import EmailMessage
from . import databaseConnector as dbc
import os
import shutil

def create_parent(filename):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

def read_email(filename) -> EmailMessage:
    try:
        with open(filename, 'r') as f:
            p = parser.Parser(policy=policy.default)
            msg = p.parse(f)
            return msg

    except Exception as e:
        print(e)
        return None

def store_email(msg: EmailMessage, filename):
    create_parent(filename)

    with open(filename, 'w') as f:
        gen = generator.Generator(f)
        gen.flatten(msg)

def delete_email(filename):
    os.remove(filename)

def update_email(filename, msg : EmailMessage):
    delete_email(filename)
    store_email(msg, filename)

def copy_email(filename_from, filename_to):
    create_parent(filename_to)
    shutil.copy(filename_from, filename_to)

def move_email(filename_from, filename_to):
    create_parent(filename_to)
    shutil.move(filename_from, filename_to)
