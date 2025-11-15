from flask import Flask
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
import os

# Put your real DSN here (or use env var for extra safety)
import sentry_sdk

sentry_sdk.init(
    dsn="https://7e57dd91c16a6461fb36e95a2f7500e1@o4510366813519872.ingest.us.sentry.io/4510370710224896",
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
)
app = Flask(__name__)

@app.route("/")
def home():
    return "Sentry is working! Go to /bug to trigger an error 🪲"

@app.route("/bug")
def trigger_bug():
    1 / 0  # deliberate division by zero
    return "no bug :("

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)