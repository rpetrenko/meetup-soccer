* example of .gmail_creds
```json
{
    "username": "XXX@gmail.com",
    "password": "XXX",
    "host": "smtp.gmail.com",
    "port": 993,
    "label": "soccer"
}
```

* example of .meetup_creds
```json
{
    "username": "XXX@gmail.com",
    "password": "XXX"
}
```

* get emails
```bash
python read_email.py ~/.gmail_creds ~/meetup-out/
```

* RSVP to meetup event
```bash
python meetup.py ~/.meetup_creds ~/meetup-out/mail_html.html
```