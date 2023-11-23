from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from email.mime.text import MIMEText

import whois, logging, requests, time, smtplib, os, ssl

def check_file(filename):
    with open(f"{filename}.txt", 'r', encoding="utf8") as file:
        lines = file.read().splitlines()
    
    with open(f"{filename}_checked.txt", 'w', encoding="utf8") as file:
        for noun in lines:
            if " " in noun:
                continue
            file.write(f"{noun}:  ")
            try:
                whois.whois(f'{noun}.de')
                file.write(f"-")
            except whois.parser.PywhoisError:
                file.write(f"FREE")
            except Exception as e:
                file.write(f'cant be checked: {e}')
            file.write("\n")

def save_word_of_the_days(year, month, day):
    words = []
    response = requests.get(f"https://wod.corpora.uni-leipzig.de/de/de/{year}/{month}/{day}")
    if response.status_code == 200:
        parsed = BeautifulSoup(response.text, 'html.parser')
        div_elements = parsed.find_all("div", {"class": "sphereContainer sphereContainer_text"})
        
        if div_elements:
            for div_element in div_elements:
                for a_tag in div_element.find_all('a'):
                    link_text = a_tag.get_text(strip=True)
                    words.append(link_text + "\n")

            with open(f"{year}_{month}_{day}.txt", 'w', encoding="utf8") as file:
                file.writelines(words)
            logging.info(f'Words saved - {datetime.now().strftime("%d.%m.%Y, %H:%M:%S")}')
            return True
        return False

def send_mail(filename):
    load_dotenv()

    sender = os.getenv("SENDER")
    receiver = os.getenv("RECEIVER")
    server = os.getenv("SERVER")
    server_port = os.getenv("SERVER_PORT")
    password = os.getenv("PASSWORD")

    with open(f"{filename}_checked.txt", 'r', encoding="utf8") as file:
        lines = file.read().splitlines()

    msg = MIMEText("\n".join(lines))
    msg['Subject'] = filename
    msg['From'] = sender
    msg['To'] = receiver

    s = smtplib.SMTP(server, server_port)
    s.ehlo()
    s.starttls() 
    s.ehlo()
    s.login(sender, password)
    s.sendmail(sender, [receiver], msg.as_string())

    logging.info(f'Email sent - {datetime.now().strftime("%d.%m.%Y, %H:%M:%S")}')

if __name__ == "__main__":
    logging.basicConfig(filename='crawler.log', encoding='utf-8', level=logging.DEBUG)

    day = datetime.now().day -1
    month = datetime.now().month
    year = datetime.now().year

    last_check = time.time()

    while True:
        if save_word_of_the_days(year, month, day):
            check_file(f"{year}_{month}_{day}")
            send_mail(f"{year}_{month}_{day}")
            time.sleep(12 * 60 * 60) # 12 hours
            logging.info(f'Sleep for 12 hours - {datetime.now().strftime("%d.%m.%Y, %H:%M:%S")}')

        time.sleep(10 * 60) # 10 minutes
        logging.info(f'Try again in 5 Minutes - {datetime.now().strftime("%d.%m.%Y, %H:%M:%S")}')
