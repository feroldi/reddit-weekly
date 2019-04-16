from prefect import Client
from prefect.schedules import CronSchedule
from rewe import flow

c = Client()
s = CronSchedule("0 * * * *")

flow.schedule = s

flow.deploy(project="Dylan's Project")
