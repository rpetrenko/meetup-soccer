import sys
import os
import time
from soccer.read_email import check_email
from soccer.meetup import meetup_auto_rsvp


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <email_creds_file> <meetup_creds_file> <outdir>")
        exit(1)
          
    email_creds = sys.argv[1]
    meetup_creds = sys.argv[2]
    outdir = sys.argv[3]

    new_emails = check_email(email_creds, outdir)

    for fname_header, fname_html in new_emails:
        fname_header = os.path.join(outdir, fname_header)
        fname_html = os.path.join(outdir, fname_html)
        print(f"=== Processing file {fname_html}")
        err = meetup_auto_rsvp(meetup_creds, fname_html, headless=True, wait=10)
        if err is not None:
            print("Something went wrong, deleting email header to retry next time")
            os.system(f"rm {fname_header}")
        time.sleep(10)
    else:
        print("no new messages")