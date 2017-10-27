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
from premailer import Premailer

HEADERS = requests.utils.default_headers()
HEADERS.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0'})

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
REDDIT_CSS = os.path.join(SCRIPT_PATH, 'css', 'reddit.css')

def _concat_css(input_name, output):
    with open(input_name, encoding='utf-8') as f:
        output.write('\n<style>\n')
        output.write(f.read())
        output.write('\n</style>\n')

def _extract_external_css(selector):
    for p in selector.xpath("/html/head/link[@rel='stylesheet']"):
            href = re.sub(r"^//", r"https://", p.xpath("@href").extract_first())
            sheet = requests.get(href, headers=HEADERS).text if href else ""
            yield sheet

def weekly_page(subreddit, file, css=None):
    if isinstance(file, str):
        with open(file, 'w', encoding='utf-8') as f:
            return weekly_page(subreddit, file=f, css=css)

    r = requests.get("https://www.reddit.com/r/{}/top/?sort=top&t=week".format(subreddit),
                     headers=HEADERS)

    if r.status_code != 200:
        raise RuntimeError("Request status code is {}.".format(r.status_code))
    if r.encoding.lower() != 'utf-8':
        raise RuntimeError("Request didn't return a UTF-8 output.")

    sel = parsel.Selector(text=r.text)

    file.write('<!DOCTYPE html>')
    file.write('<html>')

    if css == 1: # Download External
        file.write('<head>')
        file.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">')
        for stylesheet in _extract_external_css(sel):
                file.write('\n<style>\n')
                file.write(stylesheet)
                file.write('\n</style>\n')
        file.write('</head>')
    elif css == 2: # Keep External
        head = sel.xpath("/html/head").extract_first()
        head = re.sub(r'="//', '="https://', head)
        file.write(head)
    elif isinstance(css, str):
        file.write('<head>')
        file.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">')
        _concat_css(css, file)
        file.write('</head>')
    elif isinstance(css, list):
        file.write('<head>')
        file.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">')
        for c in css:
            _concat_css(c, file)
        file.write('</head>')
    else:
        file.write('<head>')
        file.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">')
        file.write('</head>')

    file.write('<body class="">')
    file.write('<div class="content" role="main">')
    for spacer in sel.xpath("/html/body/div[@class='content']/div[@class='spacer' and style]"):
        content = spacer.extract()
        content = re.sub(r'="//', r'="https://', content)
        file.write(content)
    file.write('</div>')
    file.write('</body>')

    file.write('</html>')

def send_email(subject, to, message):
    fromaddr = os.environ['REWE_SENDER']
    frompass = os.environ['REWE_PASS']

    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = fromaddr
    msg['To'] = to

    msg.attach(MIMEText('Weekly Subreddit', 'plain'))
    msg.attach(MIMEText(message, 'html'))

    with smtplib.SMTP(host='smtp.gmail.com', port=587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(fromaddr, frompass)
        server.sendmail(fromaddr, [to], msg.as_string())

def user_subreddits(token):
    reddit = praw.Reddit(client_id=os.environ['REWE_APP_ID'],
                         client_secret=os.environ['REWE_APP_SECRET'],
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0',
                         refresh_token=token)
    return reddit.user.subreddits()

def send_newsletter(token, email):
    for subreddit in user_subreddits(token):
        subreddit = subreddit.display_name
        with io.StringIO() as body:
            print("Sending {} weekly for {}...".format(subreddit, email))
            weekly_page(subreddit, body, css=REDDIT_CSS)
            email_body = Premailer(body.getvalue(),
                                   base_url='https://www.reddit.com',
                                   disable_leftover_css=True).transform()
            send_email(subject='Reddit weekly r/{}'.format(subreddit),
                       to=email, message=email_body)

def main(filepath):
    with io.open(filepath, 'r') as file:
        users = json.load(file)
        for email in users:
            token = users[email]
            send_newsletter(token, email)

# usage: ./rewe.py -u, --users=<json>

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-u', '--users', required=True, help='load users and their tokens from a JSON file')
    opt = parser.parse_args()
    main(opt.users)

