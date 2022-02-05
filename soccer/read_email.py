import imaplib
from operator import imatmul
import os
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


def download_email(email_client, mail_id, outdir):
    mail_id_str = mail_id.decode('utf-8')


    mail_content = email_client.get_email(mail_id)
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
        if "Message-ID:" in line:
            message_id = line.split()[-1][1:-1]
    print(message_id)
    
    mail_header_fname = os.path.join(outdir, f"{message_id}.header")
    mail_html_fname = os.path.join(outdir, f"{message_id}.html")

    mail_header = "\n".join(mail_header)
    html_content = "\n".join(mail_content)
    
    # check if email was already used
    if same_content(mail_header, mail_header_fname):
        print("This email was already used\n")
        return None
    else:
        with open(mail_header_fname, 'w') as fh:
            fh.write(mail_header)

        with open(mail_html_fname, 'w') as fh:
            fh.write(html_content)
        return mail_header_fname, mail_html_fname


def check_email(email_creds, outdir):
    email_creds = os.path.expanduser(email_creds)
    outdir = os.path.expanduser(outdir)

    with open(email_creds, 'r') as fh:
        data = json.load(fh)
        username = data['username']
        password = data['password']
        host = data['host']
        port = data['port']
        label = data['label']

    email_client = EmailClient(username, password, label, host, port)
    new_emails = []
    for mail_id in email_client.get_ids():
        fname = download_email(email_client, mail_id, outdir)
        if fname is not None:
            new_emails.append(fname)
    return new_emails


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <email_creds_file> <outdir>")
        exit(1)
    
    email_creds = sys.argv[1]
    outdir = sys.argv[2]
    check_email(email_creds, outdir)