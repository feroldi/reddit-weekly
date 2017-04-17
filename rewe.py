#!/bin/python3

import praw
import smtplib
import requests
import parsel
import re
import io
import json
import os

from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from argparse import ArgumentParser

def weekly_page(subreddit, file):
    headers = requests.utils.default_headers()
    headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0'})
    
    r = requests.get(f"https://www.reddit.com/r/{subreddit}/top/?sort=top&t=week",
                     headers=headers)

    assert r.status_code == 200
    assert r.encoding.lower() == 'utf-8'

    sel = parsel.Selector(text=r.text)

    file.write('<!DOCTYPE html>')
    file.write('<html>')

    head = sel.xpath("/html/head").extract_first()
    head = re.sub(r'="//', '="https://', head)
    file.write(head)

    file.write('<body>')
    for spacer in sel.xpath("/html/body/div[@class='content']/div[@class='spacer' and style]"):
        content = spacer.extract()
        content = re.sub(r'="//', r'="https://', content)
        file.write(content)
    file.write('</body>')
    file.write('</html>')

def send_email(subject, toaddr, message):
    fromaddr = os.environ['REMAILME_SENDER']
    frompass = os.environ['REMAILME_PASS']

    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = fromaddr
    msg['To'] = toaddr

    msg.attach(MIMEText('Weekly Subreddit', 'plain'))
    msg.attach(MIMEText(message, 'html'))

    with smtplib.SMTP(host='smtp.gmail.com', port=587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(fromaddr, frompass)
        server.sendmail(fromaddr, [toaddr], msg.as_string())

def user_subreddits(token):
    reddit = praw.Reddit(client_id=os.environ['REMAILME_APP_ID'],
                         client_secret=os.environ['REMAILME_APP_SECRET'],
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0',
                         refresh_token=token)
    return reddit.user.subreddits()

def send_newsletter(token, email):
    for subreddit in user_subreddits(token):
        subreddit = str(subreddit)
        with io.StringIO() as body:
            weekly_page(subreddit, body)
            send_email('Weekly r/' + subreddit + ' Subreddit',
                       email, body.getvalue())

def main(filepath):
    with io.open(filepath, 'r') as file:
        users = json.load(file)
        for email in users:
            token = users[email]
            send_newsletter(token, email)

# usage: ./rewe.py -u, --users=<json>

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-u', '--users')
    opt = parser.parse_args()
    main(opt.users)

