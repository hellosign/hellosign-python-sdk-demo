from django.shortcuts import render_to_response, render
from django.template import RequestContext
from hellosign_sdk.hsclient import HSClient
from hellosign_sdk.resource.signature_request import SignatureRequest
from hellosign_sdk.utils.exception import NoAuthMethod, BadRequest
from settings import API_KEY, CLIENT_ID, SECRET
from .forms import UploadFileForm
import os
import tempfile
import shutil
import json
from querystring_parser import parser


def index(request):
    return render_to_response('hellosign/index.html',
        context_instance=RequestContext(request))

def embedded_signing(request):
    if request.method == 'POST':
        try:
            user_email = request.POST['email']
            user_name = request.POST['name']
            hsclient = HSClient(api_key=API_KEY)

            files = [os.path.dirname(os.path.realpath(__file__)) + "/docs/nda.pdf"]
            signers = [{"name": user_name, "email_address": user_email}]
            cc_email_addresses = []
            sr = hsclient.send_signature_request_embedded(
                "1", CLIENT_ID, files, [], "NDA with Acme Co.",
                "The NDA we talked about", "Please sign this NDA and then we" +
                " can discuss more. Let me know if you have any questions.",
                "", signers, cc_email_addresses)
            embedded = hsclient.get_embeded_object(sr.signatures[0]["signature_id"])
        except KeyError:
            return render(request, 'hellosign/embedded_signing.html', {
                'error_message': "Please enter both your name and email.",
            })
        except NoAuthMethod:
            return render(request, 'hellosign/embedded_signing.html', {
                'error_message': "Please update your settings to include a " +
                "value for API_KEY.",
            })
        else:
            return render(request, 'hellosign/embedded_signing.html', {
                    'client_id': CLIENT_ID,
                    'sign_url': str(embedded.sign_url)
                    })
    else:
        return render_to_response('hellosign/embedded_signing.html',
            context_instance=RequestContext(request))

def embedded_requesting(request):
    if request.method == 'POST':
        try:
            user_email = request.POST['user_email']
            user_name = request.POST['user_name']
            signer_name = request.POST['signer_name']
            signer_email = request.POST['signer_email']
            subject = request.POST['subject']
            message = request.POST['message']
            hsclient = HSClient(api_key=API_KEY)

            files = []
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                files.append(handle_uploaded_file(request.FILES['upload_file']))
            signers = [{"name": signer_name, "email_address": signer_email}]
            cc_email_addresses = []

            sr = hsclient.create_unclaimed_draft(
                "1", CLIENT_ID, '1', user_email, files, [], "request_signature",
                "The NDA we talked about", "Please sign this NDA and then we" +
                " can discuss more. Let me know if you have any questions.",
                signers, cc_email_addresses)
            sign_url = sr.claim_url
        # except KeyError:
        #     return render(request, 'hellosign/embedded_requesting.html', {
        #         'error_message': "Please enter both your name and email.",
        #     })

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
        return render_to_response('hellosign/embedded_requesting.html',
            context_instance=RequestContext(request))

def embedded_template_requesting(request):
    try:
        hsclient = HSClient(api_key=API_KEY)
    except NoAuthMethod:
        return render(request, 'hellosign/embedded_template_requesting.html', {
            'error_message': "Please update your settings to include a " +
            "value for API_KEY.",
        })
    if request.method == 'POST':
        try:
            signers = []
            post_dict = parser.parse(request.POST.urlencode())
            template_id = post_dict["template"]
            for key, value in post_dict["signerRole"].iteritems():
                if value:
                    value['role_name'] = key
                    signers.append(value)
            ccs = []
            for key, value in post_dict["ccRole"].iteritems():
                # if value:
                ccs.append({'role_name': key, 'email_address': value})
            custom_fields = []
            for key, value in post_dict["cf"].iteritems():
                if value:
                    custom_fields.append({key: value})
            sr = hsclient.send_signature_request_embedded_with_rf(test_mode = "1",
                client_id = CLIENT_ID, reusable_form_id = template_id, title = "NDA with Acme Co.",
                subject = "The NDA we talked about", message = "Please sign this NDA and then we" +
                " can discuss more. Let me know if you have any questions.",
                signing_redirect_url = "", signers = signers, ccs = ccs, custom_fields = custom_fields)
            embedded = hsclient.get_embeded_object(sr.signatures[0]["signature_id"])
        # TODO: need some more validations here
        # except KeyError:
        #     return render(request, 'hellosign/embedded_template_requesting.html', {
        #         'error_message': "Please enter both your name and email.",
        #     })
        except NoAuthMethod:
            pass
        else:
            return render(request, 'hellosign/embedded_template_requesting.html', {
                    'client_id': CLIENT_ID,
                    'sign_url': str(embedded.sign_url)
                    })
    else:
        rf_list = hsclient.get_reusable_form_list()
        templates = "[";
        for rf in rf_list:
            # print json.dumps(rf.json_data)
            templates = templates + json.dumps(rf.json_data) + ", "
        templates = templates + "]"
        return render(request, 'hellosign/embedded_template_requesting.html', {
                    'templates': templates
                    })


def oauth(request):
    try:
        oauth_accesstoken = request.session['access_token']
        oauth_token_type = request.session['token_type']
    except KeyError:
        oauth_accesstoken = None
        oauth_token_type = None

    if request.method == 'POST':
        try:
            user_email = request.POST['email']
            user_name = request.POST['name']

            user_hsclient = HSClient(api_accesstoken=request.session['oauth_accesstoken'], api_accesstokentype=request.session['oauth_token_type'])

            files = [os.path.dirname(os.path.realpath(__file__)) + "/docs/nda.pdf"]
            signers = [{"name": user_name, "email_address": user_email}]
            cc_email_addresses = []
            sr = user_hsclient.send_signature_request(
                "1", files, [], "OAuth Demo - NDA",
                "The NDA we talked about", "Please sign this NDA and then we" +
                " can discuss more. Let me know if you have any questions.",
                "", signers, cc_email_addresses)
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
                    'oauth_accesstoken': request.session['oauth_accesstoken'],
                    'oauth_token_type': request.session['oauth_token_type'],
                    'client_id': CLIENT_ID
                    })
            else:
                return render(request, 'hellosign/oauth.html', {
                    'error_message': 'Unknow error',
                    'client_id': CLIENT_ID
                    })
    else:
        return render(request, 'hellosign/oauth.html', {
                'oauth_accesstoken': oauth_accesstoken,
                'oauth_token_type': oauth_token_type,
                'client_id': CLIENT_ID
            })

def oauth_callback(request):
    try:
        code = request.GET['code']
        state = request.GET['state']
        hsclient = HSClient(api_key=API_KEY)
        oauth = hsclient.get_oauth_data(code, CLIENT_ID, SECRET, state)
        request.session['oauth_accesstoken'] = oauth.access_token
        request.session['oauth_token_type'] = oauth.access_token_type
        # pdb.set_trace()

    except KeyError:
        return render(request, 'hellosign/oauth_callback.html', {
                'error_message': "No code or state found",
            })
    except BadRequest, e:
        # pdb.set_trace()
        return render(request, 'hellosign/oauth_callback.html', {
                'error_message': str(e),
            })
    return render_to_response('hellosign/oauth_callback.html',
            context_instance=RequestContext(request))


def handle_uploaded_file(source):
    fd, filepath = tempfile.mkstemp(prefix=source.name, dir='/tmp/')
    with open(filepath, 'wb') as dest:
        shutil.copyfileobj(source, dest)
    return filepath
