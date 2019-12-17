import praw
import yaml
from time import sleep
from praw.models.reddit.submission import Submission

if __name__ == '__main__':
    with open('config.yaml') as config_file:
        CONFIG = yaml.load(config_file)
        CLIENT_ID = CONFIG['Client ID']
        CLIENT_SECRET = CONFIG['Client Secret']
        USERNAME = CONFIG['Username']
        PASSWORD = CONFIG['Password']
        SUBREDDITS = CONFIG['Subreddits']
        USER_AGENT = CONFIG['User Agent']

r = praw.Reddit(client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                username=USERNAME,
                password=PASSWORD,
                user_agent=USER_AGENT)

subreddit = r.subreddit('memesmod')  # do not include /r/
 
remove_flair = '!rule 1'
 
 
def main():
    stream = subreddit.stream.submissions()
    try:
        for post in stream:
            if not post.link_flair_text: continue
            if post.link_flair_text.lower() == remove_flair.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 1')
    except Exception as e:
        print('### exception: {0}'.format(str(e)))
        sleep(60)
 
 
if __name__ == '__main__':
    main()
