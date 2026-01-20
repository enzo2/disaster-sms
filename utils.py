import os
import errno
import email
from email import policy
import requests
import json
import redis
import logging
import paho.mqtt.publish as publish
from dotenv import load_dotenv
load_dotenv()

log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_USER = os.getenv('MQTT_USER')
MQTT_PWD = os.getenv('MQTT_PWD')

def publish_mqtt(topic, message):
    try:
        publish.single(topic, message, retain=True, hostname=MQTT_BROKER, auth={'username': MQTT_USER, 'password': MQTT_PWD})
    except OSError as e:
        if e.errno == errno.EHOSTUNREACH:
            logger.warning(f"MQTT Broker unreachable: {e}")
        else:
            logger.error(f"Failed to publish message to MQTT: {e}")
    except Exception as e:
        logger.error(f"Failed to publish message to MQTT: {e}")

# For use with scrapy
class RedisStoragePipeline:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)

    def process_item(self, item, spider):
        try:
            key = f'{spider.name}'
            # Set the data with a 1-week expiration
            self.redis_client.setex(key, 604800, json.dumps(item))  # 604800 seconds = 1 week
            logger.info(f"Saved {spider.name} data to Redis")
            return item
        except Exception as e:
            logger.error(f"Error saving {spider.name} data to Redis: {str(e)}")
            raise DropItem(f"Failed to store item in Redis: {item}")
