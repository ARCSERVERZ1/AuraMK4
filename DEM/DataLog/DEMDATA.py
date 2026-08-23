import os
import json
import re
import sys
import time as t
from datetime import datetime, timedelta
import imaplib
import email
from email.header import decode_header
import pytz
import requests
import tomllib  # Use 'import tomli as tomllib' if on Python < 3.11
from data_classifer import dem_classifer


def validation(text, type_str):
    if type_str == 'int':
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
    def __init__(self, user, user_data, date="", url='', classifier_url='', post=True):
        self.all_transactions = []
        self.user = user
        self.pass_date = date
        self.user_data = user_data
        self.platforms = self.user_data[3] if len(self.user_data) > 3 else []
        self.url = url
        self.imap_url = 'imap.gmail.com'
        self.classifier_url = classifier_url
        self.ist_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        self.post = post
        self.conn = None

        if self.pass_date == "":
            self.today = t.strftime('%Y-%m-%d')
            self.mail_date = datetime.strptime(self.today, '%Y-%m-%d').strftime('%d-%b-%Y')
            self.pass_date = self.today
        else:
            try:
                x = datetime.strptime(self.pass_date, '%Y-%m-%d')
                self.mail_date = x.strftime('%d-%b-%Y')
                self.pass_date = str(str(x).split(' ')[0])
            except ValueError as e:
                print(f"[ERROR] Date parsing failed for {self.pass_date}: {e}")
                return

        # Calculate dates safely
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=50)

        print(f"\n======================================================================")
        print(f"[INFO] Data log request | User: {self.user} | Target Date: {self.mail_date} | TS: {self.ist_time}")
        print(f"======================================================================")

        try:
            util = dem_classifer(
                user=user,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                base_url=self.classifier_url
            )
            util.get_data()
        except Exception as e:
            print(f"[WARNING] Classifier initialization failed for {self.user}: {e}")

        # Secure connection setup
        try:
            email_id = self.user_data[1]
            password = self.user_data[2]

            self.conn = imaplib.IMAP4_SSL(self.imap_url)
            self.conn.login(email_id, password)
            self.conn.select('Inbox')

            # Execute processing pipeline
            self.get_all_transaction()

        except imaplib.IMAP4.error as e:
            print(f"[ERROR] IMAP Auth Failed for {self.user} ({email_id}). Ensure App Password is used. Details: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected connection error for {self.user}: {e}")
        finally:
            if self.conn:
                try:
                    self.conn.logout()
                    print(f"[INFO] IMAP connection closed gracefully for {self.user}.")
                except Exception:
                    pass

    def get_all_transaction(self):
        print(f"[INFO] Active configurations/platforms: {self.platforms}")

        if 'phone_pe' in self.platforms: self.run_phone_pe_log()
        if 'axis_credit' in self.platforms: self.run_axis_credit_log()
        if 'hdfc_debit' in self.platforms: self.run_hdfc_debit_log()
        if 'hdfc_credit' in self.platforms: self.run_hdfc_credit_log()

        print(f"[INFO] Found {len(self.all_transactions)} total raw transactions. Categorizing...")
        for transaction in self.all_transactions:
            self.categorise_by_labeled_data(transaction)

        self.datalog()

    def run_hdfc_credit_log(self):
        try:
            result, message = self.conn.search(
                None,
                '(OR FROM "alerts@hdfcbank.net" FROM "alerts@hdfcbank.bank.in" ON {0})'.format(self.mail_date)
            )
            if result != 'OK' or not message[0]: return

            for num in message[0].split():
                try:
                    _, msg_data = self.conn.fetch(num, "(RFC822)")
                    raw_mail = msg_data[0][1]
                    msg = email.message_from_bytes(raw_mail)
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")

                    if 'Update on your HDFC Bank Credit Card' in subject:
                        msg_str = str(msg)
                        message_body = msg_str[msg_str.find('Dear'): msg_str.find('Regards')]
                        pattern = 'ending (.*?) for Rs (.*?) at (.*?) on'
                        match = re.search(pattern, message_body)

                        if match is None:
                            print(f"[DEBUG] [HDFC_CREDIT] Unmatched layout structure: {msg_str[:200]}...")
                        else:
                            send_from = match.groups(1)[0]
                            amount = match.groups(1)[1].split('.')[0]
                            send_to = match.groups(1)[2]

                            self.all_transactions.append(
                                [self.user, 'sent', amount, send_to, send_from, '', 'hdfc_credit', 'x01']
                            )
                            print(f"[SUCCESS] [HDFC_CREDIT] Parsed: Rs.{amount} to {send_to}")
                except Exception as e:
                    print(f"[ERROR] Processing individual HDFC Credit Email failed: {e}")
        except Exception as e:
            print(f"[ERROR] Search failed in run_hdfc_credit_log: {e}")

    def run_phone_pe_log(self):
        try:
            result, data = self.conn.search(None, '(FROM {0} ON {1})'.format("noreply@phonepe.com", self.mail_date))
            if result != 'OK' or not data[0]: return

            for Tmails, i in enumerate(data[0].split()):
                try:
                    typ, data_fetch = self.conn.fetch(i, '(RFC822)')
                    email_message = {
                        part.get_content_type(): part.get_payload()
                        for part in email.message_from_bytes((data_fetch[0][1])).walk()
                    }

                    for content_type in email_message:
                        if content_type == 'text/html':
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
                                    print(f"[DEBUG] [PHONE_PE] Unmatched string layout.")
                            else:
                                transaction_data = final_match.groups()
                                self.all_transactions.append(
                                    [self.user, 'sent', transaction_data[1], transaction_data[0], transaction_data[2],
                                     transaction_data[3], 'phone_pe', 'anamoaly']
                                )
                                print(f"[SUCCESS] [PHONE_PE] Parsed: Rs.{transaction_data[1]} to {transaction_data[0]}")
                except Exception as e:
                    print(f"[ERROR] Processing individual PhonePe Email failed: {e}")
        except Exception as e:
            print(f"[ERROR] Search failed in run_phone_pe_log: {e}")

    def run_axis_credit_log(self):
        try:
            result, message = self.conn.search(None, '(FROM {0} ON {1})'.format("alerts@axisbank.com", self.mail_date))
            if result != 'OK' or not message[0]: return

            for num in message[0].split():
                try:
                    _, msg_data = self.conn.fetch(num, "(RFC822)")
                    raw_mail = msg_data[0][1]
                    msg = email.message_from_bytes(raw_mail)
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")

                    if 'Transaction alert on Axis Bank Credit Card no' in subject:
                        ref = str(msg).find('Dear')
                        if ref == -1: continue
                        transaction_msg = str(str(msg)[ref:ref + 329]).replace("=\n", '')

                        pattern = r'card no. (\w+)[^INR]+INR (\d+) at (\w+)'
                        match = re.search(pattern, str(transaction_msg))

                        if match is None:
                            pattern = 'declined due to (.*?)\.'
                            match = re.search(pattern, str(transaction_msg))
                            if match is not None:
                                print(f"[WARNING] [AXIS_CREDIT] Card Decline Detected: {transaction_msg[:100]}")
                            else:
                                print(f"[DEBUG] [AXIS_CREDIT] Card decline reason or transaction layout unknown")
                        else:
                            transaction_data = match.groups()
                            self.all_transactions.append(
                                [self.user, 'sent', transaction_data[1], transaction_data[2], transaction_data[0], '',
                                 'axis_credit', 'x01']
                            )
                            print(f"[SUCCESS] [AXIS_CREDIT] Parsed: INR {transaction_data[1]} at {transaction_data[2]}")
                except Exception as e:
                    print(f"[ERROR] Processing individual Axis Credit Email failed: {e}")
        except Exception as e:
            print(f"[ERROR] Search failed in run_axis_credit_log: {e}")

    def run_hdfc_debit_log(self):
        try:
            result, message = self.conn.search(
                None,
                '(OR FROM "alerts@hdfcbank.net" FROM "alerts@hdfcbank.bank.in" ON {0})'.format(self.mail_date)
            )
            if result != 'OK' or not message[0]: return

            for num in message[0].split():
                try:
                    _, msg_data = self.conn.fetch(num, "(RFC822)")
                    raw_mail = msg_data[0][1]
                    msg = email.message_from_bytes(raw_mail)
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")

                    if 'You have done a UPI txn. Check details!' in subject or 'You have done a UPI txn. Checkdetails!' in subject:
                        ref = str(msg).find('Dear')
                        if ref == -1: continue
                        transaction_msg = str(str(msg)[ref:ref + 329]).replace("=\n", '')
                        # pattern = r'Rs.(.*?)\..*?debited from account (.*?) to VPA (.*?) on'
                        pattern = r'Rs\.(.*?)\s+is debited from your account ending\s+(.*?)\s+towards VPA\s+(.*?)\s+on'
                        match = re.search(pattern, str(transaction_msg))

                        if match is None:
                            print(f"[DEBUG] [HDFC_DEBIT] Unmatched UPI sequence layout.")
                        else:
                            transaction_data = match.groups()
                            self.all_transactions.append(
                                [self.user, 'sent', transaction_data[0], transaction_data[2], transaction_data[1], '',
                                 'hdfc_debit', 'x01']
                            )
                            print(
                                f"[SUCCESS] [HDFC_DEBIT] Parsed UPI: Rs.{transaction_data[0]} to {transaction_data[2]}")
                except Exception as e:
                    print(f"[ERROR] Processing individual HDFC Debit Email failed: {e}")
        except Exception as e:
            print(f"[ERROR] Search failed in run_hdfc_debit_log: {e}")

    def categorise_by_labeled_data(self, transaction):
        file_name = f'classification_data_{self.user}.json'
        if os.path.exists(file_name):
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    label_data = json.loads(f.read())

                sender = transaction[3]
                if sender in label_data.get('data', {}).keys():
                    cat = label_data['data'][sender][0][0]
                    sub_cat = label_data['data'][sender][0][1]
                    print(f"[INFO] Mapping: {sender} -> Balanced to Category: {cat} | Sub-Category: {sub_cat}")
                    transaction.insert(5, cat)
                    transaction.insert(8, sub_cat)
                else:
                    transaction.insert(5, 'Miscellaneous')
                    transaction.insert(8, 'Unclassified')
            except Exception as e:
                print(f"[ERROR] Failed reading/parsing classification file {file_name}: {e}")
                transaction.insert(5, 'Miscellaneous')
                transaction.insert(8, 'Unclassified')
        else:
            transaction.insert(5, 'Miscellaneous')
            transaction.insert(8, 'Unclassified')

    def datalog(self):
        count = 0
        for transaction in self.all_transactions:
            count += 1
            try:
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
                }
                url = f'{self.url}/dem/api/datalog/{count}/{transaction[0]}/{str(self.pass_date)}'

                if self.post:
                    status = requests.post(url, json=data_template, timeout=10)
                    print(f"[POST SUCCESS] Index {count} API Response: {status.json()}")
                else:
                    print(f"[DRY-RUN LOG] Template index {count}: {data_template}")
            except requests.RequestException as e:
                print(f"[ERROR] API Data logging failed at tracking index {count}: {e}")
            except Exception as e:
                print(f"[ERROR] Processing internal datalog object structure layout failed: {e}")
        return True


def load_config():
    try:
        with open("config.toml", "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"[CRITICAL] Critical error loading config.toml setup file: {e}")
        sys.exit(1)


if __name__ == '__main__':
    config = load_config()

    api_cfg = config.get('api', {})
    settings = config.get('settings', {})

    try:
        response = requests.get(api_cfg.get('user_api_url'), timeout=15)
        response.raise_for_status()
        users = response.json()
    except Exception as e:
        print(f"[CRITICAL] Error fetching master user system array configurations: {e}")
        users = []

    for user_data in users:
        if not user_data or len(user_data) < 3:
            print(f"[WARNING] Skipping poorly formatted dataset parameters: {user_data}")
            continue

        if settings.get('daily_run', False):
            GetSpendings(
                user_data[0],
                user_data,
                date=datetime.now().strftime('%Y-%m-%d'),
                url=api_cfg.get('base_url', ''),
                post=settings.get('enable_data_log', False),
                classifier_url=api_cfg.get('classifier_url', '')
            )
        else:
            start_day = settings.get('start_day', 1)
            end_day = settings.get('end_day', 2)
            year_month = settings.get('year_month', '2026-01')

            for i in range(start_day, end_day):
                day_str = str(i).zfill(2)
                formatted_date = f"{year_month}-{day_str}"

                GetSpendings(
                    user_data[0],
                    user_data,
                    date=formatted_date,
                    url=api_cfg.get('base_url', ''),
                    post=settings.get('enable_data_log', False),
                    classifier_url=api_cfg.get('classifier_url', '')
                )