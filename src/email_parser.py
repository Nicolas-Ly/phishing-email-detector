# This module provides functions for parsing email headers. It uses the email.parser module to parse email messages and the re module 
# to extract information from the headers.
from __future__ import annotations

from email import policy
# The email.parser module provides a Parser class which can be used to parse email messages. The BytesParser class is a subclass 
# of Parser that can be used to parse email messages from bytes.
from email.parser import BytesParser
# The email.message module provides a Message class which represents an email message. The EmailMessage class is a subclass of
#  Message that provides additional methods for working with email messages.
from pathlib import Path
# The typing module provides support for type hints. The Any type is a special type that can be used to indicate that a value can 
# be of any type.
from typing import Any
# The re module provides support for regular expressions. The re module provides a set of functions that allow you to search for 
# and manipulate strings using regular expressions.
import re

# The EmailParser class provides methods for parsing email messages and extracting information from the headers. 
# The parse_email_file method takes a file path as input and returns a dictionary containing the extracted information. The _extract_body method 
# is a helper method that extracts the body of the email message. The _extract_urls method is a helper method that extracts URLs from the email 
# body. The _clean_header method is a helper method that cleans header values and returns a safe string.
class EmailParser:
    """
    Parse .eml files and extract structured email data.

    This parser focuses on the fields most useful for phishing analysis:
    - From
    - Reply-To
    - Return-Path
    - Subject
    - Body
    - URLs
    """

    URL_PATTERN = re.compile(r"https?://[^\s<>\"]+|www\.[^\s<>\"]+")
    # The URL_PATTERN is a regular expression that matches URLs in the email body. It looks for strings that start with 
    # "http://" or "https://" or "www." and are followed by any characters that are not whitespace, angle brackets, or double quotes.
    def parse_email_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Parse an email file and return important fields as a dictionary.

        Args:
            file_path: Path to the .eml file

        Returns:
            Dictionary containing extracted email fields
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Email file not found: {path}")

        if not path.is_file():
            raise ValueError(f"Provided path is not a file: {path}")

        with path.open("rb") as email_file:
            message = BytesParser(policy=policy.default).parse(email_file)

        body = self._extract_body(message)
        urls = self._extract_urls(body)

        return {
            "from": self._clean_header(message.get("From")),
            "reply_to": self._clean_header(message.get("Reply-To")),
            "return_path": self._clean_header(message.get("Return-Path")),
            "subject": self._clean_header(message.get("Subject")),
            "body": body,
            "urls": urls,
        }

    
    # parse_email_file method takes a file path as input and returns a dictionary containing the extracted information.
    # It first checks if the file exists and is a valid file. Then it opens the file in binary mode and uses the BytesParser 
    # to parse the email message. It extracts the body of the email using the _extract_body method and then extracts URLs from the 
    # body using the _extract_urls method. Finally, it returns a dictionary containing the cleaned header values, body, and URLs.
    
    def _extract_body(self, message: Any) -> str:
        """
        Extract the plain text body from an email message.

        For multipart emails, this tries to find the first text/plain part.
        If no text/plain part exists, it falls back to text/html content.
        """
        if message.is_multipart():
            plain_parts: list[str] = []
            html_parts: list[str] = []

            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", "")).lower()

                if "attachment" in content_disposition:
                    continue

                try:
                    content = part.get_content()
                except Exception:
                    continue

                if not isinstance(content, str):
                    continue

                if content_type == "text/plain":
                    plain_parts.append(content)
                elif content_type == "text/html":
                    html_parts.append(content)

            if plain_parts:
                return "\n".join(part.strip() for part in plain_parts if part.strip())

            if html_parts:
                return "\n".join(part.strip() for part in html_parts if part.strip())

            return ""

        try:
            content = message.get_content()
            return content.strip() if isinstance(content, str) else ""
        except Exception:
            return ""

    # The _extract_body method extracts the plain text body from an email message. For multipart emails, it tries to find the first 
    # text/plain part. If no text/plain part exists, it falls back to text/html content. It returns the extracted body as a string.

    def _extract_urls(self, text: str) -> list[str]:
        """
        Extract URLs from the email body.
        """
        if not text:
            return []

        matches = self.URL_PATTERN.findall(text)

        cleaned_urls = []
        for url in matches:
            cleaned_url = url.rstrip(".,);]>\"'")
            cleaned_urls.append(cleaned_url)

        return cleaned_urls

    @staticmethod
    def _clean_header(value: str | None) -> str:
        """
        Clean header values and return a safe string.
        """
        if value is None:
            return ""

        return value.strip()


if __name__ == "__main__":
    parser = EmailParser()

    sample_path = "data/sample_emails/sample1.eml"

    try:
        parsed_email = parser.parse_email_file(sample_path)

        print("Parsed Email:")
        for key, value in parsed_email.items():
            print(f"{key}: {value}")
    except Exception as error:
        print(f"Error parsing email: {error}")