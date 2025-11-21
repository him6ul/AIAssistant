"""
IMAP email ingestion for Gmail and other IMAP servers.
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional
from app.tasks.storage import get_task_storage
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailIMAPIngestor:
    """
    Ingests emails via IMAP protocol.
    """
    
    def __init__(
        self,
        server: str,
        port: int,
        username: str,
        password: str,
        use_ssl: bool = True,
        action_keywords: List[str] = None
    ):
        """
        Initialize IMAP email ingestor.
        
        Args:
            server: IMAP server address
            port: IMAP server port
            username: Email username
            password: Email password or app password
            use_ssl: Use SSL/TLS
            action_keywords: Keywords that indicate actionable emails
        """
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.action_keywords = action_keywords or [
            "follow up", "due", "please check", "action required", "todo", "task"
        ]
        self.storage = get_task_storage()
        self._processed_emails: set = set()
    
    def _connect(self) -> Optional[imaplib.IMAP4_SSL]:
        """
        Connect to IMAP server.
        
        Returns:
            IMAP connection or None if failed
        """
        try:
            if self.use_ssl:
                mail = imaplib.IMAP4_SSL(self.server, self.port)
            else:
                mail = imaplib.IMAP4(self.server, self.port)
            
            mail.login(self.username, self.password)
            logger.info(f"Connected to IMAP server: {self.server}")
            return mail
        except Exception as e:
            logger.error(f"Failed to connect to IMAP server: {e}")
            return None
    
    def _decode_header(self, header: bytes) -> str:
        """
        Decode email header.
        
        Args:
            header: Header bytes
        
        Returns:
            Decoded string
        """
        decoded_parts = decode_header(header)
        decoded_string = ""
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding)
                else:
                    decoded_string += part.decode()
            else:
                decoded_string += part
        return decoded_string
    
    def _extract_text_from_email(self, msg: email.message.Message) -> str:
        """
        Extract plain text from email message.
        
        Args:
            msg: Email message object
        
        Returns:
            Plain text content
        """
        text = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        try:
                            text += payload.decode('utf-8', errors='ignore')
                        except:
                            text += str(payload)
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                try:
                    text = payload.decode('utf-8', errors='ignore')
                except:
                    text = str(payload)
        
        return text
    
    def _contains_action_keywords(self, subject: str, body: str) -> bool:
        """
        Check if email contains action keywords.
        
        Args:
            subject: Email subject
            body: Email body
        
        Returns:
            True if contains action keywords
        """
        text = f"{subject} {body}".lower()
        return any(keyword.lower() in text for keyword in self.action_keywords)
    
    async def ingest_unread(self, max_emails: int = 50) -> List[Dict[str, Any]]:
        """
        Ingest unread emails.
        
        Args:
            max_emails: Maximum number of emails to ingest
        
        Returns:
            List of ingested email data
        """
        logger.info("Starting IMAP unread email ingestion")
        
        mail = self._connect()
        if not mail:
            return []
        
        ingested_emails = []
        
        try:
            mail.select("INBOX")
            status, messages = mail.search(None, "UNSEEN")
            
            if status != "OK":
                logger.error("Failed to search for unread emails")
                return []
            
            email_ids = messages[0].split()
            email_ids = email_ids[:max_emails]  # Limit results
            
            for email_id in email_ids:
                try:
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        continue
                    
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)
                    
                    message_id = email_id.decode()
                    
                    if message_id in self._processed_emails:
                        continue
                    
                    subject = self._decode_header(msg["Subject"] or "")
                    from_addr = self._decode_header(msg["From"] or "")
                    body_text = self._extract_text_from_email(msg)
                    
                    # Check for action keywords
                    if self._contains_action_keywords(subject, body_text):
                        ingested_emails.append({
                            "id": message_id,
                            "subject": subject,
                            "body": body_text,
                            "from": from_addr,
                            "received": msg["Date"],
                            "importance": "normal",
                            "is_read": False
                        })
                        
                        self._processed_emails.add(message_id)
                        
                        # Log ingestion
                        await self.storage.log_ingestion(
                            source_type="email",
                            source_id=message_id,
                            status="success"
                        )
                
                except Exception as e:
                    logger.error(f"Failed to process email {email_id}: {e}")
                    continue
            
            mail.close()
            mail.logout()
            
            logger.info(f"Ingested {len(ingested_emails)} unread emails via IMAP")
            return ingested_emails
        
        except Exception as e:
            logger.error(f"IMAP ingestion failed: {e}")
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except:
                    pass
            return ingested_emails

