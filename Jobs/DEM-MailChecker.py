import imaplib
import email
from email.message import Message  # <-- Added this import
from email.header import decode_header
from datetime import datetime
import re
from typing import Optional


# ---------------------------------------------------------------------------
# Helper Utilities
# ---------------------------------------------------------------------------
def decode_mime_header(header_val: Optional[str]) -> str:
    """Decodes MIME encoded email subjects."""
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


# Changed type hint to just 'Message'
def extract_clean_text(msg: Message) -> str:
    """Extracts plain text or strips HTML to retrieve clean email text payload."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disp = str(part.get("Content-Disposition"))
            # Prioritize plain text
            if content_type == "text/plain" and "attachment" not in content_disp:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(part.get_content_charset() or "utf-8", errors="ignore")
                    break
        # Fallback to HTML if no plain text found
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

    # Clean HTML tags, HTML entities, and structural whitespace
    body = re.sub(r"<[^>]+>", " ", body)
    body = body.replace("\xa0", " ").replace("&nbsp;", " ").replace("E282B9", "Rs").replace("&#8377;", "Rs")
    return re.sub(r"\s+", " ", body).strip()


# ---------------------------------------------------------------------------
# Main Fetcher Function
# ---------------------------------------------------------------------------
def fetch_and_print_emails(email_id: str, password: str, search_sender: str, target_date: str):
    """
    Connects to IMAP, searches for a specific sender on a specific date,
    and prints the Subject and Body.
    """
    conn = None
    try:
        # Convert YYYY-MM-DD to IMAP date format (DD-Mon-YYYY)
        date_obj = datetime.strptime(target_date, "%Y-%m-%d")
        imap_date = date_obj.strftime("%d-%b-%Y")

        print(f"[*] Logging into IMAP for {email_id}...")
        conn = imaplib.IMAP4_SSL("imap.gmail.com")
        conn.login(email_id, password)
        conn.select("Inbox")

        # Construct IMAP search query (Search by FROM and exactly ON date)
        query = f'(FROM "{search_sender}" ON {imap_date})'
        print(f"[*] Searching with query: {query}")

        result, data = conn.search(None, query)

        if result != "OK" or not data[0]:
            print("\n[-] No emails found matching the criteria.\n")
            return

        msg_ids = data[0].split()
        print(f"[*] Found {len(msg_ids)} email(s).\n")

        print("=" * 100)
        for msg_num in msg_ids:
            # Fetch the raw email data
            _, msg_data = conn.fetch(msg_num, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])

            # Extract Data
            subject = decode_mime_header(msg.get("Subject", "No Subject"))
            body = extract_clean_text(msg)

            # Print Output
            print(f"SUBJECT : {subject}")
            print("-" * 100)
            print(f"BODY    :\n{body}")
            print("=" * 100 + "\n")

    except Exception as e:
        print(f"[!] Error occurred: {e}")
    finally:
        if conn:
            try:
                conn.logout()
                print("[*] IMAP session logged out cleanly.")
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # --- CONFIGURATION ---
    EMAIL_ACCOUNT = "avinashbaswa.a4@gmail.com"
    APP_PASSWORD = "vnjc iyfw skrm mcic"  # Use Google App Password, not regular password
    # EMAIL_ACCOUNT = "baswasanjay19@gmail.com"
    # APP_PASSWORD = "mknr opta sxoy vpbl"  # Use Google App Password, not regular password

    SEARCH_MAIL = "credit_cards@icici.bank.in"  # e.g., "alerts@hdfcbank.net"
    TARGET_DATE = "2026-08-10"  # Date in YYYY-MM-DD format
    # ---------------------

    fetch_and_print_emails(
        email_id=EMAIL_ACCOUNT,
        password=APP_PASSWORD,
        search_sender=SEARCH_MAIL,
        target_date=TARGET_DATE
    )