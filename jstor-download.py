#Created by Timothy Gamble

import os
import re
import time
import json
import glob
import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select

profile = webdriver.FirefoxProfile()
profile.set_preference("pdfjs.disabled", True)
profile.set_preference("browser.download.folderList",2)
profile.set_preference("browser.helperApps.alwaysAsk.force", False)
profile.set_preference("browser.download.manager.showWhenStarting",False)
profile.set_preference("browser.download.dir", "/Users/Tim/Documents/Github/jstor-downloader/temp") #Point this to the temp folder
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
profile.set_preference("plugin.disable_full_page_plugin_for_types", "application/pdf")
driver = webdriver.Firefox(firefox_profile=profile)

__MAINURL__ = "https://www.jstor.org/action/showLogin?redirectUri=/?&loginSuccess=true&aerror=I001"
__BROWSEURL__ = "http://www.jstor.org/action/showJournals?browseType=title&contentType=books&letter=0-9"
__USERNAME__ = raw_input('Username: ')
__PASSWORD__ = getpass.getpass('Password: ')

def login(): #Edit the login process for your school, mine is UIUC
	driver.get(__MAINURL__)
	driver.find_element(By.XPATH,'//*[@id="inst_container"]/table/tbody/tr[212]/td[2]/a').click()
	time.sleep(5)
	driver.find_element(By.XPATH,'//input[@id="j_username"]').send_keys(__USERNAME__)
	driver.find_element(By.XPATH,'//input[@id="j_password"]').send_keys(__PASSWORD__)
	driver.find_element(By.XPATH,'//div[@id="submit_button"]/input').click()
	time.sleep(5)

def get_parent_links():
	driver.find_element(By.XPATH,'//*[@id="menu-global-browse"]').click()
	time.sleep(5)
	driver.find_element(By.XPATH,'//*[@id="content"]/div[1]/div[4]/div/dl/dd[3]/a').click()
	time.sleep(5)
	_as = driver.find_elements(By.XPATH,'//*[@id="browseBy"]/li/a')
	parent_links = []
	for a in _as:
		parent_links.append(a.get_attribute('href'))
	return parent_links

def get_book_links():
	book_links = []
	for link in get_parent_links():
		driver.get(link)
		time.sleep(5)
		_as = driver.find_elements(By.XPATH,'//table[@class="browse-table"]/tbody/tr/td[@scope="row"]/a')
		for a in _as:
			book_links.append(a.get_attribute('href'))
	with open('book_links.json','w') as output:
		json.dump(book_links, output)

def download_book(url):
	driver.get(url)
	time.sleep(5)
	try:
		driver.find_element(By.XPATH,'//*[@id="content"]/div[1]/div[2]/div[2]/div/div/div/div[1]/span')
		return
	except:
		chapters = driver.find_elements(By.XPATH,'//a[@class="pdfLink tt-track-nolink"]')
		isbn = driver.find_element(By.XPATH,'//div[@class="book-eisbn mtm"]').get_attribute('innerHTML').split(' ')[-1].replace('-','')
		for chapter in chapters:
			driver.get(chapter.get_attribute('href') + '?acceptTC=true')
		time.sleep(5)
		merge_pdf(url,isbn)

def key_func(afilename):
	nondigits = re.compile("\D")
	return int(nondigits.sub("", afilename))

def merge_pdf(url,isbn):
	name = url.split('/')[-1]
	file_names = []
	for x in sorted(glob.glob('temp/*.pdf'), key=key_func):
		file_names.append(x)
	if len(file_names) != 0:
		merger = PdfFileMerger()
	else:
		return
	for filename in file_names:
		merger.append(fileobj = PdfFileReader(file(filename, 'rb')), pages = (1,PdfFileReader(open(filename)).getNumPages()))
	merger.write("books/" + isbn + ".pdf")
	for f in file_names:
		os.remove(f)
	crop_pdf(isbn)

def crop_pdf(isbn):
	input1 = PdfFileReader(file(os.getcwd() + "/books/" + isbn + ".pdf", "rb"))
	output = PdfFileWriter()
	numPages = input1.getNumPages()
	for i in range(numPages):
		page = input1.getPage(i)
		page.cropBox.lowerLeft = (0, 60)
		output.addPage(page)
	os.remove(os.getcwd() + "/books/" + isbn + ".pdf")
	outputStream = file(os.getcwd() + "/books/" + isbn + ".pdf", "wb")
	output.write(outputStream)
	outputStream.close()

def download_all_books():
	with open('book_links.json','r') as links:
		book_links = json.loads(links.read())
		for link in book_links:
			download_book(link)

if __name__ == '__main__':
	login()
	# get_book_links() #Comment this out after you gathered all of the book links.
	download_all_books()
	driver.close()
