from __future__ import annotations

from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Any
import re


class EmailParser:
    """
    Parse .eml files and extract structured email data.

    This parser supports:
    - parsing a single .eml file
    - parsing every .eml file inside a directory
    """

    URL_PATTERN = re.compile(r"https?://[^\s<>\"]+|www\.[^\s<>\"]+")

    def parse_email_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Parse a single .eml file and return structured data.

        Args:
            file_path: Path to an email file

        Returns:
            Dictionary containing parsed fields
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
            "file_name": path.name,
            "file_path": str(path),
            "from": self._clean_header(message.get("From")),
            "reply_to": self._clean_header(message.get("Reply-To")),
            "return_path": self._clean_header(message.get("Return-Path")),
            "subject": self._clean_header(message.get("Subject")),
            "body": body,
            "urls": urls,
        }

    def parse_email_directory(self, directory_path: str | Path) -> list[dict[str, Any]]:
        """
        Parse all .eml files in a directory.

        Args:
            directory_path: Path to directory containing .eml files

        Returns:
            List of parsed email dictionaries
        """
        directory = Path(directory_path)

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Provided path is not a directory: {directory}")

        parsed_emails: list[dict[str, Any]] = []

        for email_path in sorted(directory.glob("*.eml")):
            try:
                parsed_email = self.parse_email_file(email_path)
                parsed_emails.append(parsed_email)
            except Exception as error:
                print(f"Skipping {email_path.name}: {error}")

        return parsed_emails

    def _extract_body(self, message: Any) -> str:
        """
        Extract the email body.

        For multipart emails:
        - prefer text/plain
        - fall back to text/html
        - skip attachments
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
                    plain_parts.append(content.strip())
                elif content_type == "text/html":
                    html_parts.append(content.strip())

            if plain_parts:
                return "\n".join(part for part in plain_parts if part)

            if html_parts:
                return "\n".join(part for part in html_parts if part)

            return ""

        try:
            content = message.get_content()
            return content.strip() if isinstance(content, str) else ""
        except Exception:
            return ""

    def _extract_urls(self, text: str) -> list[str]:
        """
        Extract URLs from text.
        """
        if not text:
            return []

        matches = self.URL_PATTERN.findall(text)

        cleaned_urls: list[str] = []
        for url in matches:
            cleaned_url = url.rstrip(".,);]>\"'")
            cleaned_urls.append(cleaned_url)

        return cleaned_urls

    @staticmethod
    def _clean_header(value: str | None) -> str:
        """
        Return a stripped header value or empty string.
        """
        if value is None:
            return ""
        return value.strip()


if __name__ == "__main__":
    parser = EmailParser()

    sample_directory = "data/sample_emails"

    try:
        parsed_emails = parser.parse_email_directory(sample_directory)

        print(f"Parsed {len(parsed_emails)} email(s)\n")

        for email_data in parsed_emails:
            print("=" * 60)
            print(f"File: {email_data['file_name']}")
            print(f"From: {email_data['from']}")
            print(f"Reply-To: {email_data['reply_to']}")
            print(f"Subject: {email_data['subject']}")
            print(f"URLs: {email_data['urls']}")
            print("=" * 60)
            print()

    except Exception as error:
        print(f"Error: {error}")