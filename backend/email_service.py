import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import os

def send_email(to_email: str, subject: str, html_content: str):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.environ.get('BREVO_API_KEY')
    
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )
    
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": to_email}],
        sender={"name": "Fenora", "email": "cloudberryyohh@gmail.com"},
        subject=subject,
        html_content=html_content
    )
    
    try:
        api_instance.send_transac_email(send_smtp_email)
        return {"success": True}
    except ApiException as e:
        raise Exception(f"Brevo error: {str(e)}")