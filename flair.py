import praw
import yaml
import logging
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

subreddit = r.subreddit('memes')  # do not include /r/

remove_flair1 = '1. ALL POSTS MUST BE MEMES'
remove_flair2 = '2. ALL MEMES SHOULD BE GENERAL. NO SPECIFIC PERSONAL EXPERIENCES'
remove_flair3 = '3. NO SPAM/WATERMARKS, CHAINPOSTING/SPLIT POSTS, UNMARKED NSFW'
remove_flair4 = '4. NO RACISM/HATE SPEECH/TROLLING/HARRASSMENT/BRIGADING'
remove_flair5 = '5. PLEASE DO NOT POST OR REQUEST PERSONAL INFORMATION'
remove_flair6 = '6. DIRECT IMAGE LINKS ONLY + NO GIF/VIDEO POSTS'
remove_flair7 = '7. DO NOT MENTION ANYTHING TO DO WITH KARMA/CAKEDAYS/VOTES/ETC'
remove_flair8 = '8. NO REPOSTS'
remove_flair9 = '9. NO FORCED MEMES/OVERUSED MEMES/BAD TITLES/PUSHING AGENDAS'
remove_flair10 = '10. NO MEMES ABOUT DEATHS/TERROR ATTACKS/WAR/VIOLENT TRAGEDIES'
remove_flair11 = '11. NO MEMES ABOUT POLITICS'
 
def main():
    stream = subreddit.stream.submissions()
    try:
        for post in stream:
            if not post.link_flair_text: continue
            if post.link_flair_text.lower() == remove_flair1.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 1')
            elif post.link_flair_text.lower() == remove_flair2.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 2')
            elif post.link_flair_text.lower() == remove_flair3.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 3')
            elif post.link_flair_text.lower() == remove_flair4.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 4')
            elif post.link_flair_text.lower() == remove_flair5.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 5')
            elif post.link_flair_text.lower() == remove_flair6.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 6')
            elif post.link_flair_text.lower() == remove_flair7.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 7')
            elif post.link_flair_text.lower() == remove_flair8.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 8')
            elif post.link_flair_text.lower() == remove_flair9.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 9')
            elif post.link_flair_text.lower() == remove_flair10.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 10')
            elif post.link_flair_text.lower() == remove_flair11.lower():
                print('removing {0}'.format(post.shortlink))
                post.report('!rule 11')
    except Exception as e:
        print('### exception: {0}'.format(str(e)))
        sleep(32)

if __name__ == '__main__':
    main()
