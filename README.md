# python-payson

Python API to the [Payson payments provider](http://www.payson.se).

## Installation
The entire library is contained in a single Python module, `payson.py`. Just drop it anywhere in your projects PYTHONPATH.
It is not dependent on anything outside the Python standard library (except in the tests). 

Tested with Python 2.7.

## Examples
Initiate payment:

    import decimal
    import payson

    from settings import payson_user_id, payson_user_key

    api = payson.PaysonApi(payson_user_id, payson_user_key)

    receiver = payson.Receiver(email='payments@example.com',
                               firstName=u'Pelle',
                               lastName=u'Persson',
                               amount=decimal.Decimal('125.0'),
                               primary=False)

    payment_response = api.pay(returnUrl='http://example.com/return_url',
                               cancelUrl='http://example.com/cancel_url',
                               memo=u'Purchase of nice things.',
                               senderEmail='anna.andersson@example.com',
                               senderFirstName=u'Anna',
                               senderLastName=u'Andersson',
                               receiverList=[receiver, ])
                           
    if payment_response.success:
        # Redirect users browser to Payson
        redirect(payment_response.forward_pay_url)

Get payment details:

    payment_details = api.payment_details(payment_response.token)
    if payment_details.status == 'COMPLETED':
        #  We got money :)
        ...

## Data Types
- all strings except urls and e-mail addresses are expected to be unicode 
- monetary values returned are converted to decimal.Decimal
- timestamps are converted to datetime.datetime
- true/false is converted to bool
- error codes are converted to int
- the 'custom' field is serialized/deserialized with JSON
        
## More documentation
Please see the docstrings included in `payson.py` and/or the [Payson API documentation](http://api.payson.se)

## Testing
The PaysonApi constructor detects if user id and key used are testing credentials and will then use the Payson test system.

The included `test.py` file includes some automated tests using python-mechanize that can be run with nosetests.

## Contact
The author of this software offers integration services if requested. Reach him through github.

Issues are reported through github.
