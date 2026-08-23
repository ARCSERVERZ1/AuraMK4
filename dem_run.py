import os, json, re
import time as t
import imaplib, email
from datetime import datetime, timedelta
import pytz, requests
from email.header import decode_header
# import dem_classifier as classifer

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
    def __init__(self, user, user_data, date="", url='https://engineaura.pythonanywhere.com/dem/datalogdem/',
                 post=True):
        self.all_transactions = []
        self.user = user
        self.pass_date = date
        self.user_data = user_data
        self.platforms = self.user_data['payment_method']
        self.url = url
        self.imap_url = 'imap.gmail.com'
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

        # dem_classifier.label_data(self.user ,self.pass_date ,30 )

        print(
            f"------------### Data log request for {self.user} for date {self.mail_date} ###-----------{self.ist_time}----")

        self.conn = imaplib.IMAP4_SSL('imap.gmail.com')
        email_id = self.user_data['mail_id']
        password = self.user_data['password']
        self.conn.login(email_id, password)
        self.conn.select('Inbox')

        try:
            pass
            #classifer.label_data(user, self.pass_date, 200)
        except Exception as e:
            print(f"{e}")

        self.get_all_transaction()

    def get_all_transaction(self):

        if 'phone_pe' in self.platforms: self.run_phone_pe_log()
        if 'axis_credit' in self.platforms: self.run_axis_credit_log()
        if 'hdfc_debit' in self.platforms: self.run_hdfc_debit_log()
        if 'hdfc_credit' in self.platforms: self.run_hdfc_credit_log()

        for transaction in self.all_transactions:
            self.categorise_by_labeled_data(transaction)
        self.datalog()

    def run_hdfc_credit_log(self):
        result, message = self.conn.search(None, '(FROM {0} ON {1})'.format("alerts@hdfcbank.net", self.mail_date))
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
                print(msg)
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

        result, message = self.conn.search(None, '(FROM {0} ON {1})'.format("alerts@hdfcbank.net", self.mail_date))
        transaction_msg_list = []
        for num in message[0].split():
            _, msg_data = self.conn.fetch(num, "(RFC822)")
            raw_mail = msg_data[0][1]
            msg = email.message_from_bytes(raw_mail)
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")
            if subject.find('You have done a UPI txn. Check details!') != -1 or subject.find('You have done a UPI txn. Checkdetails!') != -1:
                ref = str(msg).find('Dear')
                print(msg)
                transaction_msg = str(str(msg)[ref:ref + 329])
                transaction_msg = str(str(transaction_msg).replace("=\n", ''))
                pattern = r'Rs.(.*?)\..*?debited from account (.*?) to VPA (.*?) on'
                match = re.search(pattern, str(transaction_msg))

                if match is None:
                    print(str(transaction_msg))
                else:
                    transaction_data = match.groups()
                    self.all_transactions.append(
                        [self.user, 'sent', transaction_data[0], transaction_data[2], transaction_data[1], '',
                         'hdfc_debit', 'x01'])

    def get_categorised(self, transaction):
        print(transaction)
        pass
        try:
            AUTO_CAT = json.loads(open('auto_categorisation.json').read())
        except:
            AUTO_CAT = {"auto_category": {"Others": []}}
            print(f" auto_category json  not found in dir {os.getcwd()}")

        key_sentence = transaction[3].lower() + ' ' + transaction[5].lower()
        break_all = False
        for category in AUTO_CAT['auto_category']:
            if break_all: break
            if category == 'Others': transaction.insert(5, category)
            # special cases (debt) if message in " ['number'] " this format
            try:
                match_debt = re.search(r'\[(\d+)\]', transaction[5])
                if match_debt:
                    match_debt.group(1)
                    transaction.insert(5, 'DEBT-OUT')
                    break
            except:
                pass
            # normal search
            for keyword in AUTO_CAT['auto_category'][category]:
                match = re.search(r'\b' + re.escape(keyword.lower()) + r'\b', key_sentence, flags=re.IGNORECASE)
                if match:
                    transaction.insert(5, category)
                    break_all = True
                    break

    def categorise_by_labeled_data(self, transaction):
        file_name = self.user + '_dem_classifier.json'
        if os.path.exists(file_name):
            label_data = json.loads(open(file_name).read())

            for category, category_data in label_data.items():
                for label in category_data:
                    if label == transaction[3]:
                        print(transaction[3], "::", category)
                        transaction.insert(5, category)
                        return
            transaction.insert(5, 'Others')
        else:
            transaction.insert(5, 'Others')

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
                "sub_category": transaction[6] if transaction[6] not in [' ', ''] else 'NC',
                "group": '-',
                "payment_method": transaction[7],
                "data_ts": str(self.ist_time)
                # "xtra"
            }
            url = f'http://192.168.0.114:9001/dem/api/datalog/{count}/{transaction[0]}/{str(self.pass_date)}'
            if self.post:
                status = requests.post(url, json=data_template)
                print(status.json())
            else:
                print(data_template)
        return True


if __name__ == '__main__':
    user_data = json.loads(open('user_data.json').read())

    for user in user_data:
            for i in range(7,18):
                if len(str(i)) == 1:
                    date = '0' + str(i)
                else:
                    date = i
                GetSpendings(user, user_data[user], date=f'2026-01-{str(i)}', post=True)
    # #
    # for user in user_data:
    #             GetSpendings(user, user_data[user], date= "" , post=True)
