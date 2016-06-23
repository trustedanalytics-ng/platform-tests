#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import base64
import os
import re

from apiclient import discovery
import httplib2
import oauth2client
from retry import retry

from .tap_logger import get_logger
from configuration import config

SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = os.path.join("configuration", "secrets", "client_secret.json")
APPLICATION_NAME = 'praca-email'
TEST_EMAIL = config.CONFIG["test_user_email"]
INVITATION_EMAIL_SUBJECT = "Invitation to join Trusted Analytics platform"
INVITATION_LINK_PATTERN = r'"(https?://[^\s]+)"'

logger = get_logger(__name__)


def _get_credentials():
    credential_path = os.path.join("configuration", "secrets", "gmail-code.json")
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = oauth2client.client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = oauth2client.tools.run_flow(flow, store)
        logger.info('Storing credentials to ' + credential_path)
    return credentials


def _get_service():
    credentials = _get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    return service


def get_query(recipient, email_subject=None):
    query = "to:{}".format(recipient)
    if email_subject is not None:
        query += " subject:{}".format(email_subject)
    return query


def get_query_for_list(usernames):
    query = ""
    for username in usernames:
        query += "to:{} | ".format(username)
    return query


def _retrieve_message_ids_matching_query(service, user_id, query=''):
    response = service.users().messages().list(userId=user_id, q=query).execute()
    messages = []
    if 'messages' in response:
        messages.extend(response['messages'])
    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
        messages.extend(response['messages'])
    return [msg["id"] for msg in messages]


def _get_info_from_headers(headers):
    message_subject = recipient = sender = None
    for header in headers:
        if header["name"] == "Delivered-To":
            recipient = header["value"]
        if header["name"] == "Subject":
            message_subject = header["value"]
        if header["name"] == "From":
            sender = header["value"]
    return {"subject": message_subject, "recipient": recipient, "sender": sender}


def get_messages_from_query(query, expected_number=None, user_id=TEST_EMAIL):
    service = _get_service()
    message_ids = _retrieve_message_ids_matching_query(service, user_id, query)
    actual_number = len(message_ids)
    if expected_number is not None:
        assert actual_number == expected_number, "There are {} messages matching query: '{}'. Expected: {}".format(
            actual_number, query, expected_number)
    messages = []
    for message_id in message_ids:
        message = service.users().messages().get(userId=user_id, id=message_id, format='full').execute()
        timestamp = message['internalDate']
        headers = _get_info_from_headers(message['payload']['headers'])
        msg_str = base64.urlsafe_b64decode(message['payload']['body']['data'].encode('ASCII'))
        message_content = msg_str.decode("utf-8")
        messages.append({"subject": headers["subject"],
                         "content": message_content,
                         "timestamp": timestamp,
                         "recipient": headers["recipient"],
                         "sender": headers["sender"]})
    return messages


@retry(AssertionError, tries=30, delay=2)
def wait_for_messages_matching_query(query, messages_number=1):
    messages = get_messages_from_query(query, messages_number)
    return messages


def wait_for_messages_to(recipient, messages_number=1):
    query = get_query(recipient=recipient)
    return wait_for_messages_matching_query(query, messages_number=messages_number)


def is_there_any_messages_to(recipient, user_id=TEST_EMAIL):
    service = _get_service()
    query = get_query(recipient)
    message_ids = _retrieve_message_ids_matching_query(service, user_id, query)
    return len(message_ids) != 0


def extract_code_from_message(message):
    pattern = r"(?<=code=)([a-zA-Z0-9]|-)+"
    match = re.search(pattern, message)
    if match is None:
        raise AssertionError("Can't find code in given message: {}".format(message))
    return match.group()


def get_invitation_code_for_user(username):
    messages = wait_for_messages_to(recipient=username)
    return extract_code_from_message(messages[0]["content"])


def get_invitation_codes_for_list(usernames):
    query = get_query_for_list(usernames)
    messages = wait_for_messages_matching_query(query, messages_number=len(usernames))
    codes = {}
    for message in messages:
        codes[message["recipient"]] = extract_code_from_message(message["content"])
    return codes


def get_reset_password_links(username):
    query = get_query_for_list([username])
    #2 messages - reset email and create account
    messages = wait_for_messages_matching_query(query, messages_number=2)

    code = extract_code_from_message(messages[0]["content"])
    logger.debug("Extracted reset password code {}", code)

    return code


def get_link_from_message(email_content):
    match = re.search(INVITATION_LINK_PATTERN, email_content)
    if match is None:
        raise AssertionError("Invitation link was not found in email content: {}".format(email_content))
    return match.group()
