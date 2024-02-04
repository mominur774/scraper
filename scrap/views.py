import re
import aiohttp
import asyncio
import csv
import json
import random
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from selenium import webdriver 
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities 
from selenium.webdriver.common.by import By
from selenium.webdriver.common.by import By
from django.conf import settings
import json 
import time


event_loop = asyncio.get_event_loop()



async def fetch_url(request, session, url, headers, data, csv_writer, page_limit):
    try:
        template = json.loads(data)
        results = []

        for page in range(1, page_limit + 1):
            template['pagination']['page'] = page
            random_user_id = random.randint(5000, 20000)
            if not random_user_id == template['user_id']:
                template['user_id'] = random_user_id

            async with session.post(url, headers=headers, json=template) as response:
                if response.status == 200:
                    data = await response.json()
                    for item in data['data']:
                        data_dict = {}
                        for key, value in item.items():
                            data_dict[key] = value['value']
                        results.append(data_dict)
                else:
                    print(f"Request failed with status code {response.status}")

        csv_writer.writerows(results)
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")



async def index(request):
    if request.method == 'POST':
        page_limit = int(request.POST.get('page_limit'))
        search_urls = request.POST.getlist('search_url')


        # Initialize the CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="output.csv"'

        # Initialize the CSV writer
        csv_writer = csv.DictWriter(response, fieldnames=["id", "name", "lead_titles", "phone", "work_phone", "email", "email_score", "company_website",
                        "company_name", "company_phone_numbers", "lead_location", "company_size", "company_industry",
                        "company_profile_image_url", "linkedin_url", "company_id", "facebook_url", "twitter_url"])
        csv_writer.writeheader()

        async with aiohttp.ClientSession() as session:
            tasks = []

            desired_capabilities = DesiredCapabilities.CHROME 
            desired_capabilities["goog:loggingPrefs"] = {"performance": "ALL"} 

            options = webdriver.ChromeOptions() 
            options.add_argument('headless') 
            options.add_argument("--ignore-certificate-errors") 
            driver = webdriver.Chrome(options=options) 
            
            try:
                ##############

                driver.get('https://dashboard.slintel.com/login')

                username_field = driver.find_element('id', 'email') 
                password_field = driver.find_element('id', 'password') 

                username_field.send_keys(getattr(settings, 'EMAIL'))
                password_field.send_keys(getattr(settings, 'PASSWORD'))

                driver.find_element(By.CLASS_NAME, 'ant-btn-primary').click()

                time.sleep(10) 
                ##############

                for index, search_url in enumerate(search_urls):
                    print("\n=========")
                    print(f"Start task {index+1}")
                    print("......")


                    # Your log capture code
                    driver.get(search_url) 

                    # Wait for any additional dynamic content to load
                    time.sleep(10) 

                    # Get performance logs
                    logs = driver.get_log("performance") 

                    api_url = ""
                    headers = {}
                    data = ""

                    for log in logs: 
                        try: 
                            network_log = json.loads(log["message"])["message"] 

                            if "Network.response" in network_log["method"] or \
                                "Network.request" in network_log["method"] or \
                                "Network.webSocket" in network_log["method"]:

                                url = network_log["params"]["request"]["url"]
                                if '/api/v1/leads/search' in url:
                                    api_url = network_log["params"]["request"]["url"]
                                    headers = network_log["params"]["request"]["headers"]
                                    data = network_log["params"]["request"]["postData"]

                        except Exception as e: 
                            pass

                    
                    # driver.quit()

                    curl_command = f'curl \'{api_url}\' \\\n'
                    curl_command += ''.join([f'  -H \'{key}: {value}\' \\\n' for key, value in headers.items()])
                    curl_command += f'  --data-raw $\'{data}\' \\\n'
                    curl_command += '  --compressed'


                    url_pattern = r"curl '(.*?)'"
                    headers_pattern = r"-H '(.*?)'"
                    # data_pattern = r"--data-raw (?:\$)?'(.*?)'"
                    data_pattern = r"--data-raw (?:\$)?'(.*?)'(?:\s|$)"
                    # data_pattern = r"--data-raw (?:\$)?'((?:[^'\\]|\\.)*)'"
                    

                    url_match = re.search(url_pattern, curl_command, re.DOTALL)
                    headers_matches = re.findall(headers_pattern, curl_command)
                    data_match = re.search(data_pattern, curl_command, re.DOTALL)

                    if url_match and headers_matches and data_match:
                        url = url_match.group(1)
                        headers = {key: value for header in headers_matches for key, value in [header.split(": ", 1)]}
                        data = data_match.group(1)

                        if r'[\U0001F600-\U0001F64F]':
                            data = re.sub(r'[\U0001F600-\U0001F64F]', ':[', data)
                        
                        if r"\'n\'":
                            data = data.replace(r"\'n\'", "'n'")
                        
                        if r"\'":
                            data = data.replace(r"\'", "'")


                        tasks.append(fetch_url(request, session, url, headers, data, csv_writer, page_limit))

                        await asyncio.sleep(10) 
                    

                    
                    print(f"End task {index+1}")
                    print("=========\n")
                
                await asyncio.gather(*tasks)
            
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
            finally:
                if driver:
                    driver.quit()


            event_loop.close()

        print("\n=========")
        print(f"Completed")
        print("=========\n")
        return response

    return render(request, 'index.html')
