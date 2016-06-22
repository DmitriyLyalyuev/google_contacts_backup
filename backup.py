#!/usr/bin/python
import json
import vobject
import argparse
import gdata.contacts.client
from gdata.gauth import AuthSubToken
from oauth2client import tools
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage

def oauth2_authorize_application(client_secret_file, scope, credential_cache_file='cred_cache.json'):
    """
    authorize an application to the requested scope by asking the user in a browser.

    :param client_secret_file: json file containing the client secret for an offline application
    :param scope: scope(s) to authorize the application for
    :param credential_cache_file: if provided or not None, the credenials will be cached in a file.
        The user does not need to be reauthenticated
    :return OAuth2Credentials object
    """
    FLOW = flow_from_clientsecrets(client_secret_file,
                                   scope=scope)
    storage = Storage(credential_cache_file)
    credentials = storage.get()
    if credentials == None:
        credentials = tools.run_flow(FLOW, storage, tools.argparser.parse_args([]))
    return credentials

def main():
    parser = argparse.ArgumentParser(description='Backup google contacts')
    parser.add_argument('-a', '--account', dest='account', help='account name', required=True)
    args = parser.parse_args()

    SCOPES = ['https://www.google.com/m8/feeds/', 'https://www.googleapis.com/auth/userinfo.email']
    credentials = oauth2_authorize_application('{0}_client_id.json'.format(args.account), scope=SCOPES, credential_cache_file='auth_cache_{0}.json'.format(args.account))
    token_string = credentials.get_access_token().access_token

    with open('{0}_client_id.json'.format(args.account)) as f:
        oauth2_client_secret = json.load(f)

    auth_token = gdata.gauth.OAuth2Token(
        client_id=oauth2_client_secret['installed']['client_id'],
        client_secret=oauth2_client_secret['installed']['client_secret'],
        scope=SCOPES,
        user_agent='MyUserAgent/1.0',
        access_token=credentials.get_access_token().access_token,
        refresh_token=credentials.refresh_token)

    client = gdata.contacts.client.ContactsClient(auth_token=auth_token)
    query = gdata.contacts.client.ContactsQuery()
    query.max_results = 5000
    feed = client.GetContacts(q = query)

    for i, c in enumerate(feed.entry):
        emails = []
        phones = []
        try:
            if c.name.full_name:
                full_name = c.name.full_name.text
            if 'id\:' not in c.content:
                notes = c.content.text
        except:
            pass
        for email in c.email:
            try:
                if c.name.full_name:
                    emails.append(email.address)
            except:
                continue
        for phone in c.phone_number:
            phones.append(phone.text)

        j = vobject.vCard()
        o = j.add('fn')
        o.value = full_name

        o = j.add('n')
        o.value = vobject.vcard.Name( family='', given='' )
        if len(phones) > 0:
            for phone in phones:
                o = j.add('tel')
                o.type_param = "cell"
                o.value = phone

        if len(emails) > 0:
            for email in emails:
                o = j.add('email')
                o.value = email

        print(j.serialize())

if __name__ == "__main__":
    main()
