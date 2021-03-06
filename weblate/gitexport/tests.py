# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2017 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <https://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from base64 import b64encode

from django.core.urlresolvers import reverse
from django.http.request import HttpRequest

from weblate.gitexport.views import authenticate
from weblate.gitexport.models import get_export_url
from weblate.trans.tests.test_views import ViewTestCase


class GitExportTest(ViewTestCase):
    def setUp(self):
        super(GitExportTest, self).setUp()
        # We don't want standard Django authentication
        self.client.logout()

    def get_auth_string(self, code):
        encoded = b64encode(
            '{0}:{1}'.format(self.user.username, code).encode('utf-8')
        )
        return 'basic ' + encoded.decode('ascii')

    def test_authenticate_invalid(self):
        request = HttpRequest()
        self.assertFalse(authenticate(request, 'foo'))

    def test_authenticate_missing(self):
        request = HttpRequest()
        self.assertFalse(authenticate(request, 'basic '))

    def test_authenticate_basic_invalid(self):
        request = HttpRequest()
        self.assertFalse(authenticate(request, 'basic fdsafds'))

    def test_authenticate_digest(self):
        request = HttpRequest()
        self.assertFalse(authenticate(request, 'digest fdsafds'))

    def test_authenticate_basic_wrong(self):
        request = HttpRequest()
        self.assertFalse(authenticate(
            request,
            self.get_auth_string('invalid')
        ))

    def test_authenticate_basic(self):
        request = HttpRequest()
        self.assertTrue(authenticate(
            request,
            self.get_auth_string(self.user.auth_token.key)
        ))

    def test_authenticate_basic_inactive(self):
        self.user.is_active = False
        self.user.save()
        request = HttpRequest()
        self.assertFalse(authenticate(
            request,
            self.get_auth_string(self.user.auth_token.key)
        ))

    def get_git_url(self, path):
        kwargs = {'path': path}
        kwargs.update(self.kw_subproject)
        return reverse('git-export', kwargs=kwargs)

    def test_git_root(self):
        response = self.client.get(self.get_git_url(''))
        self.assertEqual(302, response.status_code)

    def test_git_info(self):
        response = self.client.get(self.get_git_url('info'))
        self.assertEqual(404, response.status_code)

    def git_receive(self, **kwargs):
        return self.client.get(
            self.get_git_url('info/refs'),
            QUERY_STRING='?service=git-receive-pack',
            CONTENT_TYPE='application/x-git-upload-pack-advertisement',
            **kwargs
        )

    def test_git_receive_wrong_auth(self):
        response = self.git_receive(HTTP_AUTHORIZATION='foo')
        self.assertEqual(401, response.status_code)

    def test_git_receive(self):
        response = self.git_receive()
        self.assertContains(response, 'refs/heads/master')

    def enable_acl(self):
        self.project.enable_acl = True
        self.project.save()

    def test_git_receive_acl_denied(self):
        self.enable_acl()
        response = self.git_receive()
        self.assertEqual(401, response.status_code)

    def test_git_receive_acl_auth(self):
        self.enable_acl()
        self.project.add_user(self.user)
        response = self.git_receive(
            HTTP_AUTHORIZATION=self.get_auth_string(self.user.auth_token.key)
        )
        self.assertContains(response, 'refs/heads/master')

    def test_git_receive_acl_auth_denied(self):
        self.enable_acl()
        response = self.git_receive(
            HTTP_AUTHORIZATION=self.get_auth_string(self.user.auth_token.key)
        )
        self.assertEqual(403, response.status_code)

    def test_get_export_url(self):
        self.assertEqual(
            'http://example.com/git/test/test/',
            get_export_url(self.subproject)
        )
