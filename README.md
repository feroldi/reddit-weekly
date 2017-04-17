# Reddit-weekly

Reddit-weekly was born from the idea of getting a weekly
newsletter from subreddits, so you don't have to
browse it every other day.

# Usage

    python rewe.py --users database.json

The script will read a json file (a set of emails and
reddit refresh tokens), then proceed to get a page of
each subreddit a user is subscribed to, and send it
to their email.

You can use your own app (id and secret) if you want
to run it by yourself.

# Environment variables

+ `REMAILME_SENDER`: sender's email.
+ `REMAILME_PASS`: sender's email password.
+ `REMAILME_APP_ID`: reddit's app client id.
+ `REMAILME_APP_SECRET`: reddit's app client secret.

# License

This project is licensed under the MIT license. See LICENSE.

