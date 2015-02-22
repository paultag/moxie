#  Copyright (c) Paul R. Tagliamonte <tag@pault.ag>, 2015
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import asyncio
import smtplib


class EmailAlert:
    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password

    @asyncio.coroutine
    def __call__(self, payload):
        TO = 'paultag@gmail.com'
        SUBJECT = 'TEST MAIL'
        TEXT = 'Here is a message from python.'

        server = smtplib.SMTP(self.host, 587)
        server.ehlo()
        server.starttls()
        server.login(self.user, self.password)

        BODY = '\r\n'.join(['To: %s' % TO,
                            'From: "{}" <{}>'.format("Moxie!", self.user),
                            'Subject: %s' % SUBJECT,
                            '', TEXT])

        server.sendmail(self.user, [TO], BODY)
        server.quit()
