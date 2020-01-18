import praw
import html
import logging
import re
import sys
import time
import datetime

import jsonschema
from praw import Reddit
from praw.models.reddit.comment import Comment
from praw.models.reddit.submission import Submission
from praw.models.reddit.submission import SubmissionFlair
from praw.models.reddit.subreddit import SubredditModeration
from prawcore.exceptions import NotFound
import yaml


REGEX_RULE = re.compile(r"[!]rule (\w*) *(.*)", re.IGNORECASE)
REGEX_REFRESH = re.compile(r"[!]refresh (.*)", re.IGNORECASE)

SCHEMA_VALIDATOR = jsonschema.Draft7Validator(
    yaml.safe_load(
        r"""
        type: object
        required:
            - Header
            - Footer
            - Generic
        properties:
            Header:
                type: string
            Footer:
                type: string
        additionalProperties:
            type: object
            properties:
                Flair:
                    type: string
                Message:
                    type: string
        propertyNames:
            pattern: "^\\w+$"
        """
    )
)


class Bot(object):
    def __init__(self, r):
        self.r = r
        logging.debug("Success.")
        self.logging_enabled = True
        self.subreddits = {}
        for subreddit in SUBREDDITS:
            logging.info("Checking subreddit: %s…", subreddit)
            mods, reasons = self.load_sub_config(subreddit)
            self.subreddits[subreddit] = {
                "mods": mods,
                "reasons": reasons,
            }

    def load_sub_config(self, subreddit):
        logging.debug("Loading mods…")
        mods = [mod.name for mod in self.r.subreddit(subreddit).moderator()]
        logging.info("Mods loaded: %s.", mods)
        logging.debug("Loading reasons…")
        try:
            reasons = yaml.safe_load(
                html.unescape(
                    self.r.subreddit(subreddit).wiki["taskerbot"].content_md
                )
            )
            SCHEMA_VALIDATOR.validate(reasons)
            logging.info("Reasons loaded.")
        except (jsonschema.exceptions.ValidationError, NotFound):
            reasons = None
            logging.warning(
                "r/%s/wiki/taskerbot not found or invalid, ignoring", subreddit
            )
        return mods, reasons
            
    def refresh_sub(self, subreddit):
        logging.info("Refreshing subreddit: %s…", subreddit)
        mods, reasons = self.load_sub_config(subreddit)
        sub = self.subreddits[subreddit]
        sub["mods"] = mods
        if reasons is not None:
            sub["reasons"] = reasons
        
    def check_flairs(self, subreddit):
        logging.info('Checking subreddit flairs: %s…', subreddit)
        for log in self.r.subreddit(subreddit).mod.log(action="editflair", limit=75):
            mod = log.mod.name
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if log.target_fullname is not None and log.target_fullname.startswith('t3_'):
                submission = self.r.submission(id=log.target_fullname[3:])
                if not submission.link_flair_text:
                    continue
                    
                report = {
                    "source": None,
                    "reason": submission.link_flair_text,
                    "author": mod,
                }
                self.handle_report(subreddit, report, submission, today)
 
    def handle_report(self, subreddit, report, target, today):
        sub = self.subreddits[subreddit]
        # Check for !rule command.
        match = REGEX_RULE.search(report["reason"])
        if match:
            rule = match.group(1)
            note = match.group(2)
            logging.info("Rule %s matched.", rule)
            if rule not in sub["reasons"]:
                rule = "Generic"
            msg = sub["reasons"][rule]["Message"]
            if note:
                msg = f"{msg}\n\n{note}"

            if report["source"] is not None:
                report["source"].mod.remove()
            target.mod.remove()

            author = target.author.name if target.author is not None else "OP"
            header = sub["reasons"]["Header"].format(author=author)
            footer = sub["reasons"]["Footer"].format(author=author)
            msg = f"{header}\n\n{msg}\n\n{footer}"
            target.reply(msg).mod.distinguish(sticky=True)

            if isinstance(target, Submission):
                logging.info("Removed submission.")
                target.mod.flair(sub["reasons"][rule]["Flair"])
            elif isinstance(target, Comment):
                logging.info("Removed comment.")

            permalink = target.permalink

            self.log(subreddit, '\n\n{} removed {} on {} EST'.format(
                report['author'], permalink, today))

    def log(self, subreddit, msg):
        if not self.logging_enabled:
            return
        logs_page = self.r.subreddit(subreddit).wiki["taskerbot_logs"]
        try:
            logs_content = logs_page.content_md
        except TypeError:
            logs_content = ""
        except NotFound:
            logging.warning(
                "r/%s/wiki/taskerbot_logs not found, disabling logging",
                subreddit,
            )
            self.logging_enabled = False
            return
        logs_page.edit(f"{logs_content}{msg}  \n")

    def check_mail(self):
        logging.debug("Checking mail…")
        for mail in self.r.inbox.unread():
            mail.mark_read()
            logging.info('New mail: "%s".', mail.body)
            match = REGEX_REFRESH.search(mail.body)
            if not match:
                continue
            subreddit = match.group(1)
            if subreddit in self.subreddits:
                sub = self.subreddits[subreddit]
                if mail.author in sub["mods"]:
                    self.refresh_sub(subreddit)
                    mail.reply(f"Refreshed mods and reasons for {subreddit}!")
                else:
                    mail.reply(f"Unauthorized: not an r/{subreddit} mod")
            else:
                mail.reply(f"Unrecognized sub: {subreddit}.")
    
    def run(self):
        while True:
            logging.debug("Running cycle…")
            for subreddit in SUBREDDITS:
                if self.subreddits[subreddit]["reasons"] is None:
                    continue
                try:
                    self.check_flairs(subreddit)
                except Exception as exception:
                    logging.exception(exception)
            try:
                self.check_mail()
            except Exception as exception:
                logging.exception(exception)
            logging.debug("Sleeping…")
            time.sleep(32)  # PRAW caches responses for 30s.

if __name__ == "__main__":
    with open("config.yaml") as config_file:
        CONFIG = yaml.safe_load(config_file)
        CLIENT_ID = CONFIG["Client ID"]
        CLIENT_SECRET = CONFIG["Client Secret"]
        USERNAME = CONFIG["Username"]
        PASSWORD = CONFIG["Password"]
        SUBREDDITS = CONFIG["Subreddits"]
        USER_AGENT = CONFIG["User Agent"]

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )
    logging.info("Logging in…")
    MODBOT = Bot(
        Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
            username=USERNAME,
            password=PASSWORD,
        )
    )
    MODBOT.run()
