# Faizan Ahmed
# 9/7/2021

import time, logging
import pandas as pd
from bs4 import BeautifulSoup
from typing import Tuple, List
from tqdm import tqdm
import requests
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select


driver = ''
baseURL = ''
numPages = 0


def getJobResults(position, location) -> Tuple[str, int]:
    """
    Go to the Indeed jobs page for the position and location specified by the user
    
    Returns:
        baseURL: The URL of the Indeed page 
        numPages: How many pages of results there are 
    """
    
    
    global driver 
    global numPages
        
    jobType = '&jt=internship' if 'intern' in position.lower() else ''
    remote = '&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11&vjk=7eb57af506a13421' if 'remote' in location.lower() else ''
            
    url = f"https://www.indeed.com/jobs?q={position.replace(' ', '%20')}&l={location.replace(' ', '%20')}{jobType}{remote}" 
    
    driver = webdriver.Chrome('chromedriver.exe')
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument("--log-level=3")
    
    driver.get(url)
    
    time.sleep(10)
    
    jobsFound = driver.find_elements_by_xpath('/html/body/table[2]/tbody/tr/td/table/tbody/tr/td[1]/div[3]/div[4]/div[2]/div')[0].text
    
    jobsFound = jobsFound.replace(',', '')
    jobsFound = jobsFound[jobsFound.find('of') + 3 : ] + ' found!'
    
    numPages = (int(jobsFound[0 : jobsFound.find(' ')]) // 11) + 1
    
    if numPages > 10: 
        numPages = 10
    
    baseURL = driver.current_url
    
    print(f"\n{jobsFound} {numPages} pages of results\n")
    
    time.sleep(1)
    
    return baseURL, numPages
    
    

def getJobLinks(url) -> List[str]:
    """
    Get all the application links for the jobs on the webpage
    
    Args:
        url: The URL of the Indeed page with all the job postings
        
    Returns:
        jobLinks: A list of all the URLs that link directly (most of the time) to the company's application page
    """
    
    global driver 
    
    driver.get(url)
    #time.sleep(2)
    
    jobCards = driver.find_elements_by_xpath('//div[contains(@class,"mosaic-zone")]')

    # Get all the jobs listed on the page
    jobList = jobCards[1].find_elements_by_xpath('./*[@id="mosaic-provider-jobcards"]')
    jobs = jobList[0].find_elements_by_xpath('./*')


    for job in jobs:

        try:
            jobListings = job.find_elements_by_xpath('//*[starts-with(@class, "tapItem")]')
            jobLinks = [elem.get_attribute('href') for elem in jobListings]
        
        except:
            print('Err')
            jobLinks = []
      
    
    return jobLinks
    

    
def getJobInfo(jobLinks) -> List[dict]:
    '''
    Iterate through each jobLink and extract the data on each of the pages
    
    From each job page, the 
        - Job Title
        - Company
        - Location
        - Reviews
        - Description
        - Application Link
        - Job Post Date 
        - Salary 
    is extracted 
    
    Returns:
        pageJobs: A list of dictionaries that contains all the job data from each of the job listings on an Indeed page
    '''
    
    
    global driver 
    
    pageJobs = []

    for link in jobLinks:

        driver.get(link)

        jobDetails = {}

        # Get the job's title
        title = driver.find_elements_by_xpath('//div[starts-with(@class, "jobsearch-JobInfoHeader-title-container")]')
        
        try:
            jobDetails['Title'] = title[0].text
        except:
            jobDetails['Title'] = 'N/A'


        # Get the job's company
        compElements = driver.find_elements_by_xpath('//div[starts-with(@class, "icl-u-xs-mt--xs")]')

        try:
            companies = compElements[0].find_elements_by_xpath('./div[*]')
            try:
                jobDetails['Company'] = companies[0].text.split('\n')[0]
            except:
                jobDetails['Company'] = 'N/A'
        except:
            jobDetails['Company'] = 'N/A'


        # Find the job's specified location
        try:
            loc = compElements[0].find_elements_by_xpath('./.')
            loc2 = loc[0].find_elements_by_xpath('./.')

            jobDetails['Location'] = loc2[0].text.split('\n')[1]

        except:
            jobDetails['Location'] = 'N/A'

        
        if 'reviews' in jobDetails['Location']:
            try:
                jobDetails['Location'] = loc2[0].text.split('\n')[2]
            except:
                print('Location Error')



        # Find reviews on the company
        rev = driver.find_elements_by_xpath('//div[starts-with(@class, "icl-Ratings-starsCountWrapper")]')
        
        try:
            jobDetails['Reviews'] = rev[0].get_attribute("aria-label")
        except:
            jobDetails['Reviews'] = 'N/A'


        # Find the job description
        desc = driver.find_elements_by_xpath('//div[@id="jobDescriptionText"]')
        
        try:
        
            jobDetails['Description'] = desc[0].text.replace('\n', '')
        
        except:
            try:
                desc2 = desc[0].find_elements_by_xpath('./*')
                text = ""
                for v in desc2:
                    text += v.text

                jobDetails['Description'] = text.replace('\n', '')
            except:
                jobDetails['Description'] = 'N/A'


        # Find Application Link
        try:
            app = driver.find_elements_by_xpath('//div[@id="applyButtonLinkContainer"]')
            app2 = app[0].find_elements_by_xpath('./*')
            app3 = app2[0].find_elements_by_xpath('./*')
            app4 = app3[0].find_elements_by_xpath('./*')

            jobDetails['Application Link'] = app4[0].get_attribute('href')
            

        except:
            
            jobDetails['Application Link'] = driver.current_url
            

        # Find when the job was posted
        try:
            jobPostDate = driver.find_elements_by_xpath('//div[@class="jobsearch-JobMetadataFooter"]')
            jobPostDate = jobPostDate[0].find_elements_by_xpath('./div')

            if len(jobPostDate) == 3:
                jobDetails['Job Post Date'] = jobPostDate[0].text
                
            elif len(jobPostDate) != 0:
                jobDetails['Job Post Date'] = jobPostDate[1].text
                
            else:
                jobDetails['Job Post Date'] = 'N/A'
        
        except:
            jobDetails['Job Post Date'] = 'N/A'


        # Get the job position's salary
        try:
            sal = driver.find_elements_by_xpath('//span[@class="icl-u-xs-mr--xs"]')
            if len(sal) > 0:
                jobDetails['Salary'] = sal[0].text
            else:
                jobDetails['Salary'] = 'N/A'
        except:
            jobDetails['Salary'] = 'N/A'


        pageJobs.append(jobDetails)
        
        
    return pageJobs



def scrapeJobs(position, location, baseURL, numPages) -> List[dict]:
    '''
    Iterate through the Indeed pages and extract the job data 
    
    Returns:
        allJobData: The extracted data from all the jobs listings through a specified amount of pages
    '''
    
    allJobData = []
    
    for page in tqdm(range(numPages)):
        
        pageAddOn = f"&start={page * 10}" if page > 0 else ''
        
        links = getJobLinks(baseURL + pageAddOn)
        
        jobData = getJobInfo(links)
        
        allJobData.extend(jobData)
        
        #print(jobData)
        
        
    return allJobData



def saveToCSV(jobData, position, location):
    '''
    Save all the scraped job data into a CSV file
    '''
    
    global driver
    
    fileName = f"{position} {location} Job Postings.csv"
    keys = jobData[0].keys()
    
    with open(fileName, 'w', newline='', encoding="utf-8") as outputFile:
        
        dictWriter = csv.DictWriter(outputFile, keys)
        dictWriter.writeheader()
        dictWriter.writerows(jobData)
    
    print('\nSaved as', fileName)
    
    driver.close()
    

    
position = input("\nEnter the job position you are searching for: ") 
location = input("\nWhat is your desired job location? Type 'remote' if you are interested in only remote roles: ")


baseURL, numpages = getJobResults(position, location)

allJobData = scrapeJobs(position, location, baseURL, numPages)

saveToCSV(allJobData, position, location)


