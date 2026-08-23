import time

import requests
import os, json, re
import time as t
import imaplib, email
from datetime import datetime, timedelta
import pytz, requests
from email.header import decode_header
from data_classifer import dem_classifer
import requests
import tomllib  # Use 'import tomli as tomllib' if on Python < 3.11

def validation(text, type):
    if type == 'int':
        int_conv = text.split('.')[0]
        if int_conv.isdigit():
            return [int(int_conv), 0]
        else:
            return [0, 0]
    else:
        if len(text) > 30:
            return [str(text)[:30], 1]
        else:
            return [str(text), 0]


class GetSpendings:
    def __init__(self, user, user_data, date="", url='' , classifier_url = '',
                 post=True):
        self.all_transactions = []
        self.user = user
        self.pass_date = date
        self.user_data = user_data
        self.platforms = self.user_data[3]
        self.url = url
        self.imap_url = 'imap.gmail.com'
        self.classifier_url = classifier_url
        self.ist_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        self.post = post
        if self.pass_date == "":
            self.today = t.strftime('%Y-%m-%d')
            self.mail_date = datetime.strptime(self.today, '%Y-%m-%d').strftime('%d-%b-%Y')
            self.pass_date = self.today
        else:
            x = datetime.strptime(self.pass_date, '%Y-%m-%d')
            self.mail_date = x.strftime('%d-%b-%Y')
            self.pass_date = str(str(x).split(' ')[0])

        # Calculate dates
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=50)

        util = dem_classifer(
            user=user,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d") ,
            base_url=self.classifier_url
        )

        util.get_data()

        # dem_classifier.label_data(self.user ,self.pass_date ,30 )

        print(
            f"------------### Data log request for {self.user} for date {self.mail_date} ###-----------{self.ist_time}----")

        self.conn = imaplib.IMAP4_SSL('imap.gmail.com')
        email_id = self.user_data[1]
        password = self.user_data[2]
        self.conn.login(email_id, password)
        self.conn.select('Inbox')
        self.get_all_transaction()

    def get_all_transaction(self):

        print(self.platforms)

        if 'phone_pe' in self.platforms: self.run_phone_pe_log()
        if 'axis_credit' in self.platforms: self.run_axis_credit_log()
        if 'hdfc_debit' in self.platforms: self.run_hdfc_debit_log()
        if 'hdfc_credit' in self.platforms: self.run_hdfc_credit_log()

        for transaction in self.all_transactions:
            self.categorise_by_labeled_data(transaction)
        self.datalog()

    def run_hdfc_credit_log(self):
        #result, message = self.conn.search(None, '(FROM {0} ON {1})'.format("alerts@hdfcbank.net", self.mail_date))
        result, message = self.conn.search(
            None,
            '(OR FROM "alerts@hdfcbank.net" FROM "alerts@hdfcbank.bank.in" ON {0})'.format(self.mail_date)
        )
        transaction_msg_list = []
        for num in message[0].split():
            _, msg_data = self.conn.fetch(num, "(RFC822)")
            raw_mail = msg_data[0][1]
            msg = email.message_from_bytes(raw_mail)
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            if subject.find('Update on your HDFC Bank Credit Card') != -1:

                msg = str(msg)
                message = msg[msg.find('Dear'): msg.find('Regards')]
                pattern = 'ending (.*?) for Rs (.*?) at (.*?) on'

                match = re.search(pattern, message)

                if match is None:
                    print(str(msg))
                else:
                    send_from = match.groups(1)[0]
                    amount = match.groups(1)[1].split('.')[0]
                    send_to = match.groups(1)[2]

                    self.all_transactions.append(
                        [self.user, 'sent', amount, send_to, send_from, '',
                         'hdfc_credit', 'x01'])
                    print( [self.user, 'sent', amount, send_to, send_from, '',
                         'hdfc_credit', 'x01'])

    def run_phone_pe_log(self):

        result, data = self.conn.search(None, '(FROM {0} ON {1})'.format("noreply@phonepe.com", self.mail_date))
        for Tmails, i in enumerate(data[0].split()):
            typ, data = self.conn.fetch(i, '(RFC822)')

            email_message = {
                part.get_content_type(): part.get_payload()
                for part in email.message_from_bytes((data[0][1])).walk()
            }

            for i in email_message:
                if i == 'text/html':
                    mail_string = email_message['text/html'].replace("=", "").replace("  ", "").replace("\xa0",
                                                                                                        "").replace(
                        "\r", "").replace("\n", "").replace("\t", "")
                    pattern = r'<[^>]*>'
                    remove_html = re.sub(pattern, '', mail_string)
                    cleaned_text = re.sub(r'\s+', ' ', remove_html).replace('E282B9', 'Rs').replace('&#8377;',
                                                                                                    'Rs').strip()

                    patter_paid_to = 'Paid to (.*?) Rs (\d+).*?from : (.*?)Bank.*? Message :(.*?)Hi'
                    patter_payment = 'Payment For (\S+) Rs(\d+).*?XX(.*?)'

                    final_match = re.search(patter_paid_to, cleaned_text)
                    if final_match is None:
                        final_match = re.search(patter_payment, cleaned_text)
                        if final_match is None:
                            print(cleaned_text)
                    else:
                        transaction_data = final_match.groups()
                        self.all_transactions.append(
                            [self.user, 'sent', transaction_data[1], transaction_data[0], transaction_data[2],
                             transaction_data[3], 'phone_pe', 'anamoaly'])

    def run_axis_credit_log(self):

        result, message = self.conn.search(None, '(FROM {0} ON {1})'.format("alerts@axisbank.com", self.mail_date))
        transaction_msg_list = []
        for num in message[0].split():
            _, msg_data = self.conn.fetch(num, "(RFC822)")
            raw_mail = msg_data[0][1]
            msg = email.message_from_bytes(raw_mail)
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")
                if subject.find('Transaction alert on Axis Bank Credit Card no') != 1:
                    ref = str(msg).find('Dear')
                    transaction_msg = str(str(msg)[ref:ref + 329])
                    transaction_msg = str(str(transaction_msg).replace("=\n", ''))

                    pattern = r'card no. (\w+)[^INR]+INR (\d+) at (\w+)'
                    match = re.search(pattern, str(transaction_msg))

                    if match is None:
                        pattern = 'declined due to (.*?)\.'
                        match = re.search(pattern, str(transaction_msg))
                        if match is not None:
                            print(str(transaction_msg))
                        else:
                            print(f'Card decline reason unknown')
                    else:
                        transaction_data = match.groups()
                        self.all_transactions.append(
                            [self.user, 'sent', transaction_data[1], transaction_data[2], transaction_data[0], '',
                             'axis_credit', 'x01'])

    def run_hdfc_debit_log(self):

        # result, message = self.conn.search(None, '(FROM {0} ON {1})'.format("alerts@hdfcbank.net", self.mail_date))
        result, message = self.conn.search(
            None,
            '(OR FROM "alerts@hdfcbank.net" FROM "alerts@hdfcbank.bank.in" ON {0})'.format(self.mail_date)
        )

        transaction_msg_list = []
        for num in message[0].split():
            _, msg_data = self.conn.fetch(num, "(RFC822)")
            raw_mail = msg_data[0][1]
            msg = email.message_from_bytes(raw_mail)
            subject, encoding = decode_header(msg["Subject"])[0]
            print(subject)
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            if subject.find('You have done a UPI txn. Check details!') != -1 or subject.find('You have done a UPI txn. Checkdetails!') != -1:
                ref = str(msg).find('Dear')
                transaction_msg = str(str(msg)[ref:ref + 329])
                transaction_msg = str(str(transaction_msg).replace("=\n", ''))
                # pattern = r'Rs.(.*?)\..*?debited from account (.*?) to VPA (.*?) on'
                pattern = r'Rs\.(.*?)\s+is debited from your account ending\s+(.*?)\s+towards VPA\s+(.*?)\s+on'
                match = re.search(pattern, str(transaction_msg))

                if match is None:
                    print(str(transaction_msg))
                else:
                    transaction_data = match.groups()
                    self.all_transactions.append(
                        [self.user, 'sent', transaction_data[0], transaction_data[2], transaction_data[1], '',
                         'hdfc_debit', 'x01'])


    def categorise_by_labeled_data(self, transaction):
        file_name = f'classification_data_{self.user}.json'
        if os.path.exists(file_name):
            label_data = json.loads(open(file_name).read())
            sender = transaction[3]
            if sender in label_data['data'].keys():
                print(f" {sender} -> {label_data['data'][sender][0][0]} , {label_data['data'][sender][0][1]} Categorised")
                transaction.insert(5, label_data['data'][sender][0][0])
                transaction.insert(8, label_data['data'][sender][0][1])
            else:
                transaction.insert(5, 'Miscellaneous')
                transaction.insert(8, 'Unclassified')
        else:
            print(transaction)
            transaction.insert(5, 'Miscellaneous')
            transaction.insert(8, 'Unclassified')

    def datalog(self):
        count = 0
        for transaction in self.all_transactions:
            count = count + 1
            data_template = {
                "user": transaction[0],
                "date": self.pass_date,
                "transaction_type": transaction[1],
                "amount": transaction[2],
                "sender_bank": transaction[4],
                "receiver_bank": transaction[3],
                "message": transaction[6] if transaction[6] not in [' ', ''] else 'No Message',
                "category": transaction[5],
                "sub_category": transaction[8] if transaction[8] not in [' ', ''] else 'NC',
                "group": '-',
                "payment_method": transaction[7],
                "data_ts": str(self.ist_time)
                # "xtra"
            }
            url = f'{self.url}/dem/api/datalog/{count}/{transaction[0]}/{str(self.pass_date)}'
            if self.post:

                status = requests.post(url, json=data_template)
                print(status.json())
            else:
                print(data_template)
        return True




def load_config():
    with open("config.toml", "rb") as f:
        return tomllib.load(f)


if __name__ == '__main__':
    # 1. Load the configuration
    config = load_config()

    # 2. Extract values into variables for easier use
    api_cfg = config['api']
    settings = config['settings']

    # 3. Use the User API from TOML
    try:
        response = requests.get(api_cfg['user_api_url'])
        response.raise_for_status()
        users = response.json()
    except Exception as e:
        print(f"Error fetching users: {e}")
        users = []

    # 4. Loop through users and process dates
    for user_data in users:
        print(f"Processing user: {user_data}")
        if settings['daily_run']:
            print("Daily Run")
            GetSpendings(
                user_data[0],
                user_data,
                date=datetime.now().strftime('%Y-%m-%d'),
                url=api_cfg['base_url'],
                post=settings['enable_data_log'],
                classifier_url=api_cfg['classifier_url']
            )

        else:
        # Use start/end day from TOML
            for i in range(settings['start_day'], settings['end_day']):
                # Format the date (e.g., 2026-02-01)
                day_str = str(i).zfill(2)
                formatted_date = f"{settings['year_month']}-{day_str}"

                # Only run if the data log flag is True

                GetSpendings(
                    user_data[0],
                    user_data,
                    date=formatted_date,
                    url=api_cfg['base_url'],
                    post=settings['enable_data_log'],
                    classifier_url=api_cfg['classifier_url']
                )


# if __name__ == '__main__':
#     USER_API = 'http://192.168.0.114:9002/dem/api/get_user_for_data_log/'
#     user_api = requests.get(USER_API)
#     print(user_api.json())
#
#     # time.sleep(100)
#
#     for user_data in user_api.json():
#         print(user_data)
#
#         for i in range(1 ,3):
#             if len(str(i)) == 1:
#                 date = '0' + str(i)
#             else:
#                 date = i
#             GetSpendings(user_data[0], user_data, date=f'GetSpendings(
#                     user_data[0],
#                     user_data,
#                     date=formatted_date,
#                     url=api_cfg['base_url'],
#                     post=settings['enable_data_log'],
#                     classifier_url=api_cfg['classifier_url']
#     # #
    # for user in user_data:
    #             GetSpendings(user, user_data[user], date= "" , post=True)


