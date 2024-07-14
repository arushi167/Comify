from pydispo import generate_email_address, check_mailbox
import io
import sys

class EmailGenerator:
    def __init__(self):
        self.email_address = None

    def create_email(self):
        self.email_address = generate_email_address(size=10)
        return self.email_address

    def get_recent_email_link(self):
        original_stdout = sys.stdout
        output_buffer = io.StringIO()
        sys.stdout = output_buffer
        check_mailbox(self.email_address, showInbox=False, showRecent=True)
        sys.stdout = original_stdout
        captured_output = output_buffer.getvalue()
        return self.extract_link_from_email(captured_output)

    def extract_link_from_email(self, email_content):
        import re
        url_pattern = r'https://stabilityai\.us\.auth0\.com/u/email-verification\?ticket=[^#]+'
        match = re.search(url_pattern, email_content)
        if match:
            return match.group(0)
        else:
            print("No link found in the email content.")
            return None

if __name__ == "__main__":
    email = EmailGenerator()
    email_address = email.create_email()

    run =  input("Want to check ?")
    recent_email_link = email.get_recent_email_link()
    if recent_email_link:
        print(f"Link from the recent email: {recent_email_link}")
    else:
        print("No recent email found or no link in the email.")
