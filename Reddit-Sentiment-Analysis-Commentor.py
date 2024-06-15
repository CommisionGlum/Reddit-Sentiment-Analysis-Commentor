import praw
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from textblob import TextBlob

parser = argparse.ArgumentParser(description="Reddit Sentiment Analysis tool")
parser.add_argument("--subreddit", help="Enter the subreddit that you would like to perform sentiment analysis on")
parser.add_argument("--debug", help="Enter Degub mode with extra notes about what is going on in the background")
args = parser.parse_args()

'''
repos/
├── Reddit-Sentiment-Analysis-Commentor/
│   └── Reddit-Sentiment-Analysis-Commentor.py
└── Reddit_API_Data/
    └── Reddit_API_JSON.json
'''

# Path to your JSON file
relative_path = Path("Reddit_API_Data\Reddit_API_JSON.json")
json_file_path = Path(__file__).resolve().parent.parent
combined = json_file_path / relative_path

with open(combined, 'r') as file:
    data = json.load(file)

debug = args.debug
# Initialize the Reddit instance
reddit = praw.Reddit(
    client_id=data["client_id"],
    client_secret=data["client_secret"],
    username=data["username"],
    password=data["password"],
    user_agent=data["user_agent"]
)

# Get the top posts from a subreddit
subreddit = reddit.subreddit(args.subreddit)

def main():
    for submission in subreddit.new(limit=5):
        datePosted = datetime.utcfromtimestamp(submission.created_utc)

        if(checkPostAlreadyPosted(submission.id) or submission.num_comments < 10):
            if(debug):
                print("the post has already been commented on")
        else:
            current_time = datetime.now()
            timeDifference = current_time - datePosted
            threshold = timedelta(hours = 3)
            if(timeDifference > threshold):
                queryString = ""
                submission.comments.replace_more(limit=0)

                mostBullishComment = ""
                bullishNumber = 0
                bearishNumber = 0
                mostBearishComment = ""
                numNeutral = 0
                numBullish = 0
                numBearish = 0
                totalSentiment = 0
                totalComments = 0

                for comment in submission.comments.list():
                    if(len(comment.body) <= 2 or str(comment.author) == "None"):
                        continue

                    commentBlob = TextBlob(str(comment.body))

                    commentSentiment = 0.0
                    totalSentances = 0
                    for sentence in commentBlob.sentences:
                        totalSentances += 1
                        commentSentiment += sentence.sentiment.polarity

                    commentAverageSentiment = float(commentSentiment) / float(totalSentances)
                    if(commentAverageSentiment > bullishNumber):
                        mostBullishComment = comment
                        bullishNumber = commentAverageSentiment
                    if(commentAverageSentiment < bearishNumber):
                        mostBearishComment = comment
                        bearishNumber = commentAverageSentiment
                    if(commentAverageSentiment > 0.05):
                        numBullish += 1
                    elif(commentAverageSentiment < -0.05):
                        numBearish += 1
                    else:
                        numNeutral += 1

                    totalSentiment = totalSentiment + commentAverageSentiment
                    totalComments += 1
                sentiment = ""
                if((totalSentiment / totalComments) > 0.1):
                    sentiment = "Positive"
                elif((totalSentiment / totalComments) < -0.1):
                    sentiment = "Negative"
                else:
                    sentiment = "Neutral"
                returnPostText = "*Note, this is data collected and MAY not be accurate*\n\n|Post Sentiment Table|Average Sentiment: " + sentiment + "|\n|:-|:-|\n|Positive|Negative|Neutral|\n|" + str(numBullish) + "|" + str(numBearish)  + "|" + str(numNeutral) + "|\n"
                if(numBullish > 0):
                    returnPostText = returnPostText + "\n**With the most postive comment being:** \n\n/u/" + str(mostBullishComment.author) + ": link: [" + mostBullishComment.body + "](https://www.reddit.com" + mostBullishComment.permalink + ")\n"
                if(numBearish > 0):
                    returnPostText = returnPostText + "\n**With the most negative comment being:** \n\n/u/" + str(mostBearishComment.author) + ": link: [" + mostBearishComment.body + "](https://www.reddit.com" + mostBearishComment.permalink + ")\n"
                comment = submission.reply(returnPostText)
                addPostsAlreadyPosted(submission.id)
            else:
                if(debug):
                    print("DO not post, it is too early " + str(current_time) + " " + str(datePosted))



def addPostsAlreadyPosted(search_string):
    file_path = "History-Post-Data_" + args.subreddit + ".txt"
    # Open the file in read mode
    with open(file_path, 'a+') as file:
        # Read the file line by line
        file.write(search_string + '\n')
    file.close()

def checkPostAlreadyPosted(search_string):
    file_path = "History-Post-Data_" + args.subreddit + ".txt"
    # Open the file in read mode
    try:
        with open(file_path, 'r') as file:
            # Read the file line by line
            for line in file:
                # Check if the search string exists in the current line
                if search_string in line:
                    return True
            file.close()
    except:
        with open(file_path, 'w') as file:
            file.close()
    return False

if __name__ == "__main__":
    main()