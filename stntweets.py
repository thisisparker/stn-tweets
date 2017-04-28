#!/usr/bin/env python3
# Grabs the current results of the Secure The News scorecard API,
# compares them to the previous results, and tweets about the
# differences.

import random, json, yaml, os, time, requests
from twython import Twython, TwythonError

fullpath = os.path.dirname(os.path.realpath(__file__))
CONFIG = os.path.join(fullpath, "config.yaml")

def get_config():
    with open(CONFIG,'r') as c:
        config = yaml.load(c)
    return config

def get_twitter_instance(config):
    twitter_app_key = config['twitter_app_key']
    twitter_app_secret = config['twitter_app_secret']
    twitter_oauth_token = config['twitter_oauth_token']
    twitter_oauth_token_secret = config['twitter_oauth_token_secret']
    return Twython(twitter_app_key, twitter_app_secret, twitter_oauth_token, twitter_oauth_token_secret)

def write_results(results,path):
    with open(path,"w") as f:
        json.dump(results, f, indent = 4)

def available_over_https(site):
    if (site['valid_https']
        and not site['downgrades_https']):
        return True
    else:
        return False

def compare_results(old_site, new_site):

    site_tweets = []

    if old_site == None:
         site_tweets.append("🤖 We're tracking a new site on @SecureTheNews: " + new_site['name'] + " has a grade of " + new_site['grade'] + ". " + new_site['url'])
         return site_tweets

    if (new_site['grade'] != old_site['grade'] and 
        new_site['score'] > old_site['score']):

         site_tweets.append("🤖 " + new_site['name'] + " has improved its grade on the @SecureTheNews leaderboard from " + old_site['grade'] + " to " + new_site['grade'] + ". " + new_site['url'])

    if (available_over_https(new_site)
        and not available_over_https(old_site)):

        site_tweets.append("🤖 " + new_site['name'] + " is now available over HTTPS! Next step: turn it on by default. https://securethe.news/sites")

    if (new_site['defaults_to_https']
        and not old_site['defaults_to_https']):

        site_tweets.append("🤖 Great news: " + new_site['name'] + " is now using HTTPS by default! Huge win for reader privacy and security. https://securethe.news/sites")

    if (new_site['hsts'] and not old_site['hsts']):

        site_tweets.append("🤖 " + new_site['name'] + " is now using HSTS headers. This means browsers will connect to it more securely. Yes! https://securethe.news/sites")

    if (new_site['hsts_preloaded'] 
        and not old_site['hsts_preloaded']):

        site_tweets.append("🤖 " + new_site['name'] + " is now on the HSTS preload list for major browsers, protecting user privacy. Bravo. https://securethe.news/sites")

    return site_tweets

def tweet_results(tweets, twitter):
    to_sleep = False

    for site in tweets:
        if to_sleep:
            time.sleep(1800)
        else:
            to_sleep = True

        reply_to = 'null'

        for item in site:
            if reply_to != 'null':
                time.sleep(30)

            try:
                response = twitter.update_status(status=item,
                    in_reply_to_status_id=reply_to)
                reply_to = response['id_str']

            except TwythonError as err:
                twitter.send_direct_message(screen_name=botmaster,
                    text="I tried to tweet " + item + 
                    " but got the error " + str(err))

def main():
    config = get_config()
    twitter = get_twitter_instance(config)
    botmaster = config['botmaster']

    results = requests.get("https://securethe.news/api/v1/sites/?limit=1000").json()['results']

    tweets = list()
    new_results = list()

    for site in results:
        new_results.append({'name':site['name'],
            'grade':site['latest_scan']['grade'],
            'score':site['latest_scan']['score'],
            'valid_https':site['latest_scan']['valid_https'],
            'downgrades_https':
                site['latest_scan']['downgrades_https'],
            'defaults_to_https':
                site['latest_scan']['defaults_to_https'],
            'hsts':site['latest_scan']['hsts'],
            'hsts_preloaded':site['latest_scan']['hsts_preloaded'],
            'url':'https://securethe.news/sites/' + site['slug']})

# Open existing results to compare to the new ones, if they exist.
# If not, save the new ones and we'll compare later.

    results_path = os.path.join(fullpath, "old_results.json")

    if os.path.exists(results_path):
        with open(results_path,"r") as f:
            old_results = json.load(f)

# This is the main comparison loop. It takes one site at a time and
# compares the properties of `new_site` to `old_site`.
# If it finds differences, it saves those to a list of tweets.

        for new_site in new_results:

            old_site = next((s for s in old_results if s['name'] == new_site['name']), None)

            site_tweets = compare_results(old_site, new_site)

# After all the comparisons, add the collected differences as a list
# to the `tweets` list.

            if len(site_tweets) > 0:
                tweets.append(site_tweets)

# The tweeting loop.

        if len(tweets) == 0:
            twitter.send_direct_message(screen_name=botmaster,
                text="I would've sent a message, but nothing changed!")

        tweet_results(tweets, twitter)

        write_results(new_results, results_path)

    else:
        old_results = new_results
        write_results(old_results, results_path)
        print("Created a new baseline. Comparison will be made later.")

if __name__ == "__main__":
    main()
