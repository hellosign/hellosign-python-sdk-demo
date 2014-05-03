hellosign-demo-app
==================

A demo app wrriten in Python for hellosign_python_sdk

### How to use

#### 1. Clone the source and install django

````bash
git clone git@github.com:HelloFax/hellosign-python-sdk-demo.git
cd hellosign-python-sdk-demo
pip install django
````

#### 2. Edit settings

Copy `settings.py.sample` to `settings.py` in `hellosign/`. Then update the file with your own `API_KEY` and `CLIENT_ID` and `SECRET`. (You can get your `API_KEY`, `CLIENT_ID`, `SECRET` here: https://www.hellosign.com/home/myAccount#integrations).

If you're deploying the app on Heroku, you may want to keep the sample content and use Heroku environment variables instead.


#### 3. Start the server

````
python manage.py runserver 80
````

Or just push the code to Heroku and you're all set!


Notice that in order for the app to run correctly, you need to register your HelloSign app with a valid callback url. If you want to deploy the app on localhost, you may want to use ngrok (https://ngrok.com) because `localhost` or `127.0.0.1` is not recognized as valid callback urls by HelloSign. Here's how:

1. Download ngrok (https://ngrok.com/download) and extract the zip file you've just downloaded

2. Open Terminal, navigate to the folder you've just extracted ngrok to, then run `./ngrok 80`. This will tell ngrok that you want to expose port 80 to the Internet.
When ngrok starts, it registers a random url (such as http://6eb6eb98.ngrok.com) and then forwards all traffic that reaches this url (port 80 for http or 443 for https) to your local server. What you need to do is to update your HelloSign settings for your app with this random url, so that the callbacks could be routed to your localhost.

3. Now change your local host configuration such that the demo app can be access via a custom domain name. Open /etc/hosts and add `127.0.0.1 my.api-demo.hellosign.com`. Visit http://my.api-demo.hellosign.com in your browser to make sure the demo app is now accessible. Then update the domain name on your HelloSign app to be my.api-demo.hellosign.com. This step is important to make the embedded signing/requesting demos work.  

4. Also change the HelloSign app OAuth callback url to be http://my.api-demo.hellosign.com/oauth_callback

