# slack_bot/slack_bot.py
import sys
import os
from dotenv import load_dotenv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, request, jsonify
from slack_sdk.web import WebClient
from slack_sdk.signature import SignatureVerifier
from ai_reasoning_engine.ai_engine import ai_reasoning_engine

load_dotenv("creds.env")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

app = Flask(__name__)
client = WebClient(token=SLACK_BOT_TOKEN)
verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    # Step 1: Verify Slack Signature
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return "Invalid request", 403

    data = request.get_json()

    # Step 2: Respond to Slack's URL Verification challenge
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    # Step 3: Process Event (e.g., app_mention)
    if "event" in data:
        event = data["event"]
        if event.get("type") == "app_mention":
            print(event)
            user_text = event.get("text", "").split(">", 1)[-1].strip()
            channel_id = event.get("channel")

            # Respond to user with a processing message
            # client.chat_postMessage(channel=channel_id, text=f"🔄 Processing: `{user_text}`")

            # Call AI engine and respond
            response = ai_reasoning_engine(user_text)
            client.chat_postMessage(channel=channel_id, text=response)

    return "", 200

if __name__ == "__main__":
    app.run(port=3000)
