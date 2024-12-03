# This library is intended to be used for the Nerus Strategies vetting process. The following functions cover every process.

# Import the necessary libraries needed for all of the functions
#---------------------------------------------------------------------------------------------------------------------------------------------------
import time
from selenium import webdriver # Will need to install Selenium
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import requests 
import bs4 # Will need to install
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import urllib.request
from bs4 import BeautifulSoup 
from bs4 import ParserRejectedMarkup
import pandas as pd
import json
import re
import datetime
from urllib.parse import urljoin 
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
import prompts
import ollama # Will need to install
from urllib.parse import urlparse
#---------------------------------------------------------------------------------------------------------------------------------------------------

# Create the instance of the prompts needed for the llama3 text analyses. It includes all subcategories and is updated if they are not included.
#---------------------------------------------------------------------------------------------------------------------------------------------------
prompts = prompts.prompts()
#---------------------------------------------------------------------------------------------------------------------------------------------------

# google_date_check is used to check if the date retrieved from the google function is within the one year or less limit.
#---------------------------------------------------------------------------------------------------------------------------------------------------
def google_date_check(date):
    # If "years" is in the date, we can assume that it is over one year and that is the key indicator for our use cases.
    if "years" in date:  
        return 'Inactive'
    else:
        return 'Active'
#---------------------------------------------------------------------------------------------------------------------------------------------------

# The url_ok function takes in a url and checks if it is a valid url that does not return an error status, for example a 404 error 
# would return False. This function is used in the google function to validate that the website the company has listed on their google is valid.
#---------------------------------------------------------------------------------------------------------------------------------------------------
def url_ok(url):
    # Use an exception block just in case there are any unforseen errors that occur.
    try:
        # Create a header that is less prone to be detected as bot and raise less errors and a timeout because some websites take too long to load
        # and it is important to be time efficient.
        response = requests.head(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"},timeout=120)
         
        # check the status code for any errors from the url
        if response.status_code == 200 or response.status_code == 200 or response.status_code == 301 or response.status_code == 403 and 'facebook' not in url:
            return True
        else:
            return False
    except (requests.ConnectionError,requests.exceptions.Timeout,requests.exceptions.SSLError ) as e:
        print(e)
        return False
#---------------------------------------------------------------------------------------------------------------------------------------------------

# The google function is used to verify their information via their google business account, this includes checking that the name matches, checking
# if it has a valid website listed, and if the date of the last review is within the year range that is a requirement. It takes in the search term
# to look up on google to find the business, the name of the business, and a count of how many times it has had to run due to errors.
#---------------------------------------------------------------------------------------------------------------------------------------------------
def google(search_term, name, count=0):
    
    # initializing the parameters for the webdriver
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maxamized')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    
    # Start Webdriver
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    driver = webdriver.Chrome(options=chrome_options)
    #-----------------------------------------------------------------------------------------------------------------------------------------------

    #Initial url to go to
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    url = "https://google.com"
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    #Create an instant to be later in the process so it has a global reach across the whole function
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    elems = []
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    
    # Opening the website with an exception block to try any errors from slow loading times
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    try:
        driver.get(url)
    except WebDriverException:
        time.sleep(10)
        driver.get(url)
    #-----------------------------------------------------------------------------------------------------------------------------------------------

    
    # All of the find_element(s) functions are a part of the Selenium library and are used to find elements within the webpage that is currently
    # open. All instances of time.sleep are there to allow for time to let websites load.

    

    # type in the search_term to look up the business and it hit return to search it up
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    time.sleep(2)
    search = driver.find_element(By.CLASS_NAME,"gLFyf")
    search.send_keys(search_term)
    search.send_keys(Keys.RETURN)
    time.sleep(2)
    website = False
    #-----------------------------------------------------------------------------------------------------------------------------------------------


    # This section finds the name of the business as listed on their google account and checks if the names match as listed on Optimum. If the 
    # name does not match, it returns there and the function halts to a stop. 
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    try:
        gname = driver.find_element(By.CLASS_NAME,"DoxwDb")

        if "-" in name and ',' not in name:
            person_name = name.split('-')[0][:-1]
            agency = name.split('-')[1][1:]
            
            if person_name.lower() not in gname.text.lower() and agency.lower() not in gname.text.lower():
                driver.quit()
                return "Name Does Not Match"
                
            elif person_name.lower() in gname.text.lower() and agency.lower() not in gname.text.lower():
                driver.quit()
                return "Possible Agency change"

        elif "-" in name and ',' in name:
            name = name[:name.index(',')]
            if name.lower() not in gname.text.lower():
                driver.quit()
                return "Name Does Not Match"
            
        elif name.lower() not in gname.text.lower():
            driver.quit()
            return "Name Does Not Match"
            
    except NoSuchElementException:
        x=10
    #-----------------------------------------------------------------------------------------------------------------------------------------------

    # This section checks if the business shows up as "Permanently Closed" and stops there if it is and returns so
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    try:
        closed = driver.find_element(By.CLASS_NAME,"b4cFMb")
        if closed.is_displayed():
            driver.quit()
            return "Permanently Closed"
    except NoSuchElementException:
        x=10
    #-----------------------------------------------------------------------------------------------------------------------------------------------

    website = False # initialize with the assumption that there is no website and change it to True if one that is valid is found

    # This section checks for a website associated with the business and makes sure it is a valid website using the url_ok() function.
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    try:
       links = driver.find_elements(By.XPATH, "//a[@href]")
       for link in links:
            if "Website" in link.get_attribute("innerHTML"): # The one we want will have "Website" in the text of the button for the business
                url = link.get_attribute("href")
                if url_ok(url):
                    website = True
                else:
                    if "http" in url and "https" not in url:
                        url = url.replace("http", "https")
                        if url_ok(url):
                            website = True
                        else:
                            website = False
                    else:
                        website = False
                break
                            
    except TimeoutException:
        x=10
    #-----------------------------------------------------------------------------------------------------------------------------------------------
        
    # The following section has multiple parts to it, but the whole thing is what takes care of finding the date of the most recent google review.
    # It uses the google_date_check() function to check the date meets the requirement.
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    try :
        # finds the "Reviews" button and clicks in it
        elem = driver.find_element(By.CLASS_NAME,"hqzQac")
        if elem.is_displayed():
            time.sleep(1)
            elem.click()
            time.sleep(2)
            try:
                try:
                    # Click on the "Newest" button to make sure the top review is the most recent
                    new = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Newest']")))
                    ac = ActionChains(driver)
                    ac.move_to_element(new).move_by_offset(1, 1).click().perform()
                    time.sleep(2)
                    elems = driver.find_elements(By.CLASS_NAME,"jxjCjc") # Picks out the reviews and puts their contents in a list
                except TimeoutException:
                    # This exception is to take into account the different format for review pages for places like hotels
                    try:
                        newer = driver.find_elements(By.CLASS_NAME,"aAs4ib")
                        status = "Inactive"
                        for n in newer:
                          
                            if google_date_check(n.text.split("\n")[1]) == "Active" and website:
                                status = "Active"
                                
                        driver.quit()
                        return status
                    except TimeoutException:
                        driver.quit()
                        return "Error"

                
            except ElementClickInterceptedException: # If there is an error it tries to redo the process up to 2 more times.
                count+=1
                if count <2:
                    driver.quit()
                    return google(search_term,count=count)
                else:
                    driver.quit()
                    return 'No Reviews Available Or Multiple Locations'     
        # the following picks out the first review and gets the date from it if it was able to get the reviews.           
        if len(elems) > 0:
            r=""
            for t in elems:
                if t.text != "":
                    r = t.text
                    break
                
            if len(r.split('\n')) >2:
                date = r.split('\n')[2]
            elif len(r.split('\n')) == 2:
                date = r.split('\n')[1]
    
            else:
                driver.close()
                return google(search_term,name) # sometimes an error occurs when loading the reviews so it tries again
        else:
            return 'Error'
    except NoSuchElementException :
        driver.quit()
        return 'No Reviews Available Or Multiple Locations'
    #-----------------------------------------------------------------------------------------------------------------------------------------------

    # By now the date should be set and we check to make sure that the date and website are valid.
    #-----------------------------------------------------------------------------------------------------------------------------------------------
    # It now goes through the logic of approving based off of wether or not it has a website and a recent enough review, if it does, then it
    # returns as 'Active'. Otherwise it returns something else. Keep in mind it can return not active if the review is not recent enough earlier
    # in the code for some cases. It also accounts for schools which usually don't have recent reviews, so they get a pass as long as they have
    # an active website listed.
    if google_date_check(date) == 'Active' and website:
        driver.quit()
        return 'Active'
        
    elif date == 'NEW' and website:
        driver.quit()
        return 'Active'

    elif "school" in name.lower() and website:
        driver.quit()
        return "Active"
        
    elif not website:
        driver.quit()
        return 'No Website or Website is Facebook'
    else:
        driver.quit()
        return 'Got Lost'

    #-----------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------  


# This function is used to append new data to either the approved or skipped files where it keeps track of how nominees are categorized
#--------------------------------------------------------------------------------------------------------------------------------------------------
def add_data_to_csv(csv_filename, data_array):
    """Adds data points from an array to their respective columns in a CSV.

    Args:
        csv_filename (str): The name of the CSV file.
        data_array (list): An array containing 4 data points in the order:
            Company, Subcategory, Result, Reasoning.
    """

    with open(csv_filename, 'a', newline='') as csvfile:  # Open in append mode
        fieldnames = ["Company", "Subcategory", "Result", "Reasoning"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # If the file is empty, write the header row first
        if csvfile.tell() == 0:
            writer.writeheader()

        # Create a dictionary mapping data points to column names
        data_dict = {
            "Company": data_array[0],
            "Subcategory": data_array[1],
            "Result": data_array[2],
            "Reasoning": data_array[3]
        }
        
        # Write the data as a new row
        writer.writerow(data_dict)
#--------------------------------------------------------------------------------------------------------------------------------------------------

# This function is a backup for the the sub() function. There are cases where using the function get from requests does not work to scrape text 
# from websites because it gets detected as a bot. When this happens we can implement the selenium webdriver which is able to access most 
#websites and we can then pull the text for the analyses that is needed. 
#--------------------------------------------------------------------------------------------------------------------------------------------------
def selenium_text(url):
    # Initialize the Webdriver
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--start-maxamized')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=chrome_options)
                             
    # Set a timeout, some urls take too long to load or do not work and the program can get stuck on them otherwise
    driver.set_page_load_timeout(15)

    # Go to the URL
    driver.get(url)
    time.sleep(2)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                              
    # Scrape the text
    text = driver.find_element(By.XPATH, "/html/body").text
     
    # Closing the driver and return the text
    driver.quit()
    return text

# This function is how we interact with the Meta's open source LLM model llama3. Switch to llama3.1 when running on the cloud for better accuracy.
# It takes in the prompt for the text analyses that is adjusted within the sub function to include the text we scrape from the website and put
# that into the predefined prompt for the subcategory that is being verified.
#--------------------------------------------------------------------------------------------------------------------------------------------------
def detect(text):
    response = ollama.chat(model='llama3',  messages=[
      {
        'role': 'user',
        'content': text,
      },
    ])
    return response['message']['content'] # returns the response with a yes or no within it so we know if it is approved or not

#--------------------------------------------------------------------------------------------------------------------------------------------------

# This functionis used to check a company's website and scrapes the text from it. Then it feeds the text into a prompt that is preset and is then  # input into llama3(llama3.1 for cloud launch because it uses a better GPU which can handle more requests). Llama then decides wether or not the 
#  company qualifies for the subcategory based off of the website text. It checks 25 websites within the domain of the original website.
#--------------------------------------------------------------------------------------------------------------------------------------------------
def sub(name,base_url, sub):
    driver_started = False
    text_content = ''
    s_content = ''
    count = 0
    if 'facebook' not in base_url.lower() and '..' not in base_url.lower(): # Checks to make sure it is not a facebook link and
                                                                            #that the format is correct
        visited_urls = set()
        urls_to_visit = [base_url]
    
        while len(visited_urls)<16 and len(urls_to_visit)!=0 and count<16:      # change back to 25 for the cloud 
            url = urls_to_visit.pop(0)
            visited_urls.add(url)
    
            try:
                s_text = selenium_text(url)
                if sub in prompts:
                    prompt = prompts[sub].split('subtexthere')
                    prompt.append(s_text)
                    result = detect(prompt[0]+prompt[2]+prompt[1])
                    count+=1
                else:
                    print(sub+ ' not in list yet')
                    if driver_started:
                        driver.quit()
                    return(sub)
                    
            except WebDriverException:
                if driver_started:
                        driver.quit()
                return 'url error'
    
            # Check if "yes" is in the text content
            if 'yes' in result.lower():
                print("Approved")
                if driver_started:
                        driver.quit()
                return "Approved"
            

            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--start-maxamized')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            driver = webdriver.Chrome(options=chrome_options)
            driver_started = True
            driver.get(base_url)

            
            # Find links within the same domain
            links = driver.find_elements(By.TAG_NAME, 'a') 
            

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href:
                      link_url = urljoin(base_url, href)
                      if urlparse(link_url).netloc == urlparse(base_url).netloc and link_url not in visited_urls:
                        urls_to_visit.append(link_url)
                        visited_urls.add(link_url)
                except (StaleElementReferenceException,WebDriverException) as e:
                    print(e)
                    visited_urls.add(link)
                    

            if count == 8:
                print("break")
                time.sleep(20)

            
                
        driver.quit()
        return 'Error'  # "yes" not found in the domain
    else:
        if driver_started:
                        driver.quit()
        return 'Website listed is a Facebook account or error with link'


def get_contest_ID(contest_name):
    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")
    option.add_argument('--headless')
    
    
    # Email and Password for accessing Facebook
    # Login Credentials
    EMAIL = 'brodriguez@nerus.net'
    PASSWORD = 'Fuck@1234'
    # Open chrome browser
    browser = webdriver.Chrome(options=option)
    # Open Optimum
    browser.get("https://www.optimumbynerus.net/login")
    browser.maximize_window()
    wait = WebDriverWait(browser, 30)
    wait
    # Log into Optimum
    email_field = wait.until(EC.visibility_of_element_located((By.NAME, 'email')))
    email_field.send_keys(EMAIL)
    wait
    pass_field = wait.until(EC.visibility_of_element_located((By.NAME, 'password')))
    pass_field.send_keys(PASSWORD)
    wait
    pass_field.send_keys(Keys.RETURN)
    # Search for desired contest
    contest_field = wait.until(EC.visibility_of_element_located((By.NAME, 'searchText')))
    contest_field.send_keys(contest_name)
    contest_field.send_keys(Keys.RETURN)
    wait
    
    
    # Click on "View Nominees button to go to the contest list of nominees"
    try:
        v = WebDriverWait(browser, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='View Nominees']"))).click()
    except StaleElementReferenceException :
        # Sometimes it takes some time to load so this just makes sure it catches this
        time.sleep(2)
        v = WebDriverWait(browser, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='View Nominees']"))).click()
    time.sleep(4)

    ID = browser.current_url.split('contestId=')[1]
    browser.quit()

    
    return ID

def get_contest_max_page_number(contest_name):
    option = Options()
    option.add_argument("--disable-infobars")
    option.add_argument("start-maximized")
    option.add_argument("--disable-extensions")
    option.add_argument('--headless')
    
    
    # Email and Password for accessing Facebook
    # Login Credentials
    EMAIL = 'brodriguez@nerus.net'
    PASSWORD = 'Fuck@1234'
    # Open chrome browser
    browser = webdriver.Chrome(options=option)
    # Open Optimum
    browser.get("https://www.optimumbynerus.net/login")
    browser.maximize_window()
    wait = WebDriverWait(browser, 30)
    wait
    # Log into Optimum
    email_field = wait.until(EC.visibility_of_element_located((By.NAME, 'email')))
    email_field.send_keys(EMAIL)
    wait
    pass_field = wait.until(EC.visibility_of_element_located((By.NAME, 'password')))
    pass_field.send_keys(PASSWORD)
    wait
    pass_field.send_keys(Keys.RETURN)
    # Search for desired contest
    contest_field = wait.until(EC.visibility_of_element_located((By.NAME, 'searchText')))
    contest_field.send_keys(contest_name)
    contest_field.send_keys(Keys.RETURN)
    wait
    
    
    # Click on "View Nominees button to go to the contest list of nominees"
    try:
        v = WebDriverWait(browser, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='View Nominees']"))).click()
    except StaleElementReferenceException :
        # Sometimes it takes some time to load so this just makes sure it catches this
        time.sleep(2)
        v = WebDriverWait(browser, 30).until(EC.element_to_be_clickable((By.XPATH, "//span[text()='View Nominees']"))).click()
    time.sleep(4)
    try:
        next = browser.find_element(By.XPATH,"//jhi-nominee//jhi-pagination//ul/li[7]")
    except NoSuchElementException:
        browser.quit()
        return get_contest_max_page_number(contest_name)
        
    max = next.text    
    browser.quit()
    return max

def append_to_approved_file(file_name, data_to_append):
    """
    Appends data to a CSV file with the column "Approved".
    If the file doesn't exist, creates it with the column and initial data.

    Args:
        file_name (str): Name of the CSV file.
        data_to_append: Data to append to the "Approved" column. Can be a single value or a list.
    """

    try:
        # Attempt to read existing file
        df = pd.read_csv(file_name)

        # Check if the "Approved" column exists
        if "Approved" not in df.columns:
            df["Approved"] = pd.Series(dtype='object')  # Create the column if it doesn't exist
    except FileNotFoundError:
        # If file doesn't exist, create a new DataFrame with the column
        df = pd.DataFrame({"Approved": []})

    # Ensure data_to_append is a list for consistent handling
    if not isinstance(data_to_append, list):
        data_to_append = [data_to_append]

    # Append the new data (using concat)
    new_data_df = pd.DataFrame({"Approved": data_to_append})
    df = pd.concat([df, new_data_df], ignore_index=True)

    # Save the updated DataFrame to the CSV file
    df.to_csv(file_name, index=False)

def append_to_skipped_file(file_name, data_to_append):
    """
    Appends data to a CSV file with the column "Approved".
    If the file doesn't exist, creates it with the column and initial data.

    Args:
        file_name (str): Name of the CSV file.
        data_to_append: Data to append to the "Approved" column. Can be a single value or a list.
    """

    try:
        # Attempt to read existing file
        df = pd.read_csv(file_name)

        # Check if the "Approved" column exists
        if "Skipped" not in df.columns:
            df["Skipped"] = pd.Series(dtype='object')  # Create the column if it doesn't exist
    except FileNotFoundError:
        # If file doesn't exist, create a new DataFrame with the column
        df = pd.DataFrame({"Skipped": []})

    # Ensure data_to_append is a list for consistent handling
    if not isinstance(data_to_append, list):
        data_to_append = [data_to_append]

    # Append the new data (using concat)
    new_data_df = pd.DataFrame({"Skipped": data_to_append})
    df = pd.concat([df, new_data_df], ignore_index=True)

    # Save the updated DataFrame to the CSV file
    df.to_csv(file_name, index=False)


















