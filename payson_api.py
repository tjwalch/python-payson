# -*- coding: utf-8 -*-
"""Python API for Payson paymnents provider

Copyright (c) 2012 Tomas Walch
MIT-License, see LICENSE for details
"""
import datetime
import decimal
import logging
import json
import urllib
import urllib2
import urlparse


PAYSON_API_ENDPOINT = "https://api.payson.se"
PAYSON_TEST_API_ENDPOINT = "https://test-api.payson.se"
PAYSON_API_VERSION = "1.0"
PAYSON_API_PAY_ACTION = "Pay/"
PAYSON_API_PAYMENT_DETAILS_ACTION = "PaymentDetails/"
PAYSON_API_PAYMENT_UPDATE_ACTION = "PaymentUpdate/"
PAYSON_API_VALIDATE_ACTION = "Validate/"
PAYSON_WWW_PAY_FORWARD_URL = 'https://www.payson.se/paysecure/?token=%s'
PAYSON_WWW_PAY_FORWARD_TEST_URL = \
    'https://test-www.payson.se/paysecure/?token=%s'
PAYSON_TEST_AGENT_ID = ('1', '4')
PAYSON_TEST_AGENT_KEY = ('fddb19ac-7470-42b6-a91d-072cb1495f0a',
                         '2acab30d-fe50-426f-90d7-8c60a7eb31d4')

log = logging.getLogger('Payson API')


class PaysonApi():

    def __init__(self, user_id, user_key):
        """Constructor

        :param user_id: Agent ID obtained from Payson
        :type user_id: str
        :param user_key: Password (MD5 Key) obtained from Payson
        :type user_key: str
        """
        if (user_id in PAYSON_TEST_AGENT_ID and
            user_key in PAYSON_TEST_AGENT_KEY):
            endpoint = PAYSON_TEST_API_ENDPOINT
            self.forward_pay_url = PAYSON_WWW_PAY_FORWARD_TEST_URL
        else:
            endpoint = PAYSON_API_ENDPOINT
            self.forward_pay_url = PAYSON_WWW_PAY_FORWARD_URL

        self.user_id = user_id
        self.user_key = user_key

        def mkcmd(cmd):
            return '/'.join((endpoint, PAYSON_API_VERSION, cmd))

        self.pay_cmd = mkcmd(PAYSON_API_PAY_ACTION)
        self.get_payment_details_cmd = mkcmd(PAYSON_API_PAYMENT_DETAILS_ACTION)
        self.update_payment_details_cmd = \
            mkcmd(PAYSON_API_PAYMENT_UPDATE_ACTION)
        self.validate_ipn_cmd = mkcmd(PAYSON_API_VALIDATE_ACTION)
        self.send_ipn_cmd = mkcmd('SendIPN/')

    def pay(self,
            returnUrl,
            cancelUrl,
            memo,
            senderEmail,
            senderFirstName,
            senderLastName,
            receiverList,
            ipnNotificationUrl=None,
            localeCode=None,
            currencyCode=None,
            fundingList=tuple(),
            feesPayer=None,
            invoiceFee=None,
            custom=None,
            trackingId=None,
            guaranteeOffered=None,
            orderItemList=tuple(),
            showReceiptPage=True):
        """The starting point for any kind of payment.

        For a longer description, including possible parameter values and 
        constraints, see https://api.payson.se/#Initializepayment

        :type returnUrl: unicode
        :type cancelUrl: unicode
        :type memo: unicode
        :type senderEmail: unicode
        :type senderFirstName: unicode
        :type senderLastName: unicode
        :type receiverList: iterable of Receiver instances
        :type ipnNotificationUrl: unicode
        :type localeCode: unicode
        :type currencyCode: unicode
        :type fundingList: iterable with unicode instances
        :type feesPayer: unicode
        :type invoiceFee: decimal.Decimal
        :type custom: any json serializable Python object
        :type trackingId: unicode or int
        :type guaranteeOffered: unicode
        :type orderItemList: iterable of OrderItem instances
        :type showReceiptPage: bool
        :rtype: PayResponse
        """
        pay_request = {'returnUrl': returnUrl,
                       'cancelUrl': cancelUrl,
                       'memo': memo.encode('utf-8'),
                       'senderEmail': senderEmail.encode('utf-8'),
                       'senderFirstName': senderFirstName.encode('utf-8'),
                       'senderLastName': senderLastName.encode('utf-8')}
        for i, v in enumerate(receiverList):
            k = 'receiverList.receiver(%d).%s'
            pay_request[k % (i, 'email')] = v.email.encode('utf-8')
            pay_request[k % (i, 'amount')] = str(v.amount)
            if v.primary is not None:
                pay_request[k % (i, 'primary')] = json.dumps(v.primary)
            if v.firstName:
                pay_request[k % (i, 'firstName')] = v.firstName.encode('utf-8')
            if v.lastName:
                pay_request[k % (i, 'lastName')] = v.lastName.encode('utf-8')
        if ipnNotificationUrl:
            pay_request['ipnNotificationUrl'] = ipnNotificationUrl
        if localeCode:
            pay_request['localeCode'] = localeCode
        if currencyCode:
            pay_request['currencyCode'] = currencyCode
        for i, v in enumerate(fundingList):
            pay_request['fundingList.fundingConstraint'
                        '(%d).constraint' % i] = v
        if feesPayer:
            pay_request['feesPayer'] = feesPayer
        if invoiceFee is not None:
            pay_request['invoiceFee'] = str(invoiceFee)
        if custom is not None:
            pay_request['custom'] = json.dumps(custom)
        if trackingId is not None:
            pay_request['trackingId'] = trackingId.encode('utf-8')
        if guaranteeOffered:
            pay_request['guaranteeOffered'] = guaranteeOffered
        for i, v in enumerate(orderItemList):
            k = 'orderItemList.orderItem(%d).%s'
            pay_request[k % (i, 'description')] = v.description.encode('utf-8')
            pay_request[k % (i, 'sku')] = str(v.sku)
            pay_request[k % (i, 'quantity')] = str(v.quantity)
            pay_request[k % (i, 'unitPrice')] = str(v.unitPrice)
            pay_request[k % (i, 'taxPercentage')] = str(v.taxPercentage)
        if showReceiptPage is False:
            pay_request['showReceiptPage'] = json.dumps(showReceiptPage)
        response_dict = self._do_request(self.pay_cmd, pay_request)
        pay_response = PayResponse(self.forward_pay_url, response_dict)
        log.info('PAYSON: %s response: %r' % (self.pay_cmd, response_dict))
        return pay_response

    def payment_details(self, token):
        """Get details about an existing payment.

        For a longer description, including possible parameter values, see 
        https://api.payson.se/#PaymentDetailsrequest

        :type token: unicode
        :rtype: PaymentDetailsResponse
        """
        response_dict = self._do_request(
            self.get_payment_details_cmd,
            {'token': token})
        payment_details_response = PaymentDetailsResponse(response_dict)
        log.info('PAYSON: %s response: %r' % (self.get_payment_details_cmd,
                                              response_dict))
        return payment_details_response

    def payment_update(self, token, action):
        """Update an existing payment, for instance mark an order as shipped or canceled. 

        For a longer description, including possible parameter values, see 
        https://api.payson.se/#PaymentUpdaterequest

        :type token: unicode
        :type action: unicode
        :rtype: ResponseEnvelope
        """
        response_dict = self._do_request(
            self.update_payment_details_cmd,
            {'token': token,
             'action': action})
        response = ResponseEnvelope(response_dict)
        log.info('PAYSON: %s response: %r' % (self.update_payment_details_cmd,
                                              response_dict))
        return response.ack == 'SUCCESS'

    def validate(self, message):
        """This method is used to validate the content of the IPN message that was sent to your ipnNotificationUrl.

        For a longer description, including possible parameter values, see 
        https://api.payson.se/#Validaterequest

        :param message: complete unaltered query string from the IPN request
        :type message: str 
        :returns: True if IPN is verified, otherwise False
        :rtype: bool
        """
        response = self._send_request(self.validate_ipn_cmd, message)
        log.info('PAYSON: %s response: %r' % (self.validate_ipn_cmd,
                                              response))
        if response == 'VERIFIED':
            return True
        elif response == 'INVALID':
            return False
        else:
            raise ValueError('Invalid response for IPN validation.')

    def _do_request(self, cmd, data):
        query = urllib.urlencode(data)
        response_body = self._send_request(cmd, query)
        data = urlparse.parse_qs(response_body)
        return {k: v[0] for k, v in data.items()}

    def _send_request(self, cmd, query):
        request = urllib2.Request(cmd, query)
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        request.add_header('PAYSON-SECURITY-USERID', self.user_id)
        request.add_header('PAYSON-SECURITY-PASSWORD', self.user_key)
        log.info('PAYSON: Calling %s with %r' % (cmd, query))
        try:
            response = urllib2.urlopen(request)
        except urllib2.URLError, e:
            log.error('Exception when calling {0}: {1}'.format(cmd, e))
            raise
        return response.read()


class OrderItem(object):
    """Holds Order Item values used in pay operation.
    """
    def __init__(self,
                 description,
                 sku,
                 quantity,
                 unitPrice,
                 taxPercentage):
        """Constructor.

        Payson API documentation states that some of these values are optional, 
        this is incorrect, all must be provided.

        For possible parameter values and constraints see 
        https://api.payson.se/#Initializepayment

        :param description: Description of this item.
        :type description: unicode
        :param sku: SKU of this item.
        :type sku: unicode or int
        :param quantity: Quantity of this item.
        :type quantity: decimal.Decimal
        :param unitPrice: The unit price of this item not including VAT.
        :type unitPrice: decimal.Decimal
        :param taxPercentage: Tax percentage for this item.
        :type taxPercentage: decimal.Decimal
        """
        self.description = description
        self.sku = sku
        self.quantity = quantity
        self.unitPrice = unitPrice
        self.taxPercentage = taxPercentage


class Receiver(object):
    """Holds receiver data.

    Used both in pay request and in payment details objects.
    """
    def __init__(self,
                 email,
                 amount,
                 primary=None,
                 firstName=None,
                 lastName=None):
        self.email = email
        self.amount = decimal.Decimal(amount)
        self.primary = primary
        self.firstName = firstName
        self.lastName = lastName

    @classmethod
    def from_response_data(cls, data):
        receivers = []
        i = 0
        while 'receiverList.receiver(%d).email' % i in data:
            primary = data.get('receiverList.receiver(%d).primary' % i)
            primary = json.loads(primary.lower()) if primary else None
            receivers.append(
                cls(data['receiverList.receiver(%d).email' % i],
                    data['receiverList.receiver(%d).amount' % i],
                    primary)
            )
            i += 1
        return receivers


class Error(object):

    def __init__(self, errorId, message, parameter=None):
        self.errorId = int(errorId)
        self.message = message
        self.parameter = parameter

    @classmethod
    def from_response_dict(cls, data):
        errors = []
        i = 0
        while 'errorList.error(%d).errorId' % i in data:
            errors.append(
                cls(data['errorList.error(%d).errorId' % i],
                    data['errorList.error(%d).message' % i],
                    data.get('errorList.error(%d).parameter' % i))
            )
            i += 1
        return errors


class ResponseEnvelope(object):

    def __init__(self, data):
        self.ack = data['responseEnvelope.ack']
        self.timestamp = datetime.datetime.strptime(
            data['responseEnvelope.timestamp'], '%Y-%m-%dT%H:%M:%S')
        self.correlationId = data['responseEnvelope.correlationId']
        self.errorList = Error.from_response_dict(data)

    @property
    def success(self):
        """True if request succeeded."""
        return self.ack == 'SUCCESS'


class PayResponse(object):
    """Holds the returned values from the pay operation. 
    """
    def __init__(self, forward_pay_url, data):
        self.responseEnvelope = ResponseEnvelope(data)
        self.token = data.get('TOKEN', '')
        self.forward_pay_url = forward_pay_url % self.token if self.token \
            else ''

    @property
    def success(self):
        """True if request (not payment) succeeded."""
        return self.responseEnvelope.success


class ShippingAddress(object):
    """Invoice shipping address info.
    """
    def __init__(self, data):
        self.name = data['shippingAddress.name'].decode('utf-8')
        self.streetAddress = data['shippingAddress.streetAddress'].decode('utf-8')
        self.postalCode = data['shippingAddress.postalCode'].decode('utf-8')
        self.city = data['shippingAddress.city'].decode('utf-8')
        self.country = data['shippingAddress.country'].decode('utf-8')


class PaymentDetails(object):
    """Holds the returned values from the payment_details and IPN callback operations.

    See https://api.payson.se/#PaymentDetailsrequest for a description of 
    attributes.
    """
    def __init__(self, data):
        self.purchaseId = data.get('purchaseId', '')
        self.token = data.get('token')
        self.senderEmail = data.get('senderEmail', '')
        self.status = data['status']
        self.type = data['type']
        self.guaranteeStatus = data.get('guaranteeStatus')
        self.guaranteeDeadlineTimestamp = datetime.datetime.strptime(
             data['guaranteeDeadlineTimestamp'], '%Y-%m-%dT%H:%M:%S') \
             if 'guaranteeDeadlineTimestamp' in data else None
        self.invoiceStatus = data.get('invoiceStatus')
        custom = data.get('custom')
        self.custom = custom and json.loads(custom)
        self.trackingId = data.get('trackingId', '').decode('utf-8')
        self.currencyCode = data['currencyCode']
        self.receiverFee = decimal.Decimal(data['receiverFee'])
        self.receiverList = Receiver.from_response_data(data)
        if 'shippingAddress.name' in data:
            self.shippingAddress = ShippingAddress(data)
        self.post_data = data.copy()

    @property
    def amount(self):
        return sum(receiver.amount for receiver in self.receiverList)


class PaymentDetailsResponse(PaymentDetails):
    """Returned from payment_details.

    This class contains PaymentDetails with a ResponseEnvelope.
    """
    def __init__(self, data):
        super(PaymentDetailsResponse, self).__init__(data)
        self.responseEnvelope = ResponseEnvelope(data)

    @property
    def success(self):
        """True if request succeeded."""
        return self.responseEnvelope.success
