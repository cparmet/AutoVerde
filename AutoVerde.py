## AutoVerde: Check the Verde Energy latest rate & term.
# If it's better than my contract, send myself an email.
# And log it.

# Scraping modules
import bs4 as bs
import requests

# Data manipulation
import pandas as pd
import datetime

# Sending debug emails
import sendgrid
from sendgrid.helpers.mail import *
import sys

# A function to send an email.
def sendemail(subject='AutoVerde wants a minute', body=''):
    # Store API key and email address outside the git repository.
    file_sendgrid_key = open("../sendgridkey.txt", "r")
    file_email = open("../email_address.cfg", "r")

    apikey = file_sendgrid_key.read()
    file_sendgrid_key.close()

    email_address = file_email.read()
    file_email.close()

    # using SendGrid's Python Library
    # https://github.com/sendgrid/sendgrid-python

    sg = sendgrid.SendGridAPIClient(apikey=apikey)
    from_email = Email(email_address)
    to_email = Email(email_address)
    content = Content("text/plain", body)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)

    return

## Scrape the website
url = 'https://www.verdeenergy.com/get-rates/?UtilityID=150&z=01721'
# Pretend we're a browswer, to avoid 403 errors. https://stackoverflow.com/questions/38489386/python-requests-403-forbidden
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

page = requests.get(url, headers=headers)
if page.status_code != 200:
    # Email myself that the link is broken or something on the website changed.
    sendemail(subject='AutoVerde error', body='Error from Requests: ' + str(page.status_code))
    # sys.exit(0) # While we could quit the program now, some errors are "soft errors." Let's try to continue.

soup = bs.BeautifulSoup(page.content, 'html.parser')

rates = pd.DataFrame(columns=['rate', 'term'])
rate_offers = soup.findAll("li", {"class": "rate-item"})
todays_date = datetime.date.today().strftime("%B %d, %Y")

if len(rate_offers) == 0:
    # Email myself that no rates were pulled from the website
    sendemail(subject='AutoVerde error', body='0 rates scraped' )
    sys.exit(0)  # Quit the program

for offer in rate_offers:
    rate = offer.find("h1").text
    rate = rate.split('/')[0][0:-1]
    term = offer.find('th', text='Term').find_next_sibling("td").text
    term = term.split(' ')[0]
    entry = pd.Series({'rate': rate, 'term': term})
    rates = rates.append(entry, ignore_index=True)

## Read in my rate history
rate_history = pd.read_csv('../rate_history.csv')

# Get my contracted rate
# QC: Should only be 1 row in my rate history labelled Contract?=Yes
num_yes = len(rate_history[rate_history['Contract?'] == 'Yes'])
if num_yes != 1:
    body = 'Expected 1 current rate. Found ' + num_yes + '.'
    sendemail(subject='AutoVerde error', body=body)
    sys.exit(0)  # Quit the program

contract = rate_history[rate_history['Contract?'] == 'Yes'].head(1)
contract_date, contract_rate, contract_term, _ = contract.iloc[0, :]

# Are any of the new rates better than the contracted rate?

body = ''
for i_, new_rate in rates.iterrows():
    change_rate = contract_rate - float(new_rate['rate']) # Positive means rate has gone down.
    change_term = int(new_rate.term) - int(contract_term) # Positive means term is now longer.

    if change_rate > 0 or change_term > 0:
        body += "Today's rate is " + str(new_rate.rate) + ' for ' + str(new_rate.term) + ' months. '

# If some rates were better, email them.
if body != '':
    body += 'Rate or term is better than contract, which is ' + str(contract_rate) + ' for ' + str(contract_term) + ' months.'
    sendemail(subject='We GOT ONE!', body=body)

# Update rate history.
for i_, new_rate in rates.iterrows():
    todays_entry = pd.Series({'Date': todays_date, 'Rate': new_rate.rate, 'Term': new_rate.term, 'Contract?': 'No'})
    rate_history = rate_history.append(todays_entry, ignore_index=True)

output_file_name = 'rate_history.csv'
fullpath = "%s\%s" % ("..\\", output_file_name)
rate_history.to_csv(fullpath, index=False)

# Uncomment this next bit if I want to get emails even if the rate/term isn't better.
# else:
#     sendemail(subject='No movement, master', body=body)