# monthly-listentothis-playlist
This program is running on an AWS lambda instance that runs the first of every month. 

# How it works
1. Refresh spotify API credentials
2. Create a new historical playlist and copy the latest top 50
3. Clear the latest top 50 playlist
4. Request the top 100 posts from r/listentothis and add them to Latest top 50

# Customizing
In order to customize this for other subreddits, here are the steps.

1. Create a Reddit app to get appropriate credentials. https://old.reddit.com/prefs/apps/
2. Create a spotify account you intend to use for the playlists.
3. Register an account through Spotify dev portal. https://developer.spotify.com/dashboard/login
4. Follow steps here to get refresh token for your specific account. https://documenter.getpostman.com/view/583/spotify-playlist-generator/2MtDWP?version=latest#02578443-6f63-97d4-31ec-7ce5beaca622
5. Change the subreddit that the program targets in line 83
6. Create an AWS Lambda instance using python 3.6
7. Follow instructions to upload the modified lambda function and depenceies here. https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html
8. Set cloudwatch event trigger with cron(0 1 1 * ? *) as the rule to run monthly
9. Add in your credentials as environment variables
