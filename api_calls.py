# api_calls.py
import requests
from requests.auth import HTTPBasicAuth
from config import FORUM_API_URL, FORUM_API_KEY, XAI_API_URL, XAI_API_KEY, USER_MENTION_ID
import logging
import json
import time

def get_xai_auth_header():
    return {"Authorization": f"Bearer {XAI_API_KEY}"}

def get_latest_notifications():
    logging.info("Fetching latest notifications")
    response = requests.get(
        f"{FORUM_API_URL}/core/members/{USER_MENTION_ID}/notifications",
        auth=HTTPBasicAuth(FORUM_API_KEY, ''),
        headers={"User-Agent": "MyUserAgent/1.0"}
    )
    response.raise_for_status()
    return response.json()

def post_forum_reply(topic_id, reply_text):
    logging.info(f"Posting reply to topic ID: {topic_id}")
    url = f"{FORUM_API_URL}/forums/posts"
    headers = {
        "User-Agent": "MyUserAgent/1.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = {
        "topic": int(topic_id),
        "author": int(USER_MENTION_ID),
        "post": reply_text
    }

    logging.debug(f"POST URL: {url}")
    logging.debug(f"Headers: {headers}")
    logging.debug(f"Payload: {payload}")

    response = requests.post(
        url,
        auth=HTTPBasicAuth(FORUM_API_KEY, ''),
        headers=headers,
        data=payload
    )
    logging.debug(f"Response status code: {response.status_code}")
    logging.debug(f"Response content: {response.content}")
    response.raise_for_status()
    return response.json()

def send_with_retry(url, headers, payload, max_retries=3, delay=2):
    retries = 0
    while retries < max_retries:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 429:
            retries += 1
            logging.warning(f"Rate limit exceeded. Retrying in {delay} seconds...")
            time.sleep(delay)
        else:
            response.raise_for_status()
            return response
    response.raise_for_status()

def send_to_xai(query):
    logging.info("Sending query to xAI")
    headers = {
        "Content-Type": "application/json",
        **get_xai_auth_header()
    }
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "model": "grok-2-latest",
        "stream": False,
        "temperature": 0
    }
    response = send_with_retry(XAI_API_URL, headers, payload)
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "Brak odpowiedzi od xAI.")

def check_if_image_request(query):
    logging.info("Checking if the query is about image analysis")
    headers = {
        "Content-Type": "application/json",
        **get_xai_auth_header()
    }
    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy. Please determine if the following query is asking for image analysis: " + query
            }
        ],
        "model": "grok-2-latest",
        "stream": False,
        "temperature": 0
    }
    response = send_with_retry(XAI_API_URL, headers, payload)
    result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response")
    return "yes" in result.lower()

def determine_query_type(query):
    logging.info("Determining if the query is about image analysis")
    headers = {
        "Content-Type": "application/json",
        **get_xai_auth_header()
    }
    payload = {
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "model": "grok-2-latest",
        "stream": False,
        "temperature": 0,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "image_request_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "is_image_request": {
                            "type": "boolean",
                            "description": "True if the query is about image analysis, false otherwise"
                        }
                    },
                    "required": ["is_image_request"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
    }
    response = send_with_retry(XAI_API_URL, headers, payload)
    result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
    result_json = json.loads(result)
    return result_json.get("is_image_request", False)