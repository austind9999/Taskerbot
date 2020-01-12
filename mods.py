import praw

from praw import reddit
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
            
    def check_flairs(self, subreddit):
        logging.info('Checking subreddit flairs: %s…', subreddit)
        for log in reddit.subreddit('mod').mod.log(limit=50):
            print("Mod: {}, Subreddit: {}".format(log.mod, log.subreddit))

    def run(self):
        while True:
            logging.info('Running cycle…')
            for subreddit in SUBREDDITS:
                try:
                    self.check_flairs(subreddit)
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
