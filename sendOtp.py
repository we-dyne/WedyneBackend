#!/usr/bin/env python3

import json
import requests
from random import randint


class sendotp:

    def __init__(self, key = None, msg = ""):

        self.baseUrl = "http://control.msg91.com"
        self.authkey = "288178AJjzyjEswh25d467bff"

        try:
            msg = "Your verification code is {{otp}} valid only 5 minutes. Please do not share it with anybody"
        except NameError:
            self.msg = "Your otp is {{otp}}. Please do not share it with anybody"
        else:
            self.msg = msg

    def actionURLBuilder(self, actionurl):
        # print self.baseUrl + '/api/' +str(actionurl)
        print(actionurl)
        return self.baseUrl + '/api/' + str(actionurl)

    def generateOtp(self):
        return randint(100000, 999999)

    def send(self, contactNumber, senderId):
        otp = self.generateOtp()
        values = {
            'authkey': self.authkey,
            'mobile': contactNumber,
            'message': self.msg.replace("{{otp}}", str(otp)),
            'sender': senderId,
            'otp': otp,
            'otp_expiry' : '5'
        }
        print(self.call('sendotp.php', values))
        return otp

    def retry(self, contactNumber, retrytype='text'):
        values = {
            'authkey': self.authkey,
            'mobile': contactNumber,
            'retrytype': retrytype
        }
        print(values)
        response = self.call('retryotp.php', values)

        return response

    def verify(self, contactNumber, otp):
        values = {
            'authkey': self.authkey,
            'mobile': contactNumber,
            'otp': otp
        }
        response = self.call('verifyRequestOTP.php', values)
        return response

    def call(self, actionurl, args):
        url = self.actionURLBuilder(actionurl)
        print(url)
        payload = (args)

        response = requests.post(url, data=payload, verify=False)
        return response.text
