from prefect import Client
from prefect.schedules import CronSchedule
from reddit_daily import flow

c = Client()
s = CronSchedule("0 * * * *")

flow.schedule = s

flow.deploy(project="Dylan's Project")
