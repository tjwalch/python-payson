# -*- coding: utf-8 -*-
import datetime
import decimal
import urllib2
import urlparse

import mechanize

import payson

PAYSON_AGENT_ID = '1'
PAYSON_AGENT_KEY = 'fddb19ac-7470-42b6-a91d-072cb1495f0a'
return_url = "http://localhost/return_url"
cancel_url = "http://localhost/cancel_url"
receiver = payson.Receiver(email='testagent-1@payson.se',
                           firstName=u'Åke',
                           lastName=u'Öster',
                           amount=125,
                           primary=False)


def test_pay_transfer():
    custom = ['list', 'of', 'custom', 'things', u'åäö']
    api = payson.PaysonApi(PAYSON_AGENT_ID,
                           PAYSON_AGENT_KEY)
    r = api.pay(returnUrl=return_url,
                cancelUrl=cancel_url,
                memo="test memo",
                senderEmail='test-shopper@payson.se',
                senderFirstName=u'Tester',
                senderLastName=u'Räksmörgås',
                receiverList=[receiver, ],
                custom=custom,
                fundingList=['BANK', 'CREDITCARD'],
                localeCode='se',
                currencyCode='SEK',
                feesPayer='PRIMARYRECEIVER',
                trackingId=u'ÅÄÖ',
                guaranteeOffered='NO',
                orderItemList=[payson.OrderItem('description item one',
                                                1,
                                                10,
                                                5,
                                                decimal.Decimal(0.25)),
                               payson.OrderItem('description item two',
                                                2,
                                                5,
                                                10,
                                                decimal.Decimal(0.25)), ])
    assert r.token, r.responseEnvelope.errorList[0].message
    assert isinstance(r.responseEnvelope.timestamp, datetime.datetime)
    br = mechanize.Browser()
    br.open(r.forward_pay_url)
    br.select_form(nr=0)
    br.form['QuickAgentCheckout1$rblPaymentMethod'] = ['SwedBank']
    br.submit()
    assert br.viewing_html()
    try:
        br.select_form(nr=0)
        br.set_handle_redirect(False)
        br.submit(name='btnAccept')
    except urllib2.HTTPError, response:
        location = response.hdrs.get('location')
        try:
            br.open(location)
        except urllib2.HTTPError, response:
            location = response.hdrs.get('location')
            params = urlparse.parse_qs(location.split('?')[1])
            assert 'token' in params, params
            assert params['token'][0] == r.token, \
                 "%r != %r" % (params['token'], r.token)
    finally:
        br.set_handle_redirect(True)

    r2 = api.payment_details(params['token'][0])
    assert r2.success
    assert r2.status == 'COMPLETED'
    assert r2.custom == custom, custom
    assert r2.trackingId == u'ÅÄÖ'


def test_error():
    api = payson.PaysonApi(PAYSON_AGENT_ID,
                           PAYSON_AGENT_KEY)
    r = api.pay(returnUrl=return_url,
                cancelUrl=cancel_url,
                memo="test memo",
                senderEmail='test-shopper@payson.se',
                senderFirstName=u'Tester',
                senderLastName=u'Räksmörgås',
                receiverList=[receiver, ],
                orderItemList=[payson.OrderItem('description item one',
                                            1,
                                            10,
                                            5,
                                            decimal.Decimal(0.25))])
    assert not r.success
    assert r.responseEnvelope.errorList[0].errorId == 590001


def test_pay_invoice():
    api = payson.PaysonApi(PAYSON_AGENT_ID,
                           PAYSON_AGENT_KEY)
    r = api.pay(returnUrl=return_url,
                cancelUrl=cancel_url,
                memo="test memo",
                senderEmail='test-shopper@payson.se',
                senderFirstName=u'Tester',
                senderLastName=u'Räksmörgås',
                receiverList=[receiver, ],
                fundingList=['INVOICE', ],
                orderItemList=[payson.OrderItem('description item one',
                                                1,
                                                10,
                                                5,
                                                decimal.Decimal(0.25)),
                               payson.OrderItem('description item two',
                                                2,
                                                5,
                                                10,
                                                decimal.Decimal(0.25)), ])
    assert r.success, r.responseEnvelope.errorList[0].message
    pnr = '230119-6412'
    br = mechanize.Browser()
    br.open(r.forward_pay_url)
    br.select_form(nr=0)
    br['QuickAgentCheckout1$txtSsn'] = pnr
    br.submit()
    try:
        br.select_form(nr=0)
        br.set_handle_redirect(False)
        br.submit()
    except urllib2.HTTPError, response:
        location = response.hdrs.get('location')
        params = urlparse.parse_qs(location.split('?')[1])
        assert 'TOKEN' in params, params
        assert params['TOKEN'][0] == r.token, \
             "%r != %r" % (params['token'], r.token)
    finally:
        br.set_handle_redirect(True)

    token = params['TOKEN'][0]
    r2 = api.payment_details(token)
    assert r2.success
    assert r2.status == 'PENDING', r2.status
    assert r2.invoiceStatus == 'ORDERCREATED', r2.invoiceStatus
    assert r2.shippingAddress

    assert api.payment_update(token, 'SHIPORDER')
    r4 = api.payment_details(token)
    assert r4.success
    assert r4.status == 'PENDING', r4.status
    assert r4.invoiceStatus == 'SHIPPED', r4.invoiceStatus
