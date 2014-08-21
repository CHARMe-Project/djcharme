'''
BSD Licence
Copyright (c) 2014, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice,
        this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
        this list of conditions and the following disclaimer in the
        documentation and/or other materials provided with the distribution.
    * Neither the name of the Science & Technology Facilities Council (STFC)
        nor the names of its contributors may be used to endorse or promote
        products derived from this software without specific prior written
        permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Created on 26 July 2013

@author: mnagni
'''


class CharmeError(Exception):
    """
        Raises all the exceptions related to the dj_charme
        class operations
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class SerializeError(CharmeError):
    """
        General error during graph serialisation
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class StoreConnectionError(CharmeError):
    """
        General connection error to the triplestore
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class SecurityError(CharmeError):
    """
        General security error
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class PasswordNotMachesError(CharmeError):
    """
        Throw when a user is not authenticated
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class UserNotFoundError(CharmeError):
    """
        Throw when a user is not found in db
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class MissingCookieError(SecurityError):
    """
        Missing cookie error
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class ParseError(SecurityError):
    """
        Parse error
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class NotFoundError(CharmeError):
    """
        Throw when an item is not found
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class UserError(CharmeError):
    """
        Throw when a user creates an error
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


