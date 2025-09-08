import json
import sys
sys.path.insert(0, '../')

from philiarabbit.producer import PhiliaRabbitProducer




def run_publisher():
    producer = PhiliaRabbitProducer(
        rabbit_url="amqp://guest:guest@localhost:5672",
        routing_key="event_attributes",
        exchange_name="",
    )
    producer.publish(data=json.dumps({"data": "test 11"}).encode("utf-8"), disconnect=True)
    assert producer.connection.is_closed


if __name__ == '__main__':
    run_publisher()