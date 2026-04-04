"""Send emails with optional PDF attachments via SMTP (async)."""

import ssl
from email.message import EmailMessage

import aiosmtplib

from config import settings


async def send_report_email(
    to_address: str,
    subject_name: str,
    report_id: str,
    pdf_bytes: bytes,
) -> None:
    """Send an investigation report PDF to *to_address*.

    Raises RuntimeError if SMTP is not configured or the send fails.
    """
    if not settings.smtp_host or not settings.smtp_username or not settings.smtp_password:
        raise RuntimeError(
            "Email is not configured. Set SMTP_HOST, SMTP_USERNAME, and "
            "SMTP_PASSWORD in your .env file."
        )

    msg = EmailMessage()
    msg["From"] = settings.smtp_from or settings.smtp_username
    msg["To"] = to_address
    msg["Subject"] = f"Investigation Report — {subject_name}"

    msg.set_content(
        f"Please find the investigation report for {subject_name} attached.\n\n"
        f"Report ID: {report_id}\n\n"
        "This report is confidential and intended solely for the attorney of record. "
        "It contains information gathered from publicly available sources only."
    )

    filename = f"report_{subject_name.replace(' ', '_').lower()}.pdf"
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=filename)

    use_tls = settings.smtp_port == 465
    context = ssl.create_default_context()

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        use_tls=use_tls,
        start_tls=not use_tls,
        tls_context=context,
    )
