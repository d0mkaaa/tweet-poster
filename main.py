import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QDateTimeEdit, QListWidget, QListWidgetItem, QMenu, QAction
from PyQt5.QtCore import QDateTime, Qt, QTimer
import requests
from requests_oauthlib import OAuth1
import os
import schedule
import time
import threading

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

consumer_key = config['consumer_key']
consumer_secret = config['consumer_secret']
access_token = config['access_token']
access_token_secret = config['access_token_secret']

class ScheduledTweet:
    def __init__(self, time, text, sent=False):
        self.time = time
        self.text = text
        self.sent = sent

class TweetSchedulerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.scheduled_tweets = []
        self.timer_thread = threading.Thread(target=self.schedule_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        self.check_schedule_timer = QTimer()
        self.check_schedule_timer.timeout.connect(self.check_schedule)
        self.check_schedule_timer.start(1000)

    def initUI(self):
        self.setWindowTitle('made by lmaoleonix')
        self.setGeometry(100, 100, 600, 400)

        self.layout = QVBoxLayout()

        self.tweet_label = QLabel('Tweet Text:')
        self.tweet_input = QLineEdit()
        self.layout.addWidget(self.tweet_label)
        self.layout.addWidget(self.tweet_input)

        self.time_label = QLabel('Scheduled Time:')
        self.time_input = QDateTimeEdit()
        self.time_input.setDateTime(QDateTime.currentDateTime())
        self.layout.addWidget(self.time_label)
        self.layout.addWidget(self.time_input)

        self.schedule_button = QPushButton('Schedule Tweet')
        self.schedule_button.clicked.connect(self.schedule_tweet)
        self.layout.addWidget(self.schedule_button)

        self.tweet_list = QListWidget()
        self.layout.addWidget(self.tweet_list)

        self.setLayout(self.layout)

        style_sheet = """
            QWidget {
                background-color: #ffffff;
                font-family: Arial, sans-serif;
            }
            QLabel {
                font-size: 16px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QListWidget {
                background-color: #f2f2f2;
            }
            QListWidget:item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """
        self.setStyleSheet(style_sheet)

    def post_tweet(self, tweet_text):
        oauth = OAuth1(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )

        data = {
            "text": tweet_text,
        }

        response = requests.post(
            "https://api.twitter.com/2/tweets",
            auth=oauth,
            json=data,
        )

        if response.status_code == 201:
            print("Tweet posted successfully!")
            return True
        else:
            print(f"Error posting tweet: {response.status_code} - {response.text}")
            return False

    def schedule_tweet(self):
        tweet_text = self.tweet_input.text()
        scheduled_time = self.time_input.dateTime().toString("HH:mm")

        current_time = QDateTime.currentDateTime().toString("HH:mm")
        if scheduled_time <= current_time:
            sent = self.post_tweet(tweet_text)
            scheduled_tweet = ScheduledTweet(current_time, tweet_text, sent)
            self.scheduled_tweets.append(scheduled_tweet)
            self.add_to_tweet_list(f"{current_time}: {tweet_text} (Sent: {sent})")
        else:
            def post_scheduled_tweet():
                sent = self.post_tweet(tweet_text)
                scheduled_tweet = ScheduledTweet(scheduled_time, tweet_text, sent)
                self.scheduled_tweets.append(scheduled_tweet)
                self.add_to_tweet_list(f"{scheduled_time}: {tweet_text} (Sent: {sent})")

            schedule.every().day.at(scheduled_time).do(post_scheduled_tweet)

        self.tweet_input.clear()
        print(f"Tweet scheduled for {scheduled_time}")

    def add_to_tweet_list(self, text):
        item = QListWidgetItem(text)
        self.tweet_list.addItem(item)

    def schedule_timer(self):
        while True:
            schedule.run_pending()
            time.sleep(1)

    def check_schedule(self):
        current_time = QDateTime.currentDateTime().toString("HH:mm")
        for tweet in self.scheduled_tweets:
            if tweet.time <= current_time and not tweet.sent:
                sent = self.post_tweet(tweet.text)
                tweet.sent = sent
                self.update_tweet_list_item(tweet)

    def update_tweet_list_item(self, tweet):
        items = self.tweet_list.findItems(f"{tweet.time}: {tweet.text}", Qt.MatchExactly)
        if items:
            item = items[0]
            item.setText(f"{tweet.time}: {tweet.text} (Sent: {tweet.sent})")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TweetSchedulerApp()
    window.show()
    sys.exit(app.exec_())
