import praw
import smtplib
import requests
import parsel
import re
import io
import json
import os
import datetime

from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from argparse import ArgumentParser
from premailer import Premailer

from prefect import task, Flow
from prefect.client import Secret
from prefect.triggers import any_failed

HEADERS = requests.utils.default_headers()
HEADERS.update(
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0"
    }
)

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
REDDIT_CSS = os.path.join(SCRIPT_PATH, "css", "reddit.css")


@task(name="Fetch User Subreddits")
def user_subreddits():
    app_id = Secret("REDDIT_DAILY_APP_ID").get()
    app_secret = Secret("REDDIT_DAILY_APP_SECRET").get()
    refresh_token = Secret("REDDIT_DAILY_REFRESH_TOKEN").get()

    reddit = praw.Reddit(
        client_id=app_id,
        client_secret=app_secret,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0",
        refresh_token=refresh_token,
    )
    return list(reddit.user.subreddits())


def _concat_css(input_name, output):
    with open(input_name, encoding="utf-8") as f:
        output.write("\n<style>\n")
        output.write(f.read())
        output.write("\n</style>\n")


def _extract_external_css(selector):
    for p in selector.xpath("/html/head/link[@rel='stylesheet']"):
        href = re.sub(r"^//", r"https://", p.xpath("@href").extract_first())
        sheet = requests.get(href, headers=HEADERS).text if href else ""
        yield sheet


@task(name="Extract Top Posts")
def weekly_page(subreddit):
    css = REDDIT_CSS
    subreddit = subreddit.display_name

    response = requests.get(
        "https://old.reddit.com/r/{}/top/?sort=top&t=day".format(subreddit),
        headers=HEADERS,
    )

    if response.status_code != 200:
        raise RuntimeError("Request status code is {}.".format(response.status_code))
    if response.encoding.lower() != "utf-8":
        raise RuntimeError("Request didn't return a UTF-8 output.")

    sel = parsel.Selector(text=response.text)

    file = io.StringIO()

    file.write("<!DOCTYPE html>")
    file.write("<html>")

    if css == 1:  # Download External
        file.write("<head>")
        file.write(
            '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">'
        )
        for stylesheet in _extract_external_css(sel):
            file.write("\n<style>\n")
            file.write(stylesheet)
            file.write("\n</style>\n")
        file.write("</head>")
    elif css == 2:  # Keep External
        head = sel.xpath("/html/head").extract_first()
        head = re.sub(r'="//', '="https://', head)
        file.write(head)
    elif isinstance(css, str):
        file.write("<head>")
        file.write(
            '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">'
        )
        _concat_css(css, file)
        file.write("</head>")
    elif isinstance(css, list):
        file.write("<head>")
        file.write(
            '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">'
        )
        for c in css:
            _concat_css(c, file)
        file.write("</head>")
    else:
        file.write("<head>")
        file.write(
            '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">'
        )
        file.write("</head>")

    file.write('<body class="">')
    file.write('<div class="content" role="main">')

    for spacer in sel.xpath(
        "/html/body/div[@class='content']/div[@class='spacer' and style]"
    ):
        content = spacer.extract()
        content = re.sub(r'="//', r'="https://', content)
        file.write(content)

    file.write("</div>")
    file.write("</body>")

    file.write("</html>")

    file.seek(0)

    return file


@task(name="Format Email")
def format_email(email_body):
    email_body_stage_1 = Premailer(
        email_body.getvalue(),
        base_url="https://www.reddit.com",
        disable_leftover_css=True,
    )
    email_body_stage_2 = email_body_stage_1.transform()
    return email_body_stage_2


# , max_retries=5, retry_delay=datetime.timedelta(minutes=5)
@task(name="Send Email")
def send_email(subreddit, message):
    subject = "Reddit weekly r/{}".format(subreddit)
    email_address = Secret("REDDIT_DAILY_EMAIL").get()
    password = Secret("REDDIT_DAILY_EMAIL_PASSWORD").get()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = email_address
    msg["To"] = email_address

    msg.attach(MIMEText("Daily Subreddit", "plain"))
    msg.attach(MIMEText(message, "html"))

    with smtplib.SMTP(host="smtp.gmail.com", port=587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(email_address, password)
        server.sendmail(email_address, [email_address], msg.as_string())


@task(name="Failure Slack Notification", trigger=any_failed)
def send_failure_notice():
    print("This task is a stand-in for sending a real slack message, fix it Dylan")


with Flow("Reddit Daily") as flow:
    subreddits = user_subreddits()
    email_bodies = weekly_page.map(subreddits)
    formatted_email_bodies = format_email.map(email_bodies)
    results = send_email.map(subreddit=subreddits, message=formatted_email_bodies)
    send_failure_notice(upstream_tasks=[results])
    flow.set_reference_tasks([results])


# TODO Add task that runs only if upstream tasks fail that slacks me if something broke
# TODO Reduce the text files into one text file and email that

