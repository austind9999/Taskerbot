import praw
import html
import logging
import re
import sys
import time
import datetime

from praw import Reddit
from praw.models.reddit.comment import Comment
from praw.models.reddit.submission import Submission
from praw.models.reddit.submission import SubmissionFlair
from praw.models.reddit.subreddit import SubredditModeration
import yaml


class Bot(object):

    def __init__(self, r):
        self.r = r
        logging.info('Success.')
        self.subreddits = {}
        for subreddit in SUBREDDITS:
            logging.info('Checking subreddit: %s…', subreddit)
            self.subreddits[subreddit] = {}
            sub = self.subreddits[subreddit]
            logging.info('Loading mods…')
            sub['mods'] = list(mod.name for mod in
                               self.r.subreddit(subreddit).moderator())
            logging.info('Mods loaded: %s.', sub['mods'])
            logging.info('Loading reasons…')
            sub['reasons'] = yaml.load(html.unescape(
                self.r.subreddit(subreddit).wiki['taskerbot'].content_md))
            logging.info('Reasons loaded.')

    def refresh_sub(self, subreddit):
        logging.info('Refreshing subreddit: %s…', subreddit)
        sub = self.subreddits[subreddit]
        logging.info('Loading mods…')
        sub['mods'] = list(mod.name for mod in
                           self.r.subreddit(subreddit).moderator())
        logging.info('Mods loaded: %s.', sub['mods'])
        logging.info('Loading reasons…')
        sub['reasons'] = yaml.load(html.unescape(
            self.r.subreddit(subreddit).wiki['taskerbot'].content_md))
        logging.info('Reasons loaded.')
        
    def check_flairs(self, subreddit):
        logging.info('Checking subreddit flairs: %s…', subreddit)
        for log in self.r.subreddit(subreddit).mod.log(action="editflair", limit=50):
            mod = log.mod.name
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if log.target_fullname is not None and log.target_fullname.startswith('t3_'):
                submission = self.r.submission(id=log.target_fullname[3:])
                if not submission.link_flair_text:
                    continue
                report = {'reason': submission.link_flair_text, 'author': mod}
                self.handle_report(subreddit, report, submission, today)

    def handle_report(self, subreddit, report, target, today):
        sub = self.subreddits[subreddit]
        # Check for !rule command.
        match = re.search(r'!rule (\w*) *(.*)', report['reason'],
                          re.IGNORECASE)
        if match:
            rule = match.group(1)
            note = match.group(2)
            logging.info('Rule %s matched.', rule)
            if rule not in sub['reasons']:
                rule = 'Generic'
            msg = sub['reasons'][rule]['Message']
            if note:
                msg = '{}\n\n{}'.format(msg, note)

            if 'source' in report is not None:
                report['source'].mod.remove()
            target.mod.remove()
            
            if target.author.name is not None:
                authorname = target.author.name 
            if target.author.name is None: 
                authorname = "OP"
            
            if isinstance(target, Submission):
                logging.info('Removed submission.')
                header = sub['reasons']['Header'].format(
                    author=authorname)
                footer = sub['reasons']['Footer'].format(
                    author=authorname)
                msg = '{header}\n\n{msg}\n\n{footer}'.format(
                    header=header, msg=msg, footer=footer)
                target.reply(msg).mod.distinguish(sticky=True)
                target.mod.flair(sub['reasons'][rule]['Flair'])
                permalink = target.permalink
            elif isinstance(target, Comment):
                logging.info('Removed comment.')
                permalink = target.permalink(fast=True)

        #    self.log(subreddit, '\n\n{} removed {} on {} EST'.format(
        #        report['author'], permalink, today))

    def log(self, subreddit, msg):
        logs_page = self.r.subreddit(subreddit).wiki['taskerbot_logs']
        try:
            logs_content = logs_page.content_md
        except TypeError:
            logs_content = ""
        logs_page.edit("{}{}  \n".format(logs_content, msg))

    def check_mail(self):
        logging.info('Checking mail…')
        for mail in self.r.inbox.unread():
            mail.mark_read()
            logging.info('New mail: "%s".', mail.body)
            match = re.search(r'!refresh (.*)', mail.body, re.IGNORECASE)
            if not match:
                continue
            subreddit = match.group(1)
            if subreddit in self.subreddits:
                sub = self.subreddits[subreddit]
                if mail.author in sub['mods']:
                    self.refresh_sub(subreddit)
                    mail.reply(
                        "Refreshed mods and reasons for {}!".format(subreddit))
                else:
                    mail.reply(
                        ("Unauthorized: not an r/{} mod").format(subreddit))
            else:
                mail.reply("Unrecognized sub:  {}.".format(subreddit))

    def run(self):
        while True:
            logging.info('Running cycle…')
            for subreddit in SUBREDDITS:
                try:
                  #  self.check_comments(subreddit)
                    self.check_flairs(subreddit)
                  #  self.check_reports(subreddit)
                    self.check_mail()
                except Exception as exception:
                    logging.exception(exception)
            logging.info('Sleeping…')
            time.sleep(32) # PRAW caches responses for 30s.


if __name__ == '__main__':
    with open('config.yaml') as config_file:
        CONFIG = yaml.load(config_file)
        CLIENT_ID = CONFIG['Client ID']
        CLIENT_SECRET = CONFIG['Client Secret']
        USERNAME = CONFIG['Username']
        PASSWORD = CONFIG['Password']
        SUBREDDITS = CONFIG['Subreddits']
        USER_AGENT = CONFIG['User Agent']

    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s')
    logging.info('Logging in…')
    MODBOT = Bot(Reddit(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
                        user_agent=USER_AGENT, username=USERNAME,
                        password=PASSWORD))
    MODBOT.run()
