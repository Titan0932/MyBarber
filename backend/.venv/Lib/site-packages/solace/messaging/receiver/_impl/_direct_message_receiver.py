# pubsubplus-python-client
#
# Copyright 2021-2023 Solace Corporation. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module contains the implementation cass and methods for the DirectMessageReceiver"""
# pylint: disable=too-many-ancestors, too-many-instance-attributes, missing-class-docstring, missing-function-docstring
# pylint: disable=no-else-break,no-else-return,inconsistent-return-statements,protected-access

import concurrent
import logging
import queue
import weakref
from typing import Union

from solace.messaging.builder._impl._message_receiver_builder import DirectMessageReceiverBackPressure
from solace.messaging.config._solace_message_constants import DISPATCH_FAILED, RECEIVE_MESSAGE_FROM_BUFFER
from solace.messaging.errors.pubsubplus_client_error import PubSubPlusClientError
from solace.messaging.receiver._impl._message_receiver import _MessageReceiverState, \
    _DirectRequestReceiver
from solace.messaging.receiver._impl._receiver_utilities import validate_subscription_type
from solace.messaging.receiver.direct_message_receiver import DirectMessageReceiver
from solace.messaging.receiver.inbound_message import InboundMessage
from solace.messaging.receiver.message_receiver import MessageHandler
from solace.messaging.resources.topic_subscription import TopicSubscription
from solace.messaging.utils._solace_utilities import is_not_negative, convert_ms_to_seconds, is_type_matches, \
    _PubSubPlusQueue, QueueShutdown, _SolaceThread, Holder
from solace.messaging.utils.manageable import Metric

logger = logging.getLogger('solace.messaging.receiver')


class _DirectMessageReceiverThread(_SolaceThread):  # pylint: disable=missing-class-docstring
    # Thread used to dispatch received messages on a receiver.

    def __init__(self, owner_info, owner_logger: 'logging.Logger', direct_message_receiver, messaging_service, *args,
                 **kwargs):
        super().__init__(owner_info, owner_logger, *args, **kwargs)
        self._message_receiver = direct_message_receiver
        self._message_receiver_queue = self._message_receiver.receiver_queue
        self._message_handler = None
        self._stop_event = self._message_receiver.stop_event  # we receive this from direct message impl class
        self._messaging_service = messaging_service
        # This boolean is used to notify the direct receiver async receive thread that the receiver has been
        # terminated or is in the process of being terminated. The receiver will update this boolean as a part
        # of handling termination. Having a simple boolean be updated by the receiver is more performant than
        # checking the state of the receiver in the `run()` method, regardless of what means is used since the
        # receiver has multiple states that could towards termination, which means multiple reads vs. a single
        # read. This, however is only a temporary change until the queue improvements can be made. Do not
        # change this unless as a part of the queue improvements.
        self.asked_to_terminate = False

    def _on_join(self):
        self._stop_event.set()
        self._message_receiver_queue.shutdown()

    @property
    def message_handler(self):
        return self._message_handler

    @message_handler.setter
    def message_handler(self, message_handler):
        self._message_handler = message_handler

    def run(self):
        # Start running thread
        if logger.isEnabledFor(logging.DEBUG):  # pragma: no cover # Ignored due to log level
            self.adapter.debug('THREAD: [%s] started', type(self).__name__)
        while not self._stop_event.is_set():
            inbound_message = None
            try:
                inbound_message = self._message_receiver_queue.get()
            except QueueShutdown:
                #the queue has shutdown no need to pull from it anymore
                break

            if inbound_message:
                if inbound_message.get_message_discard_notification().has_internal_discard_indication():
                    # Since we are always dealing with one message at a time,
                    # and the discard indication is a boolean, we only need to
                    # increment by one each time, so we can hardcode it here
                    self._message_receiver._int_metrics. \
                        _increment_internal_stat(Metric.INTERNAL_DISCARD_NOTIFICATIONS, 1)
                try:
                    self._message_handler.on_message(inbound_message)
                except Exception as exception:  # pylint: disable=broad-except
                    self.adapter.warning("%s %s", DISPATCH_FAILED, str(exception))
        if logger.isEnabledFor(logging.DEBUG):  # pragma: no cover # Ignored due to log level
            self.adapter.debug('THREAD: [%s] exited', type(self).__name__)


class _DirectMessageReceiver(_DirectRequestReceiver, DirectMessageReceiver):
    # class for direct message receiver, it is the base class used to receive direct messages

    def __init__(self, builder: 'DirectMessageReceiverBuilder'):  # pylint: disable=duplicate-code
        super().__init__(builder)
        if logger.isEnabledFor(logging.DEBUG):  # pragma: no cover # Ignored due to log level
            self.adapter.debug('[%s] initialized', type(self).__name__)
        self._running = False
        self._set_next_discard_indication = False

        self._message_handler = None
        self._int_metrics = self._messaging_service.metrics()
        key = "subscriptions"
        if key in builder.topic_dict:
            subscription = builder.topic_dict[key]
            if isinstance(subscription, str):
                self._topic_dict[subscription] = False  # not applied
            else:
                for topic in subscription:
                    self._topic_dict[topic] = False  # not applied
        key = "group_name"
        if key in builder.topic_dict:
            self._group_name = builder.topic_dict[key]
        self._message_receiver_state = _MessageReceiverState.NOT_STARTED
        self.__init_back_pressure(builder)
        self._message_receiver_thread_holder = Holder()
        self._listener_service_finalizer = weakref.finalize(self,
                                                            direct_receiver_thread_cleanup,
                                                            self._message_receiver_thread_holder)

    def _handle_events_on_terminate(self):
        super()._handle_events_on_terminate()
        if self._message_receiver_thread is not None:
            self._message_receiver_thread.asked_to_terminate = True

    def __init_back_pressure(self, builder: 'DirectMessageReceiverBuilder'):
        # This method presumes that the buffer type and capacity have previously been validated.
        if builder.receiver_back_pressure_type != DirectMessageReceiverBackPressure.Elastic:
            if builder.receiver_back_pressure_type == DirectMessageReceiverBackPressure.DropOldest:
                self._force = True
                self._block = True
                self._message_receiver_queue = _PubSubPlusQueue(maxsize=builder._buffer_capacity)

            elif builder.receiver_back_pressure_type == DirectMessageReceiverBackPressure.DropLatest:
                self._force = False
                self._block = False
                self._message_receiver_queue = _PubSubPlusQueue(maxsize=builder._buffer_capacity)

            def on_buffer_overflow(discarded):
                if discarded and isinstance(discarded, InboundMessage):
                    peeked_message = self._message_receiver_queue.unsafe_peek()
                    if peeked_message:
                        peeked_message.get_message_discard_notification().set_internal_discard_indication()
                    # We do this for every message that is received if the queue is full, so we only need to
                    # increment the metric by one each time. Since we increment by the same amount every time,
                    # we can hardcode it
                    self._int_metrics._increment_internal_stat(Metric.RECEIVED_MESSAGES_BACKPRESSURE_DISCARDED, 1)

            # pylint: disable=unused-argument
            def on_buffer_overflow_discard_latest(discarded):
                self._set_next_discard_indication = True
                self._int_metrics._increment_internal_stat(Metric.RECEIVED_MESSAGES_BACKPRESSURE_DISCARDED, 1)

            def on_item_put(item):
                if self._set_next_discard_indication:
                    item.get_message_discard_notification().set_internal_discard_indication()
                    self._set_next_discard_indication = False

            if builder.receiver_back_pressure_type == DirectMessageReceiverBackPressure.DropOldest:
                self._message_receiver_queue.register_on_event(_PubSubPlusQueue.ON_BUFFER_OVERFLOW_EVENT,
                                                               on_buffer_overflow)
            elif builder.receiver_back_pressure_type == DirectMessageReceiverBackPressure.DropLatest:
                self._message_receiver_queue.register_on_event(_PubSubPlusQueue.ON_PUT_ITEM_EVENT, on_item_put)
                self._message_receiver_queue.register_on_event(_PubSubPlusQueue.ON_BUFFER_OVERFLOW_EVENT,
                                                               on_buffer_overflow_discard_latest)

        else:
            # elastic case
            self._message_receiver_queue = _PubSubPlusQueue()

    def add_subscription(self, another_subscription: TopicSubscription):
        # Subscribe to a topic synchronously (blocking). """
        validate_subscription_type(subscription=another_subscription, logger=logger)
        self._can_add_subscription()
        self._do_subscribe(another_subscription.get_name())

    def add_subscription_async(self, topic_subscription: TopicSubscription) -> concurrent.futures.Future:
        # method to add the subscription asynchronously
        return self._executor.submit(self.add_subscription, topic_subscription)

    def receive_message(self, timeout: int = None) -> Union[InboundMessage, None]:
        # Get a message, blocking for the time configured in the receiver builder.
        # may return None when the flow goes api is called after TERMINATING state & internal buffer is empty
        # as well as when service goes down """
        self._can_receive_message()
        if timeout is not None:
            is_not_negative(input_value=timeout, logger=logger)

        if logger.isEnabledFor(logging.DEBUG):  # pragma: no cover # Ignored due to log level
            self.adapter.debug("%s", RECEIVE_MESSAGE_FROM_BUFFER)
        try:
            message = self._message_receiver_queue.get(block=True,
                                                       timeout=convert_ms_to_seconds(
                                                           timeout) if timeout is not None else None)
            # This first condition checks to make sure the message is not None
            if message and message.get_message_discard_notification().has_internal_discard_indication():
                # Since we are always dealing with one message at a time, and the discard indication is a boolean,
                # we only need to increment by one each time, so we can hardcode it here
                self._int_metrics._increment_internal_stat(Metric.INTERNAL_DISCARD_NOTIFICATIONS, 1)

            return message
        except queue.Empty:  # when timeout arg is given just return None on timeout
            return
        except QueueShutdown:
            # unblock wait on terminate
            return
        except (PubSubPlusClientError, KeyboardInterrupt) as exception:
            logger.warning(str(exception))
            raise exception

    def receive_async(self, message_handler: MessageHandler):
        # Specify the asynchronous message handler.
        is_type_matches(actual=message_handler, expected_type=MessageHandler, logger=logger)
        with self._receive_lock:
            self._can_receive_message()
            if self._message_receiver_thread is None:
                self._message_receiver_thread = _DirectMessageReceiverThread(self._id_info, logger, self,
                                                                             self._messaging_service)
                self._message_receiver_thread_holder.value = self._message_receiver_thread
                self._message_receiver_thread.message_handler = message_handler
                self._message_receiver_thread.daemon = True
                self._message_receiver_thread.start()
            else:  # just update the thread's message handler
                self._message_receiver_thread.message_handler = message_handler

    def remove_subscription(self, subscription: TopicSubscription):
        # Unsubscribe from a topic synchronously (blocking).
        validate_subscription_type(subscription=subscription, logger=logger)
        self._can_remove_subscription()
        self._do_unsubscribe(subscription.get_name())

    def remove_subscription_async(self, topic_subscription: TopicSubscription) -> concurrent.futures.Future:
        # method to remove the subscription asynchronously
        validate_subscription_type(topic_subscription)
        return self._executor.submit(self.remove_subscription, topic_subscription)

    def _halt_messaging(self):
        self._unsubscribe()


def direct_receiver_thread_cleanup(thread_holder):
    direct_receiver_thread = thread_holder.value
    if direct_receiver_thread is not None and direct_receiver_thread.is_alive():
        direct_receiver_thread.join()
