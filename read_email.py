import imaplib
import base64
from operator import imatmul
import os
import email
import json
import sys
import quopri


class EmailClient(object):
    def __init__(self, user, passw, folder, email_host, email_port) -> None:
        self.mail = imaplib.IMAP4_SSL(email_host, int(email_port))
        self.mail.login(user, passw)
        self.mail.select(folder)

    def get_ids(self):
        _, data = self.mail.search(None, 'ALL')
        mail_ids = data[0]
        return mail_ids.split()

    def get_email(self, email_id):
        _, data = self.mail.fetch(email_id, '(RFC822)' )
        raw_email = data[0][1]
        raw_email = quopri.decodestring(raw_email)
        return raw_email


def same_content(content, filename):
    if not os.path.exists(filename):
        return False

    with open(filename, 'r') as fh:
        data = fh.read()
        if data != content:
            return False
    return True

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <email_creds_file> <outdir>")
        exit(1)
    
    email_creds = os.path.expanduser(sys.argv[1])
    outdir = os.path.expanduser(sys.argv[2])

    with open(email_creds, 'r') as fh:
        data = json.load(fh)
        username = data['username']
        password = data['password']
        host = data['host']
        port = data['port']
        label = data['label']

    mail = EmailClient(username, password, label, host, port)
    ids = mail.get_ids()
    # print(ids)
    mail_content = mail.get_email(ids[0])
    mail_content = mail_content.decode('utf-8', errors='ignore')
    mail_content = mail_content.splitlines()

    header = []
    html_content = []
    for i, l in enumerate(mail_content):
        if l.startswith("<!DOCTYPE html"):
            break
    
    mail_header, mail_content = mail_content[:i], mail_content[i:-1]

    for line in mail_header:
        if "Subject:" in line or "Date:" in line:
            print(line)

    mail_header = "\n".join(mail_header)
    html_content = "\n".join(mail_content)
    
    outfile = os.path.join(outdir, "mail_header.txt")
    # check if email was already used
    if same_content(mail_header, outfile):
        print("This email was already used")
        exit(1)
    else:
        with open(outfile, 'w') as fh:
            fh.write(mail_header)

        outfile = os.path.join(outdir, "mail_html.html")
        with open(outfile, 'w') as fh:
            fh.write(html_content)


if __name__ == "__main__":
    main()