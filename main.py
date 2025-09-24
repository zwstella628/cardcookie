import os
import functions_framework
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

def scrape_best_discount(base_url: str) -> float:
    best_discount = 0.0
    page = 1

    while True:
        url = f"{base_url}?page-number={page}" if page > 1 else base_url
        response = requests.get(url, timeout=100)
        if response.status_code != 200:
            print("response status code: ", response.status_code)
            break

        soup = BeautifulSoup(response.text, "html.parser")
        print("response.text: ", response.text)
        discount_tags = soup.select("td.card-cell.card-discount")
        if not discount_tags:
            print("can't find discount_tags")
            break

        for tag in discount_tags:
            try:
                text = tag.get_text(strip=True).replace("%", "").replace("Off", "").strip()
                discount = float(text)
                if discount > best_discount:
                    best_discount = discount
            except ValueError:
                continue

        page += 1

    return best_discount

def send_email(subject: str, body: str):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")
    email_to = os.getenv("EMAIL_TO")

    if not all([email_user, email_pass, email_to]):
        print("Email configuration missing, skipping email")
        return

    msg = MIMEMultipart()
    msg["From"] = email_user
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.sendmail(email_user, email_to.split(","), msg.as_string())
        print("Email sent successfully")
    except Exception as e:
        print("Failed to send email:", e)

@functions_framework.http
def hello_http(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    # Read STORES env variable
    stores_env = os.getenv("STORES", "")
    stores = {}
    for item in stores_env.split(","):
        if "=" in item:
            name, url = item.split("=", 1)
            stores[name.strip()] = url.strip()

    results = {}
    for store, url in stores.items():
        print("Store: ", store)
        print("Url: ", url)
        discount = scrape_best_discount(url)
        results[store] = discount
        print(f"Best discount for {store}: {discount}%")

    
    # # Build summary text
    # summary = "\n".join([f"{store.title()}: {disc}%" for store, disc in results.items()])

    # # Send email
    # send_email("CardCookie Discount Summary", summary)


    #TODO(zhanw): add email support
    #TODO(zhanw): add sql support 
    #TODO(zhanw): add spanner support
    #TODO(zhanw): chat to show the trends


    return jsonify(results)
