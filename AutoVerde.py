## AutoVerde: Check the Verde Energy latest rate & term.
# If it's better than my contract, send myself an email.
# And log it.

# Selenium modules for setting up a headless Chrome browser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select

CHROME_PATH = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'  # '/usr/bin/google-chrome'
CHROMEDRIVER_PATH = 'chromedriver.exe'
WINDOW_SIZE = "1920,1080"

# Data manipulation
import pandas as pd
import datetime

# Sending emails
import sendgrid
from sendgrid.helpers.mail import *

# A function to send an email.

def sendemail(subject='AutoVerde wants a minute', body=''):
    # Store API key outside the git repository.
    file = open("../sendgridkey.txt", "r")
    apikey = file.read()
    file.close()

    # using SendGrid's Python Library
    # https://github.com/sendgrid/sendgrid-python

    sg = sendgrid.SendGridAPIClient(apikey=apikey)
    from_email = Email("test@example.com")
    to_email = Email("crap@chadparmet.com")
    content = Content("text/plain", body)
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    print(response.status_code)
    print(response.body)
    print(response.headers)

    return


# Use Selenium to get today's rate details.
# https://stackoverflow.com/a/23447450/7414797

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
chrome_options.binary_location = CHROME_PATH

driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                          chrome_options=chrome_options)


driver.get("https://www.verdeenergy.com/Registration")

# This next line confirms that loading the website via Selenium still shows Massachusetts selected by default
# driver.get_screenshot_as_file("capture.png")


# Check: Is it still live? I found that when it timedout, the current_url will change.
if 'Registration' not in driver.current_url:
    sendemail(subject='AutoVerde error', body='Driver timeout')

# Select the dropdown box.
select = Select(driver.find_element_by_id('SelectedElectricUtilityCompany_top'))

# Activate the first option from the list
select.select_by_index(1)

# Use next line as debug to confirm select worked. It did!
# driver.get_screenshot_as_file("capture.png")


# Get the result
rate = driver.find_element_by_id('todayRate')
todays_rate = rate.text
todays_rate = float(todays_rate) * 100
term = driver.find_element_by_id('todayTerm')
todays_term = term.text
# print(todays_rate)
# print('For ' + todays_term + ' months')

# Read in the rate history
rate_history = pd.read_csv('../rate_history.csv')
todays_date = datetime.date.today().strftime("%B %d, %Y")

# QC: Should only be 1 row labelled Contract?=Yes
num_yes = len(rate_history[rate_history['Contract?'] == 'Yes'])
if num_yes != 1:
    body = 'Expected 1 current rate. Found ' + num_yes + '.'
    sendemail(subject='AutoVerde error', body=body)

contract = rate_history[rate_history['Contract?'] == 'Yes'].head(1)
contract_date, contract_rate, contract_term, _ = contract.iloc[0, :]

# Is the new rate better than contracted rate?

# Old: WHen I cared about the last rate, not my contracted rate, used this:
# last_date,last_rate,last_term=rate_history.tail(1).iloc[0,:]

change_rate = contract_rate - todays_rate # Positive means rate has gone down.
change_term = int(todays_term) - int(contract_term) # Positive means term is now longer.
body = "Today's rate is " + str(todays_rate) + ' for ' + str(todays_term) + ' months. Contract is ' + str(
    contract_rate) + ' for ' + str(contract_term) + ' months.'

if change_rate > 0 or change_term > 0:
    sendemail(subject='We GOT ONE!', body=body)

# Uncomment this next bit if I want to get emails even if the rate/term isn't better.
# else:
#     sendemail(subject='No movement, master', body=body)


# Update rate history.

todays_entry = pd.Series({'Date': todays_date, 'Rate': todays_rate, 'Term': todays_term, 'Contract?': 'No'})
rate_history = rate_history.append(todays_entry, ignore_index=True)
output_file_name = 'rate_history.csv'
fullpath = "%s\%s" % ("..\\", output_file_name)
rate_history.to_csv(fullpath, index=False)

# Feb 2018 - Changed from .close to .quit, so it will also kill chromedriver.exe process.
driver.quit()

