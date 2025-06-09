from __future__ import print_function
import time, os
import brevo_python
from brevo_python.rest import ApiException
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

# Configure API key authorization: api-key
configuration = brevo_python.Configuration()
configuration.api_key['api-key'] = os.getenv("EMAIL_API")

# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['partner-key'] = 'Bearer'

# create an instance of the API class
api_instance = brevo_python.AccountApi(brevo_python.ApiClient(configuration))

# Step 2: Create an instance of the API class
api_instance = brevo_python.TransactionalEmailsApi(brevo_python.ApiClient(configuration))

# Step 3: Define the email content
def send_email(code, email):
    send_smtp_email = brevo_python.SendSmtpEmail(
        to=[{"email": email, "name": "Recipient Name"}],
        sender={"email": "agridcredscore.verify@gmail.com", "name": "AgriCredScore"},
        subject="Your Verification Code",
        html_content=f"<html><body><h1>Your Verification Code</h1><p>{code}</p></body></html>"
    )

    # Step 4: Send the email
    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        pprint(api_response)
    except ApiException as e:
        print("Exception when calling TransactionalEmailsApi->send_transac_email: %s\n" % e)



