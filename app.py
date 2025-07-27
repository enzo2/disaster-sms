from dotenv import load_dotenv
load_dotenv()
import os
import logging
from flask import Flask, request, jsonify
from data_collection import collect_data
from data_summarization import summarize_data
from message_sender import send_sms, send_email
from twilio.request_validator import RequestValidator
from utils import publish_mqtt

TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
MQTT_TOPIC = os.getenv('MQTT_TOPIC') if os.getenv('MQTT_TOPIC') else None
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL') if os.getenv('ADMIN_EMAIL') else None

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

app.wsgi_app = ReverseProxied(app.wsgi_app)

@app.route('/health', methods=['GET'])
def health_check():
    try:
        logger.info("Health check received")
        if MQTT_TOPIC:
            publish_mqtt(MQTT_TOPIC, "ok")
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/sms_api', methods=['POST'])
def sms_api():
    logger.info("API request received.")
    # Validate Twilio request
    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    url = request.url
    post_vars = request.form.to_dict()
    twilio_signature = request.headers.get('X-Twilio-Signature', '')

    if not validator.validate(url, post_vars, twilio_signature):
        request_data = request.get_data(as_text=True)
        headers = dict(request.headers)
        logger.warning(f"Twilio request validation failed. Headers: {headers}, Body: {request_data}")
        send_email(f"Twilio request validation failed: \n\n Headers: {headers} \n\n Body: {request_data}", "Twilio Validation Error", [ADMIN_EMAIL])
        return jsonify({"error": "Twilio request validation failed"}), 403

    from_number = request.form.get('From')
    body = request.form.get('Body', '')

    logger.info(f"Received SMS from: {from_number}")
    logger.info(f"Body: {body}")

    try:
        if body.lower().strip() == 'test':
            logger.info("Test message received.")
            send_sms('Test successful!', from_number)
        else:
            logger.info("Starting response.")
            collect_data(body)
            summary = summarize_data(body)
            send_sms(summary, from_number)
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        error_message = f"Error processing your request: {e}"
        send_email(error_message, "Disaster SMS Error", [ADMIN_EMAIL])
        send_sms("Sorry, an error occurred while processing your request.", from_number)

    return jsonify({"status": "success", "message": "SMS received and processed"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
