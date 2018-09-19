# -*- coding: utf-8 -*-

from django.test import TestCase
import factories
from rest_framework.test import APIRequestFactory

from workflow.models import Internationalization
from ..views import InternationalizationViewSet


class InternationalizationListViewTest(TestCase):
    def setUp(self):
        factories.Internationalization()
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()

    def test_list_internationalization_superuser(self):
        """
        Superusers are able to list all the objects
        """
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        request = self.factory.get('/api/internationalization/')
        view = InternationalizationViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_internationalization_normaluser(self):
        """
        Normal users are able to list all the objects
        """
        request = self.factory.get('/api/internationalization/')
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class InternationalizationCreateViewTest(TestCase):
    def setUp(self):
        self.tola_user = factories.CoreUser()
        self.factory = APIRequestFactory()

    def test_create_internationalization_superuser(self):
        """
        Superusers are able to create new translations
        """
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        data = {
            u'language': u'pt-BR',
            u'language_file': u'{"name": "Nome", "gender": "Gênero"}'
        }
        request = self.factory.post('/api/internationalization/', data)
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['language'], data['language'])

    def test_create_internationalization_normaluser(self):
        """
        Normal users aren't able to create new translations
        """
        data = {
            u'language': u'pt-BR',
            u'language_file': u'{"name": "Nome", "gender": "Gênero"}'
        }
        request = self.factory.post('/api/internationalization/', data)
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 403)


class InternationalizationRetrieveViewsTest(TestCase):
    def setUp(self):
        self.tola_user = factories.CoreUser()
        self.factory = APIRequestFactory()

    def test_retrieve_unexisting_internationalization(self):
        request = self.factory.get('/api/internationalization/1111')
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=1111)
        self.assertEqual(response.status_code, 404)

    def test_retrieve_internationalization_superuser(self):
        """
        Superusers are able to retrieve any translation
        """
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()
        inter = factories.Internationalization()

        request = self.factory.get('/api/internationalization/{}'.format(
            inter.id))
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=inter.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['language'], inter.language)

    def test_retrieve_internationalization_normaluser(self):
        """
        Normal users are able to retrieve any translation
        """
        inter = factories.Internationalization()

        request = self.factory.get('/api/internationalization/{}'.format(
            inter.id))
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'get': 'retrieve'})
        response = view(request, pk=inter.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['language'], inter.language)


class InternationalizationUpdateViewTest(TestCase):
    def setUp(self):
        self.tola_user = factories.CoreUser()
        self.factory = APIRequestFactory()

    def test_update_unexisting_internationalization(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        data = {
            u'language': u'pt-BR',
        }
        request = self.factory.post('/api/internationalization/', data)
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'post': 'update'})
        response = view(request, pk=999)

        self.assertEqual(response.status_code, 404)

    def test_update_internationalization_superuser(self):
        """
        Superusers are able to update translations
        """
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()
        inter = factories.Internationalization()

        data = {
            u'language': u'pt-BR',
            u'language_file': u'{"name": "Nome", "gender": "Gênero"}'
        }
        request = self.factory.post('/api/internationalization/', data)
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'post': 'update'})
        response = view(request, pk=inter.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['language'], data['language'])

    def test_update_internationalization_normaluser(self):
        """
        Normal users aren't able to update translations
        """
        inter = factories.Internationalization()

        data = {
            u'language': u'pt-BR',
        }
        request = self.factory.post('/api/internationalization/', data)
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'post': 'update'})
        response = view(request, pk=inter.pk)

        self.assertEqual(response.status_code, 403)


class InternationalizationDeleteViewTest(TestCase):
    def setUp(self):
        self.tola_user = factories.CoreUser()
        self.factory = APIRequestFactory()

    def test_delete_unexisting_internationalization(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        request = self.factory.delete('/api/internationalization/')
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=999)

        self.assertEqual(response.status_code, 404)

    def test_delete_internationalization_superuser(self):
        """
        Superusers are able to delete any translation
        """
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()
        inter = factories.Internationalization()

        request = self.factory.delete('/api/internationalization/')
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=inter.pk)

        self.assertEqual(response.status_code, 204)
        self.assertRaises(
            Internationalization.DoesNotExist,
            Internationalization.objects.get, pk=inter.pk)

    def test_delete_internationalization_normaluser(self):
        """
        Normal users aren't able to delete translations
        """
        inter = factories.Internationalization()

        request = self.factory.delete('/api/internationalization/')
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=inter.pk)

        self.assertEqual(response.status_code, 403)


class InternationalizationFilterViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()

    def test_filter_internationalization_by_language(self):
        """
        Any user can filter translations by language
        """
        factories.Internationalization()
        inter_pt_br = factories.Internationalization(language='pt-BR')

        query_string = 'language={}'.format(inter_pt_br.language)
        url = '/api/internationalization/?{}'.format(query_string)

        request = self.factory.get(url)
        request.user = self.tola_user.user
        view = InternationalizationViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['language'], inter_pt_br.language)