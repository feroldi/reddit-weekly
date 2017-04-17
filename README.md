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

In order to send an email, it is necessary to
have an existing email account, so that there is
an actual sender.

# Setup

Firstly, go to [reddit apps](https://www.reddit.com/prefs/apps/) and
register a new app. You'll need the personal use script id,
and the secret. In case you aren't sure about the authentication
process, [read about it here](https://praw.readthedocs.io/en/latest/getting_started/authentication.html).
Next step is to create an email account. Currently, the script is
using Gmail to log in, but there are plans (#3) to provide
a way to plug-in a back-end that takes care of the emailing part.

Then, you need to generate your reddit's refresh token.
The easiest way is to run [this](https://praw.readthedocs.io/en/latest/tutorials/refresh_token.html#refresh-token)
script. This token is used for authentication to get a reddit account's subreddits.

**Note**: only the `identity` and `mysubreddits` scopes are necessary
from a user's account, so when this message come up:

    Now enter a comma separated list of scopes, or all for all tokens:

Just enter with `identity,mysubreddits`.

Export all variables used by the script. For example:

    export REMAILME_SENDER='place sender email here'
    export REMAILME_PASS='place sender password gere'
    export REMAILME_APP_ID='place client id here'
    export REMAILME_APP_SECRET='place client secret here'

Create a json file (let's call it `database.json`) with all the desired
target emails (emails to send the newsletter to), and their respective refresh token.

    {
        "example1@mail_one.com": "refresh token 1",
        "example2@mail_two.com": "refresh token 2"
        // etc...
    }

Only then you can run it:

    ./rewe.py --users database.json

And it will proceed to send a newsletter to each email
in the json file.

# Environment variables

+ `REMAILME_SENDER`: sender's email.
+ `REMAILME_PASS`: sender's email password.
+ `REMAILME_APP_ID`: reddit's app client id.
+ `REMAILME_APP_SECRET`: reddit's app client secret.

# How does it look like

Screenshot of newsletter from r/programming:

![reddit-weekly](http://i.imgur.com/QEyqKYs.png)

# License

This project is licensed under the MIT license. See LICENSE.

