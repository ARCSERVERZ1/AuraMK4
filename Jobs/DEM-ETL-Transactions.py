import os
import json
import re
import sys
import logging
import imaplib
import email
import email.utils
from email.message import Message
from email.header import decode_header
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pytz
import requests

try:
    import tomllib
except ImportError:
    import tomli as tomllib

# ---------------------------------------------------------------------------
# Logging & Path Configuration
# ---------------------------------------------------------------------------
HOME = Path(__file__).resolve().parent
if str(HOME) not in sys.path:
    sys.path.insert(0, str(HOME))

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("DEM_Engine")


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
@dataclass
class Transaction:
    user: str
    trans_type: str
    amount: str
    receiver: str
    sender_bank: str
    category: str = "Miscellaneous"
    sub_category: str = "Unclassified"
    message: str = "No Message"
    payment_method: str = ""
    payment_ref: str = ""
    date_str: str = ""
    timestamp: str = ""
    status: str = "1"

    def to_api_payload(self, run_timestamp: str) -> Dict[str, Any]:
        return {
            "user": self.user,
            "date": self.date_str,
            "transaction_time": self.timestamp,
            "transaction_type": self.trans_type,
            "amount": self.amount,
            "sender_bank": self.sender_bank,
            "receiver_bank": self.receiver,
            "message": self.message if self.message.strip() else "No Message",
            "category": self.category,
            "sub_category": self.sub_category if self.sub_category.strip() else "NC",
            "group": "-",
            "payment_method": self.payment_method,
            "data_ts": run_timestamp,
            "Status": self.status,
        }


# ---------------------------------------------------------------------------
# Helper Utilities
# ---------------------------------------------------------------------------
def decode_mime_header(header_val: Optional[str]) -> str:
    if not header_val:
        return ""
    decoded_fragments = decode_header(header_val)
    text_parts = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            text_parts.append(fragment.decode(encoding or "utf-8", errors="ignore"))
        else:
            text_parts.append(str(fragment))
    return "".join(text_parts)


def extract_clean_text(msg: Message) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disp = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disp:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                    break
        if not body:
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disp = str(part.get("Content-Disposition"))
                if content_type == "text/html" and "attachment" not in content_disp:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                        break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode(msg.get_content_charset() or "utf-8", errors="ignore")

    body = re.sub(r"<[^>]+>", " ", body)
    body = body.replace("\xa0", " ").replace("&nbsp;", " ").replace("E282B9", "Rs").replace("&#8377;", "Rs")
    return re.sub(r"\s+", " ", body).strip()


def get_boolean_setting(val: Any) -> bool:
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes", "on")
    return bool(val)


def normalize_date(date_str: str, fallback_dt: datetime) -> str:
    """Normalizes various string date formats into a standard YYYY-MM-DD for the API."""
    if not date_str:
        return fallback_dt.strftime("%Y-%m-%d")

    date_str = re.sub(r'\s+', ' ', date_str.strip())
    formats = [
        "%Y-%m-%d",  # 2026-08-16
        "%d-%m-%Y",  # 16-08-2026
        "%d-%m-%y",  # 16-08-26
        "%b %d, %Y",  # Aug 10, 2026
        "%d %b %Y",  # 16 Aug 2026
        "%d-%b-%Y"  # 16-Aug-2026
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return fallback_dt.strftime("%Y-%m-%d")


def get_email_date(msg: Message, fallback_dt: datetime) -> str:
    """Safely extracts and formats the header Date of the email as fallback."""
    date_hdr = msg.get("Date")
    if date_hdr:
        try:
            dt = email.utils.parsedate_to_datetime(date_hdr).astimezone(pytz.timezone("Asia/Kolkata"))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
    return fallback_dt.strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Processing Engine
# ---------------------------------------------------------------------------
class SpendingsExtractor:
    def __init__(self, user: str, user_data: list, config: dict, http_session: requests.Session):
        self.user = user
        self.user_data = user_data
        self.email_id = user_data[1] if len(user_data) > 1 else ""
        self.password = user_data[2] if len(user_data) > 2 else ""
        self.platforms = user_data[3] if len(user_data) > 3 else []

        self.config = config
        self.api_cfg = config.get("api", {})
        self.settings = config.get("settings", {})

        self.http_session = http_session
        self.ist_time = datetime.now(pytz.timezone("Asia/Kolkata"))
        self.all_transactions: List[Transaction] = []
        self.labels_map: Dict[str, Any] = {}
        self.conn: Optional[imaplib.IMAP4_SSL] = None

    def _fetch_classification_labels(self, end_date: datetime) -> Dict[str, Any]:
        classifier_url = self.api_cfg.get("classifier_url")
        if not classifier_url:
            return {}
        past_days = int(self.settings.get("classification_past_days", 30))
        classifier_start = end_date - timedelta(days=past_days)
        params = {
            "user": self.user,
            "start_date": classifier_start.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
        try:
            response = self.http_session.get(classifier_url, params=params, timeout=15)
            response.raise_for_status()
            return response.json().get("data", response.json()) if isinstance(response.json(), dict) else {}
        except requests.RequestException:
            return {}

    def _match_category(self, receiver: str) -> Optional[Tuple[str, str]]:
        if not receiver or not self.labels_map: return None
        clean_recv = receiver.strip().lower()
        for key, val in self.labels_map.items():
            if key.strip().lower() == clean_recv:
                if val and isinstance(val, list) and len(val) > 0 and len(val[0]) >= 2:
                    return val[0][0], val[0][1]
        for key, val in self.labels_map.items():
            key_clean = key.strip().lower()
            if clean_recv in key_clean or key_clean in clean_recv:
                if val and isinstance(val, list) and len(val) > 0 and len(val[0]) >= 2:
                    return val[0][0], val[0][1]
        return None

    def run(self, start_date: datetime, end_date: datetime):
        logger.info(f"Starting processing for {self.user} | Range: {start_date.date()} to {end_date.date()}")
        self.labels_map = self._fetch_classification_labels(end_date=end_date)
        try:
            self.conn = imaplib.IMAP4_SSL("imap.gmail.com")
            self.conn.login(self.email_id, self.password)
            self.conn.select("Inbox")

            imap_since = start_date.strftime("%d-%b-%Y")
            imap_before = (end_date + timedelta(days=1)).strftime("%d-%b-%Y")

            if "phone_pe" in self.platforms: self._parse_phone_pe(imap_since, imap_before)
            if "axis_credit" in self.platforms: self._parse_axis_credit(imap_since, imap_before)
            if "hdfc_debit" in self.platforms: self._parse_hdfc_debit(imap_since, imap_before)
            if "hdfc_credit" in self.platforms: self._parse_hdfc_credit(imap_since, imap_before)
            if "icici_credit" in self.platforms: self._parse_icici_credit(imap_since, imap_before)

            self._apply_categorization()
            self._dispatch_datalog()

        except Exception as e:
            logger.error(f"Execution error: {e}")
        finally:
            if self.conn:
                try:
                    self.conn.logout()
                except:
                    pass

    # -----------------------------------------------------------------------
    # Platform Parsers
    # -----------------------------------------------------------------------
    def _fetch_messages_for_query(self, query: str) -> List[Message]:
        result, data = self.conn.search(None, query)
        if result != "OK" or not data[0]: return []
        messages = []
        for msg_num in data[0].split():
            try:
                _, msg_data = self.conn.fetch(msg_num, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                messages.append(msg)
            except:
                pass
        return messages

    def _parse_phone_pe(self, since_date: str, before_date: str):
        query = f'(FROM "noreply@phonepe.com" SINCE {since_date} BEFORE {before_date})'
        for msg in self._fetch_messages_for_query(query):
            body = extract_clean_text(msg)
            email_dt = get_email_date(msg, self.ist_time)

            pat_paid_to = r"Paid to (.*?) Rs (\d+).*?from : (.*?)Bank.*? Message :(.*?)Hi"
            match = re.search(pat_paid_to, body)
            if match:
                data = match.groups()
                self.all_transactions.append(
                    Transaction(
                        user=self.user,
                        trans_type="sent",
                        amount=data[1].replace(",", ""),
                        receiver=data[0].strip(),
                        sender_bank=data[2].strip() if len(data) > 2 else "PhonePe",
                        message=data[3].strip() if len(data) > 3 else "No Message",
                        payment_method="phone_pe",
                        date_str=email_dt,
                        timestamp=""
                    )
                )

    def _parse_axis_credit(self, since_date: str, before_date: str):
        query = f'(FROM "alerts@axis.bank.in" SINCE {since_date} BEFORE {before_date})'
        for msg in self._fetch_messages_for_query(query):
            subject = decode_mime_header(msg.get("Subject", "")).lower()
            if "spent on credit card no." not in subject:
                continue

            body = extract_clean_text(msg)
            email_dt = get_email_date(msg, self.ist_time)

            amt_m = re.search(r"Transaction Amount:\s*(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)", body, re.I)
            merch_m = re.search(r"Merchant Name:\s*(.*?)\s+Axis Bank", body, re.I)
            card_m = re.search(r"Card No\.\s*(XX\d+)", body, re.I)
            dt_m = re.search(r"Date & Time:\s*([\d-]+),\s*([\d:]+(?:\s*[A-Z]+)?)", body, re.I)

            avail_lim = re.search(r"Available Limit\*?:\s*(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)", body, re.I)
            tot_lim = re.search(r"Total Credit Limit\*?:\s*(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)", body, re.I)

            if amt_m and merch_m and card_m:
                msg_str = "No Message"
                if avail_lim and tot_lim:
                    msg_str = f"Available Limit: ₹{avail_lim.group(1)} | Total Limit: ₹{tot_lim.group(1)}"

                self.all_transactions.append(
                    Transaction(
                        user=self.user,
                        trans_type="sent",
                        amount=amt_m.group(1).replace(",", ""),
                        receiver=merch_m.group(1).strip(),
                        sender_bank=card_m.group(1),
                        message=msg_str,
                        date_str=dt_m.group(1) if dt_m else email_dt,
                        timestamp=dt_m.group(2).strip() if dt_m else "",
                        payment_method="axis_credit",
                    )
                )

    def _parse_hdfc_debit(self, since_date: str, before_date: str):
        query = f'(OR FROM "alerts@hdfcbank.net" FROM "alerts@hdfcbank.bank.in" SINCE {since_date} BEFORE {before_date})'
        for msg in self._fetch_messages_for_query(query):
            subject = decode_mime_header(msg.get("Subject", "")).lower()
            if "you have done a upi txn" in subject:
                body = extract_clean_text(msg)
                email_dt = get_email_date(msg, self.ist_time)

                main_m = re.search(
                    r"(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s+is debited from.*?account ending\s+([A-Za-z0-9]+)\s+towards VPA\s+(.*?)\s+on\s+([\d-]+)",
                    body, re.I)
                ref_m = re.search(r"UPI transaction reference no\.:\s*(\d+)", body, re.I)

                if main_m:
                    msg_str = f"UPI Ref: {ref_m.group(1)}" if ref_m else "No Message"

                    self.all_transactions.append(
                        Transaction(
                            user=self.user,
                            trans_type="sent",
                            amount=main_m.group(1).replace(",", ""),
                            sender_bank=main_m.group(2).strip(),
                            receiver=main_m.group(3).strip(),
                            date_str=main_m.group(4).strip(),
                            timestamp="",
                            message=msg_str,
                            payment_method="hdfc_debit"
                        )
                    )

    def _parse_hdfc_credit(self, since_date: str, before_date: str):
        query = f'(OR FROM "alerts@hdfcbank.net" FROM "alerts@hdfcbank.bank.in" SINCE {since_date} BEFORE {before_date})'
        for msg in self._fetch_messages_for_query(query):
            subject = decode_mime_header(msg.get("Subject", ""))
            if "Update on your HDFC Bank Credit Card" in subject:
                body = extract_clean_text(msg)
                email_dt = get_email_date(msg, self.ist_time)

                pattern = r"ending\s+(.*?)\s+for\s+(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d+)?)\s+at\s+(.*?)\s+on\s+([\d-]+)(?:\s+at\s+([\d:]+))?"
                match = re.search(pattern, body, re.IGNORECASE)

                if match:
                    account, amount, merchant, date_val = match.group(1), match.group(2), match.group(3), match.group(4)
                    time_val = match.group(5) if match.group(5) else ""
                    self.all_transactions.append(
                        Transaction(
                            user=self.user,
                            trans_type="sent",
                            amount=amount.replace(",", ""),
                            receiver=merchant.strip(),
                            sender_bank=account.strip(),
                            date_str=date_val if date_val else email_dt,
                            timestamp=time_val,
                            payment_method="hdfc_credit",
                        )
                    )

    def _parse_icici_credit(self, since_date: str, before_date: str):
        query = f'(FROM "credit_cards@icici.bank.in" SINCE {since_date} BEFORE {before_date})'
        for msg in self._fetch_messages_for_query(query):
            subject = decode_mime_header(msg.get("Subject", "")).lower()
            if "transaction alert for your icici bank credit card" not in subject:
                continue

            body = extract_clean_text(msg)
            email_dt = get_email_date(msg, self.ist_time)

            card_m = re.search(r"Card\s+(XX\d+)", body, re.I)
            amt_m = re.search(r"transaction of\s+(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)", body, re.I)
            dt_m = re.search(r"on\s+([A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s+at\s+([\d:]+)", body, re.I)
            info_m = re.search(r"Info:\s*(.*?)\.\s+The Available", body, re.I)

            avail_lim = re.search(r"Available Credit Limit.*?is\s+(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)", body, re.I)
            tot_lim = re.search(r"Total Credit Limit is\s+(?:INR|Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)", body, re.I)

            if amt_m and info_m and card_m:
                msg_str = "No Message"
                if avail_lim and tot_lim:
                    msg_str = f"Available Limit: ₹{avail_lim.group(1)} | Total Limit: ₹{tot_lim.group(1)}"

                self.all_transactions.append(
                    Transaction(
                        user=self.user,
                        trans_type="sent",
                        amount=amt_m.group(1).replace(",", ""),
                        receiver=info_m.group(1).strip(),
                        sender_bank=card_m.group(1),
                        message=msg_str,
                        date_str=dt_m.group(1) if dt_m else email_dt,
                        timestamp=dt_m.group(2).strip() if dt_m else "",
                        payment_method="icici_credit",
                    )
                )

    # -----------------------------------------------------------------------
    # Categorization & Output
    # -----------------------------------------------------------------------
    def _apply_categorization(self):
        print("\n" + "=" * 135)
        print(f" Successfully Classified Transactions for {self.user}")
        print("=" * 135)
        print(
            f"| {'Status':<10} | {'Date & Time':<20} | {'Amount':<9} | {'Receiver':<32} | {'Category':<16} | {'Sub-Category':<16} | {'Balance Limit Info':<15}")
        print("-" * 135)

        found_classified = False
        for tx in self.all_transactions:
            # Normalize the date in the main loop so it's ready for display and payload
            tx.date_str = normalize_date(tx.date_str, self.ist_time)

            matched = self._match_category(tx.receiver)

            if matched:
                tx.category, tx.sub_category = matched
                tx.status = "2"
                found_classified = True

                receiver_disp = (tx.receiver[:29] + '...') if len(tx.receiver) > 32 else tx.receiver
                cat_disp = (tx.category[:13] + '...') if len(tx.category) > 16 else tx.category
                sub_disp = (tx.sub_category[:13] + '...') if len(tx.sub_category) > 16 else tx.sub_category
                dt_disp = f"{tx.date_str} {tx.timestamp}".strip()
                msg_disp = (tx.message[:12] + '...') if len(tx.message) > 15 else tx.message

                print(
                    f"| [MATCHED]  | {dt_disp[:20]:<20} | ₹{tx.amount[:8]:<8} | {receiver_disp:<32} | {cat_disp:<16} | {sub_disp:<16} | {msg_disp:<15}")
            else:
                tx.category = "Miscellaneous"
                tx.sub_category = "Unclassified"
                tx.status = "1"

        if not found_classified:
            print(f"| {'No categorized transactions found for this period.':^131} |")
        print("=" * 135 + "\n")

    def _dispatch_datalog(self):
        post_enabled = get_boolean_setting(self.settings.get("enable_data_log", False))
        base_url = self.api_cfg.get("base_url", "").rstrip("/")

        if not self.all_transactions: return

        print("\n" + "=" * 125)
        print(f" API Log Responses for {self.user}")
        print("=" * 125)

        # Dictionary to track counts per normalized Date
        date_counters: Dict[str, int] = {}

        for tx in self.all_transactions:
            # Increment the counter for this specific date
            if tx.date_str not in date_counters:
                date_counters[tx.date_str] = 1
            else:
                date_counters[tx.date_str] += 1

            count = date_counters[tx.date_str]

            payload = tx.to_api_payload(str(self.ist_time))
            # URL formatted with the specific Date and its specific Count
            url = f"{base_url}/dem/api/datalog/{count}/{tx.user}/{tx.date_str}"

            if post_enabled:
                try:
                    res = self.http_session.post(url, json=payload, timeout=10)
                    print(f"[POST Date: {tx.date_str} | Count: {count:02d}] URL: {url}")
                    print(f"            Payload : {json.dumps(payload)}")
                    try:
                        print(f"            Response: ({res.status_code}) {json.dumps(res.json())}\n")
                    except:
                        print(f"            Response: ({res.status_code}) {res.text}\n")
                    res.raise_for_status()
                except requests.RequestException as e:
                    logger.error(f"API Data logging failed for Date {tx.date_str} (Count {count}): {e}\n")
            else:
                print(f"[DRY-RUN Date: {tx.date_str} | Count: {count:02d}] Would POST to: {url}")
                print(f"              Payload : {json.dumps(payload)}\n")
        print("=" * 125 + "\n")


# ---------------------------------------------------------------------------
# Runner Script Entrypoint
# ---------------------------------------------------------------------------
def load_config() -> dict:
    config_path = HOME / "DEM-ETL-Prod-Config.toml"
    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.critical(f"Critical error loading TOML configuration from {config_path}: {e}")
        sys.exit(1)


def main():
    config = load_config()
    api_cfg = config.get("api", {})
    settings = config.get("settings", {})

    http_session = requests.Session()

    try:
        response = http_session.get(api_cfg.get("user_api_url"), timeout=15)
        response.raise_for_status()
        users = response.json()
    except Exception as e:
        logger.critical(f"Failed to fetch configured user directory from API: {e}")
        users = []

    is_daily_run = get_boolean_setting(settings.get("daily_run", False))

    if is_daily_run:
        yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        target_start = yesterday
        target_end = yesterday
    else:
        year_month = settings.get("year_month", "2026-08")
        start_day = settings.get("start_day", 1)
        end_day = settings.get("end_day", 1)

        target_start = datetime.strptime(f"{year_month}-{str(start_day).zfill(2)}", "%Y-%m-%d")
        target_end = datetime.strptime(f"{year_month}-{str(end_day).zfill(2)}", "%Y-%m-%d")

    for user_data in users:
        if not user_data or len(user_data) < 3: continue

        extractor = SpendingsExtractor(
            user=user_data[0],
            user_data=user_data,
            config=config,
            http_session=http_session
        )
        extractor.run(start_date=target_start, end_date=target_end)


if __name__ == "__main__":
    main()