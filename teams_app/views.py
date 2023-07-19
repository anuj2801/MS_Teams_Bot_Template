from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from teams_app.teams import TeamsApp
from teams_app.config import Configuration
from teams_app.sessions import sessions
from botbuilder.core import TurnContext

import requests
import pandas as pd
import json
import os
import time


config = Configuration()
app_object = TeamsApp(config.app_id, config.app_secret,
                      config.tenant_id, verbose=True)


class webhook(APIView):

  def post(self, request):
        # if not app_object.validate_request(request): #authentication
        #   HttpResponse.
           
        body = request.data
        card_details=[
                        {"type": "text", "text": "Please Select analysis"},
                        {"type": "button", "button_title": "Data Quality", "button_value": {"name":"data_quality"}},
                        {"type": "button", "button_title": "Data Harmonization", "button_value": {"name":"data_harmonization"}}
                     ]

        greetings=["HI", "HELLO"]
        
        userId=body.get("from").get("id")
        text=body.get("text")
        attachments=body.get("attachments")
        button_value=body.get("value")
        
        session_object=sessions(userId)        
        
        if body.get("name")=="fileConsent/invoke":
            app_object.validate_token_expiry()
            app_object.send_typing_activity(body)
            action=body.get("value").get("action")
            if(action=="accept"):
              uploadUrl=body.get("value").get("uploadInfo").get("uploadUrl")
              contentUrl=body.get("value").get("uploadInfo").get("contentUrl")
              fileType=body.get("value").get("uploadInfo").get("fileType")
              fileName=body.get("value").get("uploadInfo").get("name")
              uniqueId=body.get("value").get("uploadInfo").get("uniqueId")
              
              #deleting file consent card
              activityId=body.get("replyToId")
              deleteUrl=app_object.get_service_url(body) + \
                app_object.conversation_url_subpart % app_object.get_conversation_id(body)+f"/{activityId}" 
              resp=requests.delete(url=deleteUrl, headers=app_object.header)
              
              app_object.send_simple_msg(body, "Please wait for a moment. File Uploading in progress.")
              #file upload session
              
              
              
              response_url=app_object.get_response_url(body)
              jsn={
                "type": "message",
                "from": body.get("recipient"),
                "conversation": body.get("conversation"),
                "recipient": {"aadObjectId": body.get("from").get("aadObjectId")},
                "attachments": [{
                "contentType": "application/vnd.microsoft.teams.card.file.info",
                "contentUrl": contentUrl,
                "name": fileName,
                "content": {
                "uniqueId": uniqueId,
                "fileType": fileType,
                }
                }]
                }
              if body.get("id") is not None:
                jsn["replyToId"] = body.get("id")
              res = requests.post(
                 response_url,
                 json=jsn,
                 headers=app_object.header
                 )
            else:
             app_object.send_simple_msg(body, "Please select Allow to get merged csv file on your OneDrive")              
        elif text:
            text=text.upper()
            if text in greetings:
             app_object.send_adaptive_card(card_details, body)
            else:
             app_object.send_simple_msg(body, "Please start your conversation with 'Hi' or 'Hello'")
        elif attachments:
            '''
            Returns message based on the number of files uploaded corresponding to the clicked button and downloads files to downloaded folder
            '''

            analysis=session_object.get_session(userId, "analysis")
            
            if not analysis:
               app_object.send_simple_msg(body, "Please select some analysis first")

            attachments_size=0
            for i in range(0,len(body.get("attachments"))-1):
                if attachments[i].get('content').get('fileType')=="csv":
                   attachments_size=attachments_size+1
              
         
            if analysis=="data_quality":
                if(attachments_size<3):
                  app_object.send_simple_msg(body, "Please Upload 3 csv files")
                elif(attachments_size==3):
                  local_paths=app_object.get_files_url(body)
                  
                  paths_dict={"analysis":analysis,"option":"", "files":local_paths}
                  session_object.set_session(userId, paths_dict)
                   
                  app_object.send_simple_msg(body, "THANKS FOR SELECTING DATA QUALITY")
                else:
                  app_object.send_simple_msg(body, "Please Upload only 3 csv files")   
            elif analysis=="data_harmonization":
                if(attachments_size<2):
                  app_object.send_simple_msg(body, "Please Upload 2 csv files")
                elif(attachments_size==2):
                  local_paths=app_object.get_files_url(body)
                  
                  paths_dict={"analysis":analysis,"option":"", "files":local_paths}
                  session_object.set_session(userId, paths_dict)
                  
                  
                  analysis_card_details=[
                        {"type": "text", "text": "Please select option for Data Harmonization"},
                        {"type": "button", "button_title": "ChatGPT", "button_value": {"name":"ChatGPT"}},
                        {"type": "button", "button_title": "GPT4", "button_value": {"name":"GPT4"}},
                        {"type": "button", "button_title": "Fuzzy Wuzzy", "button_value": {"name":"Fuzzy Wuzzy"}},
                        {"type": "button", "button_title": "Rapidfuzz", "button_value": {"name":"Rapidfuzz"}},
                        {"type": "button", "button_title": "Jaro Winkler", "button_value": {"name":"Jaro Winkler"}},
                        {"type": "button", "button_title": "JW Layered with ChatGPT", "button_value": {"name":"JW Layered with ChatGPT"}},
                        {"type": "button", "button_title": "JW Layered with GPT4", "button_value": {"name":"JW Layered with GPT4"}},
                        {"type": "button", "button_title": "FW Layered with GPT4", "button_value": {"name":"FW Layered with GPT4"}},
                        {"type": "button", "button_title": "Recursive Data Harmonization", "button_value": {"name":"Recursive Data Harmonization"}}
                     ]
        
                  app_object.send_adaptive_card(analysis_card_details, body)
                  
                else:
                  app_object.send_simple_msg(body, "Please Upload only 2 csv files")
            else:
                app_object.send_simple_msg(body, "Unrecognized action")        
        elif button_value:
            '''
            Returns some results/message based on the clicked button
            '''
            button_value=button_value.get("name")
            files_value=session_object.get_session(userId, "files")
            analysis=session_object.get_session(userId,"analysis")
            
            if files_value and ((analysis=="data_quality" and not button_value=="data_harmonization" and not button_value=="data_quality") or (analysis=="data_harmonization" and not button_value=="data_quality" and not button_value=="data_harmonization")):
               
                #data_harmonization API Call
                files_path=session_object.get_session(userId, "files")
                val={"analysis":analysis, "option":button_value,"files":files_path}
                session_object.set_session(userId, val)
                file1_path=files_path[0]
                file2_path=files_path[1]
                
                file1_name=file1_path[12:]
                file2_name=file2_path[12:]
                
                url = "http://127.0.0.1:7000/upload/"

                payload = {'option': button_value}
                files=[('file1',(file1_name,open(file1_path,'rb'),'text/csv')),
                ('file2',(file2_name,open(file2_path,'rb'),'text/csv'))]
                headers = {
                  'Authorization': 'Basic YWRtaW46ZHBAMTIzNDU2'
                }
                
                response=requests.request("POST", url, headers=headers, data=payload, files=files)
                
                data=json.loads(response.text)
                data=json.loads(data)
                df = pd.DataFrame(data)
                tstp = time.time()
                df.to_csv(f"./csvFiles/csvfile_{button_value}_{tstp}.csv")
                
                app_object.validate_token_expiry()
                app_object.send_typing_activity(body)
                response_url = app_object.get_response_url(body)
                jsn={
                "type": "message",
                "from": body.get("recipient"),
                "conversation": body.get("conversation"),
                "recipient": {"aadObjectId": body.get("from").get("aadObjectId")},
                "attachments": [{
                "contentType": "application/vnd.microsoft.teams.card.file.consent",
                "name": f"csvfile_{button_value}_{tstp}.csv",
                "content": {
                "description": f"Merged CSV file after data harmonization using {button_value}",
                "sizeInBytes": os.stat(f"./csvFiles/csvfile_{button_value}_{tstp}.csv").st_size,
                "acceptContext": {
                },
                "declineContext": {
                }
                }
                }]
                }
                if body.get("id") is not None:
                   jsn["replyToId"] = body.get("id")
                res = requests.post(
                 response_url,
                 json=jsn,
                 headers=app_object.header
                 )       
            else:  
                val={"analysis":button_value, "option":"", "files":[]}
                session_object.set_session(userId, val)
        
                if button_value=="data_quality":
                   app_object.send_simple_msg(body, "Please Upload 3 csv files")
                elif button_value=="data_harmonization":
                   app_object.send_simple_msg(body, "Please upload 2 csv files")
                else:
                   app_object.send_simple_msg(body, "Unrecognized action")      
        return JsonResponse(request.data)
