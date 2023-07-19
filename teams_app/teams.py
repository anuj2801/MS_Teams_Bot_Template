import time
import os
import requests
import datetime
import sys
import traceback
import json
from colorama import Fore, Style
from teams_app.config import Configuration
from http import HTTPStatus

from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    TurnContext,
    UserState,
)
from botbuilder.schema import Activity, ActivityTypes

from teams_app.auth_bot import AuthBot

# from dialogs import MainDialog

config = Configuration()

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
SETTINGS = BotFrameworkAdapterSettings(config.app_id, config.app_secret)
ADAPTER = BotFrameworkAdapter(SETTINGS)

MEMORY = MemoryStorage()
USER_STATE = UserState(MEMORY)
CONVERSATION_STATE = ConversationState(MEMORY)

    # Create dialog
    # DIALOG = MainDialog(config.CONNECTION_NAME)

    # Create Bot
BOT = AuthBot(CONVERSATION_STATE, USER_STATE) 


class TeamsApp():
    def __init__(self, app_id, aap_secret, tenant_id, verbose=False) -> None:
        """
        app_id: The app id of the bot
        app_secret: The app secret of the bot
        tenant_id: The tenant id of the bot
        verbose: If true, prints out the logs
        """
        # parameters can not be None
        if app_id is None or aap_secret is None or tenant_id is None:
            raise ValueError("Parameters can not be None")

        self.app_id = app_id
        self.app_secret = aap_secret
        self.tenant_id = tenant_id
        self.verbose = verbose

        self.log("Initializing TeamsApp", Fore.GREEN)

        self.bot_authentication_url = "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token"
        self.conversation_url_subpart = "v3/conversations/%s/activities"
        self.conversation_service_url_subpart = "v3/conversations/%s/activities/%s"

        self.header, self.timestamp, self.expires_in = self.get_token()
        
        
    # Catch-all for errors.
    async def on_error(self, context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
       print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
       traceback.print_exc()

    # Send a message to the user
       await context.send_activity("The bot encountered an error or bug.")
       await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )

    # Send a trace activity if we're talking to the Bot Framework Emulator
       if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
           trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
           )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
           await context.send_activity(trace_activity)


    ADAPTER.on_turn_error = on_error

    # Create MemoryStorage and state
    MEMORY = MemoryStorage()
    USER_STATE = UserState(MEMORY)
    CONVERSATION_STATE = ConversationState(MEMORY)

    # Create dialog
    # DIALOG = MainDialog(config.CONNECTION_NAME)

    # Create Bot
    BOT = AuthBot(CONVERSATION_STATE, USER_STATE) 
        
    def validate_request(self, request):
        print("VR")
        if "application/json" in request.headers["Content-Type"]:
           body =  request.data
        else:
           return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

        activity = Activity().deserialize(body)
        auth_header = request.headers["Authorization"] if "Authorization" in request.headers else ""

        response =  ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
              return True
        else:
              return False   

    def check_body(self, request_body):
        """
        Checks if the body is None
        """
        # body can not be None
        if request_body is None:
            raise ValueError(
                "request_body can not be None, please provide request_body.")

    def get_user_text(self, request_body):
        """
        Returns the text typed by the user in the chat
        """
        self.check_body(request_body)
        return request_body.get("text")

    def get_user_id(self, request_body):
        """
        Returns the user id of the user who typed the message
        """
        self.check_body(request_body)
        return request_body.get("from").get("aadObjectId")

    def get_user_selection(self, request_body):
        """
        Returns the user selection from the adaptive card
        basically the value of the button pressed by the user
        """
        self.check_body(request_body)
        value = request_body.get("value", {})

        if len(value) == 0:
            value = None

        return value

    def get_tenant_id(self, request_body):
        """
            Returns the tenant id of user
        """
        self.check_body(request_body)
        return request_body.get("conversation").get("tenantId", None)

    def get_teams_bot_id(self, request_body):
        """
            Returns teams bot id
        """
        self.check_body(request_body)
        return request_body.get("recipient").get("id", None)

    def get_conversation_id(self, request_body):
        """
            Returns the conversation id of user
        """
        self.check_body(request_body)
        return request_body.get("conversation").get("id", None)

    def get_service_url(self, request_body):
        """
            Returns the service url where the message is to be sent
        """
        self.check_body(request_body)
        return request_body.get("serviceUrl")

    def download(self, url, dest_folder, file_name):
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)  # create folder if it does not exist
    
        filename = file_name  # be careful with file names
        file_path = os.path.join(dest_folder, filename)
    
        r = requests.get(url, stream=True)
        if r.ok:
            print("saving to", os.path.abspath(file_path))
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 8):
                    if chunk:
                        f.write(chunk)
                        f.flush()
                        os.fsync(f.fileno())
            return file_path            
        else:  # HTTP status code 4XX/5XX
            print("Download failed: status code {}\n{}".format(r.status_code, r.text))

    def get_files_url(self, request_body):
        """
            Returns the list of paths of the uploaded files where they are downloaded
        """
        self.check_body(request_body)
        local_path=[]
        for i in range(0, len(request_body.get("attachments"))-1):
         download_url=request_body.get("attachments")[i].get("content").get("downloadUrl")
         file_name=request_body.get("attachments")[i].get("name")
         local_path.append(self.download(download_url, "downloaded", file_name))
        return local_path

    def log(self, text, color=Fore.BLACK):
        if self.verbose:
            print(color + text + Style.RESET_ALL)

    def get_token(self):
        try:
            st = time.time()
            url = self.bot_authentication_url
            data = {
                "grant_type": "client_credentials",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "scope": "https://api.botframework.com/.default"
            }
            self.log("Requesting token from %s" % url)
            response = requests.post(url, data)
            if response.status_code != 200:
                raise ValueError("Failed to get token, status code: %s, response: %s" % (
                    response.status_code, response.text))

            timestamp = time.time()
            response_data = response.json()
            headers = {
                "Authorization": "%s %s" % (response_data["token_type"], response_data["access_token"])
            }
            self.log("Token generation took %s seconds" % (timestamp - st))
            # print(response_data["expires_in"])
            return headers, timestamp, response_data.get("expires_in")
        except Exception as e:
            self.log("Failed to get token, error: %s" % e, Fore.RED)
            raise e

    def validate_token_expiry(self):
        """
        Checks if the token has expired
        """
        buffer = 60
        if time.time() - self.timestamp > self.expires_in - buffer:
            self.log("Token expired, generating new token")
            self.header, self.timestamp, self.expires_in = self.get_token()

    def get_response_url(self, request_body):
        """
        returns the url to which the response has to be sent
        """
        # service url, conversation id and request_body can not be None
        if self.get_service_url(request_body) is None or self.get_conversation_id(request_body) is None or request_body is None:
            raise ValueError(
                "service url, conversation id and request_body can not be None")

        if request_body.get("id") is None:
            response_url = self.get_service_url(request_body) + \
                self.conversation_url_subpart % self.get_conversation_id(request_body)
        else:
            response_url = self.get_service_url(request_body) + \
                self.conversation_service_url_subpart % (
                    self.get_conversation_id(request_body), request_body.get("id"))

        return response_url

    def send_simple_msg(self, request_body, text):
        """
        Sends a simple text message to the user
        """
        
        self.validate_token_expiry()
        
        self.send_typing_activity(request_body)
        
        response_url = self.get_response_url(request_body)
        jsn = {
            "type": "message",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%zZ"),
            "from": {
                "id": self.get_teams_bot_id(request_body)
            },
            "conversation": {
                "id": self.get_conversation_id(request_body)
            },
            "text": text,
        }

        self.log("Sending message to %s" % response_url)
        res = requests.post(
            response_url,
            json=jsn,
            headers=self.header
        )

        return res.status_code
    
    def send_typing_activity(self, request_body):
        '''
        Sends typing activity
        '''
        st = time.time()
        response_url = self.get_response_url(request_body)
        jsn = {
            "type": "typing",
            "from": request_body["recipient"],
            "recipient": request_body["from"],
        }
        res = requests.post( 
            response_url,
            json=jsn,
            headers=self.header
            )
        if res.status_code not in [200, 201, 202, 204]:
           self.log(f"Send Typing Activity Failed with status code {res.status_code}")
        else:
            self.log(f"Send Typing Activity Took {time.perf_counter() - st}")
    
    def get_user_details_based_on_conversation_id(self, request_body, aad_object_id):
        """
        conversation_id: user conversation_id
        headers: request bot headers
        """
        service_url=self.get_service_url(request_body)
        conversation_id=self.get_conversation_id(request_body)
        
        url = f"{service_url}v3/conversations/{conversation_id}/pagedmembers"
        
        res = requests.get(
        url,
        headers=self.header
        )
        
        user_details = {"email": "",
        "name": ""}
        if res.status_code == 200:
           for item in res.json()["members"]:
              if item["aadObjectId"] == aad_object_id:
                 user_details["email"] = item.get("email", item.get("userPrincipalName"))
                 user_details["name"] = item.get("name")
        
        self.log(f"Fetched below details for {conversation_id}")
        print(user_details)
        
        return user_details
    
    @staticmethod
    def adaptive_card_image(img_url):
        """
            create json for adaptive card's body
        """

        res = {"type": "Image",
               "url": img_url,
               "altText": "Image"}

        return res

    @staticmethod
    def adaptive_card_task_module_button(title, link_to_open):
        """
            create json for adding buttons in adaptive card for opening task module
        """
        res = {"type": "Action.Submit",
               "title": title,
               "data": {
                   "msteams": {
                       "type": "task/fetch"
                   },
                   "redirect_url": link_to_open,
               }
               }

        return res

    @staticmethod
    def adaptive_card_button(title, button_value):
        """
            create json for adding buttons in adaptive card
        """
        res = {
            'type': 'Action.Submit',
            'data': button_value,
            'title': title
        }
        return res

    def adaptive_card_text(self, text):
        """
            create json for adding text in adaptive card
        """
        res = {
            "type": "TextBlock",
            "text": text,
            "wrap": True
        }
        return res

    def send_adaptive_card(self, card_details, request_body):
        """
        Sends an adaptive card to the user
        based on values present in card details

        if card has image, then image_url should be present
        if card has buttons, then buttons should have a url to hit

        card_details = [{"type": "image", "url": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"},
                        {"type": "button", "button_title": "button1", "button_value": "button1_value"},
                        {"type": "task-module-button", "button_title": "Title", "link_to_open": "https://www.google.com"},
                        {"type": "text", "text": "text to be displayed"}
                        ]

        """
        self.send_typing_activity(request_body)
        
        response_url = self.get_response_url(request_body)
        adaptive_card_body = []
        adaptive_card_actions = []
        for card_element in card_details:
            if card_element["type"] == "text":
                adaptive_card_body.append(
                    self.adaptive_card_text(text=card_element["text"]))
            elif card_element["type"] == "image":
                adaptive_card_body.append(
                    self.adaptive_card_image(img_url=card_element["url"]))
            elif card_element["type"] == "task-module-button":
                adaptive_card_actions.append(self.adaptive_card_task_module_button(title=card_element["button_title"],
                                                                                   link_to_open=card_element["link_to_open"]))
            elif card_element["type"] == "button":
                adaptive_card_actions.append(self.adaptive_card_button(title=card_element["button_title"],
                                                                       button_value=card_element["button_value"]))
        
        jsn = {
            "type": "message",
            "from": request_body.get("recipient"),
            "conversation": request_body.get("conversation"),
            "recipient": {"aadObjectId": request_body.get("from").get("aadObjectId")},
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "version": "1.2",
                        "body": adaptive_card_body,
                        "actions": adaptive_card_actions,
                        "msteams": {
                            "width": "Full"
                        }
                    }
                }
            ]
        }

        if request_body.get("id") is not None:
            jsn["replyToId"] = request_body.get("id")
        self.log("Sending Adaptive Card to %s" % response_url)
        res = requests.post(
            response_url,
            json=jsn,
            headers=self.header
        )

        return res.status_code