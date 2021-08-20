import json
import time

from workflows.services.common_service import CommonService


class SampleConsumer(CommonService):
    """An example service building on top of the workflow.services architecture,
    demonstrating how this architecture can be used.
    This service consumes messages off a queue."""

    # Human readable service name
    _service_name = "Message Consumer"

    # Logger name
    _logger_name = "workflows.service.sample_consumer"

    def initializing(self):
        """Subscribe to a channel."""
        self._transport.subscribe("transient.destination", self.consume_message)
        self.counter = 0
        self._register_idle(3, self.create_message)

    def create_message(self):
        """Create and send a unique message for this service."""
        self.counter += 1
        self.log.info("Sending message #%d", self.counter)
        self._transport.send(
            "transient.destination",
            "Message #%d\n++++++++Produced @%10.3f ms"
            % (self.counter, (time.time() % 1000) * 1000),
        )

    def consume_message(self, header, message):
        """Consume a message"""
        t = (time.time() % 1000) * 1000

        if header:
            header = json.dumps(header, indent=2) + "\n" + "----------------" + "\n"
        else:
            header = ""
        if isinstance(message, dict):
            message = json.dumps(message, indent=2) + "\n" + "----------------" + "\n"

        self.log.info(
            f"=== Consume ====\n{header}{message}\nReceived message @{t:10.3f} ms"
        )
        time.sleep(0.1)
