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
- The default docker compose setup includes labels for Traefik, and docker networks for Traefik and a tunnel to your MQTT broker. You can remove these if you use a different setup.
- Optionally, configure your MQTT broker to receive healthchecks. To tunnel to your broker, establish a TCP tunnel container and add it to the `mqtt` docker network.

## How It Works

- The Flask app exposes `/sms_api`, accepting POST requests from Twilio. Incoming requests are validated.
- User sends an SMS, optionally containing a specific location or question. 
- Twilio forwards the SMS to the app API endpoint. 
- The backend collects data from:
  - OpenAI API with web search
  - National Weather Service APIs (alerts and forecast)
- Data is stored in Redis with a 1-day expiration, in case APIs go down.
- LLM is used to summarize the data to MMS-size. The summary is tailored to the user's request and current emergency context.
- The summary is sent via SMS using Twilio.
- There is no database. Any further request must be initiated by the user again.
- Errors are sent to the admin via email.
- App health is monitored via healthcheck and optionally MQTT.

## License

This project is licensed under the Sustainable Use License, allowing for personal and non-commerical use. See the [LICENSE](LICENSE.md) file for details.