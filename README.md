# README #

This README would normally document whatever steps are necessary to get your application up and running.

### What is this repository for? ###

* Quick summary<br>
  GPT Teams Connnection Template<br>
  It is a pre defined code that can be used as it is to connect to GPT use case apis. It's a quick way to connect all GPT work to teams.
* Version - 1.0

### How do I get set up? ###

* Summary of set up<br>
  <ul>
  <li>STEP 1: Registration on Azure & creation of app id, app secret & tenant id.</li>
  <li>STEP 2: Update App's manifest on Azure Active Directory with "accessTokenAcceptedVersion": 2 and "signInAudience": "AzureADandPersonalMicrosoftAccount"</li>
  <li>STEP 3: Use these credentials to set up config.py file(inside teams_app folder).</li>
  <li>STEP 4: Use <b>python manage.py runserver</b> command in root folder and check your local host port.</li>
  <li>STEP 5: Install ngrok and set path of ngrok to system environment variables. Use Command <b>ngrok http (local host port)</b> to get public ip.</li>
  <li>STEP 6: Make new bot using bot framework and set channel to Microsoft teams.</li>
  <li>STEP 7: Add app id and set messaging endpoint of the bot to public ip/webhook.</li>
  <li>STEP 8: Use <b>python manage.py runserver</b> to run the app in terminal.</li>
  <li>STEP 9: Go to bot in Microsoft teams and type any text and see if you are getting hello text reply.</li>
  </ul>
* Configuration<br>
  It has to be done in config.py file using azure registration credentials.<br>
        self.app_id = ""<br>
        self.app_secret = ""<br>
        self.tenant_id = ""<br>

* Dependencies<br>
  <ul>
  <li>Python</li>
  <li>Django</li>
  <li>Django Rest Framework</li>
  </ul>
* Database configuration
* How to run tests
* Deployment instructions

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
