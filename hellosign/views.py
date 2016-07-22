from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.http import HttpResponse
from hellosign_sdk import HSClient
from hellosign_sdk.resource import SignatureRequest
from hellosign_sdk.utils.exception import NoAuthMethod, BadRequest
from settings import API_KEY, CLIENT_ID, SECRET
from .forms import UploadFileForm
import os
import tempfile
import shutil
import json
import traceback
from querystring_parser import parser

EVENT_OK_RESP_TOKEN = "Hello API Event Received"

def index(request):
    ''' Landing page '''
    return render_to_response('hellosign/index.html', context_instance=RequestContext(request))

def embedded_signing(request):
    ''' Embedded signing demo '''
    if request.method == 'POST':
        try:

            user_email = request.POST['email']
            user_name = request.POST['name']
            hsclient = HSClient(api_key=API_KEY)

            files = [os.path.dirname(os.path.realpath(__file__)) + "/docs/nda.pdf"]
            signers = [{"name": user_name, "email_address": user_email}]
            cc_email_addresses = []
            sr = hsclient.send_signature_request_embedded(
                test_mode=True,
                client_id=CLIENT_ID,
                files=files,
                title="NDA with Acme Co.",
                subject="The NDA we talked about",
                message="Please sign this NDA and then we can discuss more. Let me know if you have any questions.",
                signers=signers,
                cc_email_addresses=cc_email_addresses)
            embedded = hsclient.get_embedded_object(sr.signatures[0].signature_id)
        except KeyError:
            return render(request, 'hellosign/embedded_signing.html', {
                'error_message': "Please enter both your name and email."
            })
        except NoAuthMethod:
            return render(request, 'hellosign/embedded_signing.html', {
                'error_message': "Please update your settings to include a value for API_KEY."
            })
        else:
            return render(request, 'hellosign/embedded_signing.html', {
                'client_id': CLIENT_ID,
                'sign_url': str(embedded.sign_url)
            })
    else:
        return render_to_response('hellosign/embedded_signing.html', context_instance=RequestContext(request))

def embedded_requesting(request):
    if request.method == 'POST':
        try:

            user_email = request.POST['user_email']
            signer_name = request.POST['signer_name']
            signer_email = request.POST['signer_email']

            hsclient = HSClient(api_key=API_KEY)

            files = []
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                files.append(handle_uploaded_file(request.FILES['upload_file']))
            signers = [{"name": signer_name, "email_address": signer_email}]
            cc_email_addresses = []

            sr = hsclient.create_embedded_unclaimed_draft(
                test_mode=True,
                client_id=CLIENT_ID,
                is_for_embedded_signing=True,
                requester_email_address=user_email,
                files=files,
                draft_type="request_signature",
                subject="The NDA we talked about",
                message="Please sign this NDA and then we can discuss more. Let me know if you have any questions.",
                signers=signers,
                cc_email_addresses=cc_email_addresses)

            sign_url = sr.claim_url

        except NoAuthMethod:
            return render(request, 'hellosign/embedded_requesting.html', {
                'error_message': "Please update your settings to include a " +
                "value for API_KEY.",
            })
        else:
            return render(request, 'hellosign/embedded_requesting.html', {
                'client_id': CLIENT_ID,
                'sign_url': str(sign_url)
            })
    else:

        return render_to_response('hellosign/embedded_requesting.html', context_instance=RequestContext(request))

def embedded_signing_with_template(request):
    try:
        hsclient = HSClient(api_key=API_KEY)
    except NoAuthMethod:
        return render(request, 'hellosign/embedded_signing_with_template.html', {
            'error_message': "Please update your settings to include a value for API_KEY."
        })
    if request.method == 'POST':
        try:
            signers = []
            post_dict = parser.parse(request.POST.urlencode())
            template_id = post_dict["template"]
            for (key, value) in post_dict["signerRole"].iteritems():
                if value:
                    value['role_name'] = key
                    signers.append(value)

            ccs = []
            if 'ccRole' in post_dict and len(post_dict['ccRole']) > 0:
                for (key, value) in post_dict["ccRole"].iteritems():
                    # if value:
                    ccs.append({'role_name': key, 'email_address': value})

            custom_fields = []
            if 'cf' in post_dict and len(post_dict['cf']) > 0:
                for (key, value) in post_dict["cf"].iteritems():
                    if value:
                        custom_fields.append({key: value})

            sr = hsclient.send_signature_request_embedded_with_template(
                test_mode=True,
                client_id=CLIENT_ID,
                template_id=template_id,
                title="NDA with Acme Co.",
                subject="The NDA we talked about",
                message="Please sign this NDA and then we can discuss more. Let me know if you have any questions.",
                signing_redirect_url=None,
                signers=signers,
                ccs=ccs,
                custom_fields=custom_fields)

            embedded = hsclient.get_embedded_object(sr.signatures[0].signature_id)

        # TODO: need some more validations here
        # except KeyError:
        #     return render(request, 'hellosign/embedded_signing_with_template.html', {
        #         'error_message': "Please enter both your name and email.",
        #     })
        except NoAuthMethod:
            pass
        else:
            return render(request, 'hellosign/embedded_signing_with_template.html', {
                'client_id': CLIENT_ID,
                'sign_url': str(embedded.sign_url)
            })
    else:
        template_list = hsclient.get_template_list()
        templates = [];
        for template in template_list:
            template_data = dict(template.json_data)
            del template_data['accounts']
            templates.append(template_data)
        templates = json.dumps(templates)
        return render(request, 'hellosign/embedded_signing_with_template.html', {
            'templates': templates
        })

def oauth(request):
    ''' OAuth demo page '''

    try:
        access_token = request.session['access_token']
        token_type = request.session['token_type']
    except KeyError:
        access_token = None
        token_type = None

    if request.method == 'POST':
        try:
            user_email = request.POST['email']
            user_name = request.POST['name']

            user_hsclient = HSClient(access_token=access_token, access_token_type=token_type)

            files = [os.path.dirname(os.path.realpath(__file__)) + "/docs/nda.pdf"]
            signers = [{"name": user_name, "email_address": user_email }]
            cc_email_addresses = []

            sr = user_hsclient.send_signature_request(
                True,
                files,
                None,
                "OAuth Demo - NDA",
                "The NDA we talked about", "Please sign this NDA and then we can discuss more. Let me know if you have any questions.",
                None,
                signers,
                cc_email_addresses)

        except KeyError:
            return render(request, 'hellosign/oauth.html', {
                'error_message': "Please enter both your name and email.",
                'client_id': CLIENT_ID
            })
        except NoAuthMethod:
            return render(request, 'hellosign/oauth.html', {
                'error_message': "Please update your settings to include a " +
                "value for API_KEY.",
                'client_id': CLIENT_ID
            })
        else:
            if isinstance(sr, SignatureRequest):
                return render(request, 'hellosign/oauth.html', {
                    'message': 'Request sent successfully.',
                    'access_token': access_token,
                    'token_type': token_type,
                    'client_id': CLIENT_ID
                })
            else:
                return render(request, 'hellosign/oauth.html', {
                    'error_message': 'Unknow error',
                    'client_id': CLIENT_ID
                })
    else:
        return render(request, 'hellosign/oauth.html', {
            'access_token': access_token,
            'token_type': token_type,
            'client_id': CLIENT_ID
        })

def oauth_callback(request):
    ''' Handles an OAuth callback.
        Retrieves the code and exchanges it for a valid access token.
    '''

    try:
        code = request.GET['code']
        state = request.GET['state']
        hsclient = HSClient(api_key=API_KEY)
        oauth = hsclient.get_oauth_data(code, CLIENT_ID, SECRET, state)
        request.session['access_token'] = oauth.access_token
        request.session['token_type'] = oauth.access_token_type
        print "Got OAuth Token: %s" % oauth.access_token
    except KeyError:
        return render(request, 'hellosign/oauth_callback.html', {
            'error_message': "No code or state found"
        })
    except BadRequest, e:
        return render(request, 'hellosign/oauth_callback.html', {
            'error_message': str(e)
        })

    return render_to_response('hellosign/oauth_callback.html', context_instance=RequestContext(request))

@csrf_exempt
def event_callback(request):
    ''' Handles an event callback.
        Extracts event info, prints it out and return a successful response.
    '''
    try:

        data = json.loads(request.POST.get('json'))
        event = data['event']

        # Verifying event hash
        import hashlib, hmac
        h = hmac.new(API_KEY, (str(event['event_time']) + event['event_type']), hashlib.sha256).hexdigest()
        valid = (h == event['event_hash'])
        print "\n"
        print "Hash verification: %s" % ("PASSED" if valid else "FAILED")

        # Print out event info
        print "Account: %s" % data['account_guid']
        print "Client: %s\n" % data['client_id']
        print "Event"
        print "------------------"
        print "Type: %s" % event['event_type']
        print "Time: %s" % event['event_time']
        print "Hash: %s" % event['event_hash']
        print "Metadata: %s" % json.dumps(event['event_metadata'], indent=4)
        if 'signature_request' in data:
            print "\n"
            print "Signature Request"
            print "------------------"
            print json.dumps(data['signature_request'], indent=4)
        print "\n"
    except BaseException, e:
        print "ERROR: Could not process event (%s)" % e
        traceback.print_exc()

    return HttpResponse(EVENT_OK_RESP_TOKEN, content_type="html/text")

def handle_uploaded_file(source):
    fd, filepath = tempfile.mkstemp(prefix=source.name, dir='/tmp/')
    with open(filepath, 'wb') as dest:
        shutil.copyfileobj(source, dest)
    return filepath
