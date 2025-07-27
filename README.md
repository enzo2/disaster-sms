# disaster-SMS

This app delivers relevant information via SMS in an emergency scenario, particularly during power and/or internet outages. Why might this be useful? Typically, we are instructed to use radio (AM/FM and NOAA stations) as a source of information during a serious disaster. However, in many scenarios, cell phone towers may continue to work, albeit with spotty connectivity or network overload. In this case, you may text a friend for information. This app replaces the friend with a search-enabled LLM, immediately giving you a full picture of the situation, or answering your specific inquiry, condensed into an SMS-sized response.

The app runs as a Docker stack intended to be kept alive on a Cloud VM at any reputable cloud provider which would, hopefully, be resilient in a disaster. Twilio is used for SMS.

## Requirements

- Docker environment running in a reputable/resilient data center
- Twilio account with a phone number and SMS campaign
- OpenAI or OpenAI-compatible LLM API with web search capability

## Setup

- **Deployment:** Docker Compose, with a `.devcontainer` setup for development.
- **Configuration:** `.env` file used for configuration.
- **Dependencies:** `uv` for Python package management.
- Scripts can be run standalone for testing purposes (eg. `uv run data_collection.py`)
- Optionally, configure your MQTT broker to receive healthchecks

## How It Works

- The Flask app exposes `/sms_api`, protected by an authorization token.
- API health is monitored via healthcheck
- User sends an SMS optionally containing any context or requests.
- Twilio forwards the SMS to the app API endpoint.
- Incoming requests are authenticated and parsed for sender, subject, and message body.
- The backend collects data from:
  - OpenAI API with web search
  - National Weather Service APIs (alerts for specific locations)
- Data is stored in Redis with a 1-week expiration, in case APIs go down.
- LLM is used to condense the information, focusing on the user's request. The summary is tailored to the user's request and current emergency context.
- The summary is sent via SMS.
- Errors are sent to the admin via email.
