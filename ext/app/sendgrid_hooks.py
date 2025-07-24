from ecdsa import VerifyingKey, BadSignatureError
from ecdsa.util import sigdecode_der
import base64
import hashlib
from flask import request, current_app as app
from ext.scf import SENDGRID_PUBLIC_KEY
# -*- coding: utf-8 -*-

class EventWebhookHeader:
    """
    This class lists headers that get posted to the webhook. Read the docs for
    more details: https://sendgrid.com/docs/for-developers/tracking-events/event
    """
    SIGNATURE = 'X-Twilio-Email-Event-Webhook-Signature'
    TIMESTAMP = 'X-Twilio-Email-Event-Webhook-Timestamp'

    def __init__(self):
        pass


class EventWebhook:
    """
    This class allows you to use the Event Webhook feature. Read the docs for
    more details: https://sendgrid.com/docs/for-developers/tracking-events/event
    """

    def __init__(self, public_key=None):
        """
        Construct the Event Webhook verifier object
        :param public_key: verification key under Mail Settings
        :type public_key: string
        """
        self.public_key = self.convert_public_key_to_ecdsa(public_key) if public_key else public_key

    def convert_public_key_to_ecdsa(self, public_key):
        """
        Convert the public key string to a VerifyingKey object.

        :param public_key: verification key under Mail Settings
        :type public_key string
        :return: VerifyingKey object using the ECDSA algorithm
        :rtype VerifyingKey
        """
        pem_key = "-----BEGIN PUBLIC KEY-----\n" + public_key + "\n-----END PUBLIC KEY-----"
        return VerifyingKey.from_pem(pem_key)

    def verify_signature(self, payload, signature, timestamp, public_key=None):
        """
        Verify signed event webhook requests.

        :param payload: event payload in the request body
        :type payload: string
        :param signature: value obtained from the 'X-Twilio-Email-Event-Webhook-Signature' header
        :type signature: string
        :param timestamp: value obtained from the 'X-Twilio-Email-Event-Webhook-Timestamp' header
        :type timestamp: string
        :param public_key: elliptic curve public key
        :type public_key: VerifyingKey
        :return: true or false if signature is valid
        """
        timestamped_payload = (timestamp + payload).encode('utf-8')
        decoded_signature = base64.b64decode(signature)

        key = public_key or self.public_key
        try:
            key.verify(decoded_signature, timestamped_payload, hashfunc=hashlib.sha256, sigdecode=sigdecode_der)
            return True
        except BadSignatureError:
            return False


def verify_sendgrid_signature(resource, items):
    if resource == 'webhook':
        # Get headers
        signature = request.headers.get(EventWebhookHeader.SIGNATURE, None)
        timestamp = request.headers.get(EventWebhookHeader.TIMESTAMP, None)

        # Get raw payload
        payload = request.get_data(as_text=True)

        # Initialize EventWebhook
        event_webhook = EventWebhook()

        # Convert public key to ECDSA
        try:
            ec_public_key = event_webhook.convert_public_key_to_ecdsa(SENDGRID_PUBLIC_KEY)
        except Exception as e:
            app.logger.error(f"Failed to convert public key: {e}")
            raise ValueError("Invalid public key")

        # Verify signature
        is_verified = event_webhook.verify_signature(
            payload=payload,
            signature=signature,
            timestamp=timestamp,
            public_key=ec_public_key
        )

        if not is_verified:
            app.logger.error("SendGrid webhook signature verification failed")
            raise ValueError("Signature verification failed")

        # Log success (optional)
        app.logger.info("SendGrid webhook signature verified successfully")