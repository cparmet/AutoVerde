I like my electricity supplier. If the price of electricity goes down, you can update your contract to get the better rate. This is nice. But to see if the rate has gone down, you need to visit a website. That's boring. 

This Python script automates the activity by scraping the website for the latest electricity rate and emailing me if the rate is better than my contracted rate. I schedule this script to run daily.

Aug 2018: The electricity website changed and there's no more form to fill out to get the rate. That simplifies the script, which no longer needs Selenium and a headless Chrome browser to automate filling out the form.