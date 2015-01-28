"""Count the number of unique message threads in a Gmail inbox, by logging
in with IMAP and checking the count of unique values of the X-GM-THRID header.

This example was helpful:
http://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/

"""
import imaplib
import re
from collections import defaultdict
from dateutil.parser import parser
from email.parser import HeaderParser
from operator import itemgetter

thread_id_re = re.compile('X-GM-THRID (\d+)')

date_parser = parser()
header_parser = HeaderParser()

def thread_id_from_message_tuple(m):
    result = thread_id_re.search(m[0])
    return result.group(1) if result else None

def thread_info_from_message_tuple(m):
    parsed = dict(header_parser.parsestr(m[1]).items())
    return {
        'thread_id': thread_id_from_message_tuple(m),
        'date': parsed['Date'],
        'date_ts': date_str_to_timestamp(parsed['Date']),
        'subject': parsed['Subject'],
        'from': parsed['From'],
    }

def date_str_to_timestamp(date_str):
    return int(date_parser.parse(date_str).strftime('%s'))

def gmail_thread_info(email, password):
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(email, password)

    mail.select('INBOX')

    _, (uid_list,) = mail.uid('search', None, 'ALL')
    uids = uid_list.split(' ')

    _, inbox = mail.uid('fetch', ','.join(uids), '(X-GM-THRID BODY.PEEK[HEADER])')

    # every other "message" is the string ")"
    actual_messages = [inbox[i] for i in xrange(0, len(inbox), 2)]
    thread_infos = map(thread_info_from_message_tuple, actual_messages)

    # Group messages into Gmail threads
    thread_id_to_messages = defaultdict(list)
    for m in thread_infos:
        thread_id_to_messages[m['thread_id']].append(m)

    # Pick the one whose subject doesn't start with "Re:"
    thread_id_to_single_message = {}
    for thread_id, messages in thread_id_to_messages.iteritems():
        if len(messages) == 1:
            thread_id_to_single_message[thread_id] = messages[0]
        else:
            subjects_without_reply = [m for m in messages if not m['Subject'].startswith('Re: ')]
            if subjects_without_reply:
                thread_id_to_single_message[thread_id] = subjects_without_reply[0]
            else:
                thread_id_to_single_message[thread_id] = messages[0]

    out = []

    # Sort by timestamp
    out = list(sorted(thread_id_to_single_message.itervalues(), key=itemgetter('date_ts'), reverse=True))

    return out
