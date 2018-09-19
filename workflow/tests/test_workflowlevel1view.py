import json
import re

from django.test import TestCase
import factories
from rest_framework.reverse import reverse
from rest_framework.serializers import ValidationError
from rest_framework.test import APIRequestFactory
from workflow.models import (WorkflowTeam, WorkflowLevel1,
                             ROLE_ORGANIZATION_ADMIN, ROLE_PROGRAM_TEAM,
                             ROLE_PROGRAM_ADMIN, ROLE_VIEW_ONLY)

from ..serializers import WorkflowLevel1PermissionsSerializer
from ..views import WorkflowLevel1ViewSet
from mock import patch, PropertyMock


class WorkflowLevel1ListViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()
        factories.Group()

    def test_list_workflowlevel1_superuser(self):
        wflvl1 = factories.WorkflowLevel1()
        wflvl2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)

        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        request = self.factory.get('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wflvl1.name)

    def test_list_workflowlevel1_superuser_and_org_admin(self):
        wflvl1 = factories.WorkflowLevel1()
        wflvl2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        request = self.factory.get('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wflvl1.name)
        self.assertEqual(response.data[0]['budget'],
                         wflvl2.total_estimated_budget)

    def test_list_workflowlevel1_org_admin(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        request = self.factory.get('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wflvl1.name)

    def test_list_workflowlevel1_program_admin(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        group_program_admin = factories.Group(name=ROLE_PROGRAM_ADMIN)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user, workflowlevel1=wflvl1,
            role=group_program_admin)

        request = self.factory.get('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wflvl1.name)

    def test_list_filter_workflowlevel1_program_admin(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl1_2 = factories.WorkflowLevel1(
            name='Population Health Initiative',
            organization=self.tola_user.organization)
        group_program_admin = factories.Group(name=ROLE_PROGRAM_ADMIN)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user, workflowlevel1=wflvl1,
            role=group_program_admin)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user, workflowlevel1=wflvl1_2,
            role=group_program_admin)

        request = self.factory.get('/api/workflowlevel1/?name=%s' %
                                   wflvl1.name)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wflvl1.name)
        self.assertNotEqual(response.data[0]['name'], wflvl1_2.name)

    def test_list_workflowlevel1_program_team(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        group_program_team = factories.Group(name=ROLE_PROGRAM_TEAM)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user, workflowlevel1=wflvl1,
            role=group_program_team)

        request = self.factory.get('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wflvl1.name)

    def test_list_workflowlevel1_normal_user_same_org(self):
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            partner_org=self.tola_user.organization,
            role=factories.Group(name=ROLE_VIEW_ONLY))
        factories.WorkflowLevel1(organization=self.tola_user.organization)

        request = self.factory.get('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    @patch('api.views.DefaultCursorPagination.page_size',
           new_callable=PropertyMock)
    def test_list_workflowlevel1_pagination(self, page_size_mock):
        ''' For page_size 1 and pagination true, list wfl1 endpoint should
         return 1 wfl1 for each page'''
        # set page_size =1
        page_size_mock.return_value = 1
        wfl1_1 = factories.WorkflowLevel1(
            name='1. wfl', organization=self.tola_user.organization)
        wfl1_2 = factories.WorkflowLevel1(
            name='2. wfl', organization=self.tola_user.organization)
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        request = self.factory.get('?paginate=true')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)

        # page_size = 1, so it should return just one wfl1
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], wfl1_1.name)

        m = re.search('=(.*)&', response.data['next'])
        cursor = m.group(1)

        request = self.factory.get('?cursor={}&paginate=true'.format(
            cursor))
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], wfl1_2.name)


class WorkflowLevel1PermissionsListViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()
        factories.Group()

    def test_list_permissions_superuser_empty(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data,
                         {'permissions': [], 'role_org': 'Admin'})

    def test_list_permissions_superuser(self):
        organization_other = factories.Organization(name='ACME')
        factories.WorkflowLevel1(organization=organization_other)

        wflvl1_0 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl1_1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)

        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                'permissions': [
                    {
                        'workflowlevel1_id': wflvl1_0.id,
                        'workflowlevel1_uuid': str(wflvl1_0.level1_uuid),
                        'role': 'Admin',
                        'create': True,
                        'edit': True,
                        'remove': True,
                        'manageUsers': True,
                        'view': True,
                    },
                    {
                        'workflowlevel1_id': wflvl1_1.id,
                        'workflowlevel1_uuid': str(wflvl1_1.level1_uuid),
                        'role': 'Admin',
                        'create': True,
                        'edit': True,
                        'remove': True,
                        'manageUsers': True,
                        'view': True,
                    }
                ],
                'role_org': 'Admin',
            })

    def test_list_permissions_org_admin_empty(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data,
                         {'permissions': [],
                          'role_org': ROLE_ORGANIZATION_ADMIN})

    def test_list_permissions_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)

        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                'permissions': [
                    {
                        'workflowlevel1_id': wflvl1.id,
                        'workflowlevel1_uuid': str(wflvl1.level1_uuid),
                        'role': ROLE_ORGANIZATION_ADMIN,
                        'create': True,
                        'edit': True,
                        'remove': True,
                        'manageUsers': True,
                        'view': True,
                    },
                ],
                'role_org': ROLE_ORGANIZATION_ADMIN,
            })

    def test_list_permissions_program_admin(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        factories.WorkflowTeam(workflow_user=self.tola_user,
                               role=factories.Group(name=ROLE_PROGRAM_ADMIN),
                               workflowlevel1=wflvl1)

        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                'permissions': [
                    {
                        'workflowlevel1_id': wflvl1.id,
                        'workflowlevel1_uuid': str(wflvl1.level1_uuid),
                        'role': ROLE_PROGRAM_ADMIN,
                        'create': True,
                        'edit': True,
                        'remove': True,
                        'manageUsers': True,
                        'view': True,
                    },
                ],
            })

    def test_list_permissions_program_team(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        factories.WorkflowTeam(workflow_user=self.tola_user,
                               role=factories.Group(name=ROLE_PROGRAM_TEAM),
                               workflowlevel1=wflvl1)

        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                'permissions': [
                    {
                        'workflowlevel1_id': wflvl1.id,
                        'workflowlevel1_uuid': str(wflvl1.level1_uuid),
                        'role': ROLE_PROGRAM_TEAM,
                        'create': True,
                        'edit': True,
                        'remove': False,
                        'manageUsers': False,
                        'view': True,
                    },
                ],
            })

    def test_list_permissions_view_only(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        factories.WorkflowTeam(workflow_user=self.tola_user,
                               role=factories.Group(name=ROLE_VIEW_ONLY),
                               workflowlevel1=wflvl1)

        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                'permissions': [
                    {
                        'workflowlevel1_id': wflvl1.id,
                        'workflowlevel1_uuid': str(wflvl1.level1_uuid),
                        'role': ROLE_VIEW_ONLY,
                        'create': False,
                        'edit': False,
                        'remove': False,
                        'manageUsers': False,
                        'view': True,
                    },
                ],
            })

    def test_list_permissions_mixed(self):
        wflvl1_0 = factories.WorkflowLevel1(
            name='wflvl1_0', organization=self.tola_user.organization)
        wflvl1_1 = factories.WorkflowLevel1(
            name='wflvl1_1', organization=self.tola_user.organization)
        wflvl1_2 = factories.WorkflowLevel1(
            name='wflvl1_2', organization=self.tola_user.organization)
        factories.WorkflowTeam(workflow_user=self.tola_user,
                               role=factories.Group(name=ROLE_PROGRAM_ADMIN),
                               workflowlevel1=wflvl1_0)
        factories.WorkflowTeam(workflow_user=self.tola_user,
                               role=factories.Group(name=ROLE_PROGRAM_TEAM),
                               workflowlevel1=wflvl1_1)
        factories.WorkflowTeam(workflow_user=self.tola_user,
                               role=factories.Group(name=ROLE_VIEW_ONLY),
                               workflowlevel1=wflvl1_2)

        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                'permissions': [
                    {
                        'workflowlevel1_id': wflvl1_0.id,
                        'workflowlevel1_uuid': str(wflvl1_0.level1_uuid),
                        'role': ROLE_PROGRAM_ADMIN,
                        'create': True,
                        'edit': True,
                        'remove': True,
                        'manageUsers': True,
                        'view': True,
                    },
                    {
                        'workflowlevel1_id': wflvl1_1.id,
                        'workflowlevel1_uuid': str(wflvl1_1.level1_uuid),
                        'role': ROLE_PROGRAM_TEAM,
                        'create': True,
                        'edit': True,
                        'remove': False,
                        'manageUsers': False,
                        'view': True,
                    },
                    {
                        'workflowlevel1_id': wflvl1_2.id,
                        'workflowlevel1_uuid': str(wflvl1_2.level1_uuid),
                        'role': ROLE_VIEW_ONLY,
                        'create': False,
                        'edit': False,
                        'remove': False,
                        'manageUsers': False,
                        'view': True,
                    },
                ],
            })

    def test_list_permissions_view_only_group_empty(self):
        group_view_only = factories.Group(name=ROLE_VIEW_ONLY)
        self.tola_user.user.groups.add(group_view_only)

        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data,
                         {'permissions': [], 'role_org': ROLE_VIEW_ONLY})

    def test_list_permissions_view_only_group(self):
        group_org_admin = factories.Group(name=ROLE_VIEW_ONLY)
        self.tola_user.user.groups.add(group_org_admin)
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)

        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {
                'permissions': [
                    {
                        'workflowlevel1_id': wflvl1.id,
                        'workflowlevel1_uuid': str(wflvl1.level1_uuid),
                        'role': ROLE_VIEW_ONLY,
                        'create': False,
                        'edit': False,
                        'remove': False,
                        'manageUsers': False,
                        'view': True,
                    },
                ],
                'role_org': ROLE_VIEW_ONLY,
            })

    def test_list_permissions_empty(self):
        request = self.factory.get('')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'permissions': []})

    def test_list_permissions_anonymoususer(self):
        request = self.factory.get('')
        view = WorkflowLevel1ViewSet.as_view({'get': 'permissions'})
        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_get_user_org_role_is_superuser(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        view = WorkflowLevel1ViewSet()
        result = view._get_user_org_role(self.tola_user.user)
        self.assertEqual(result, 'Admin')

    def test_get_user_org_role_is_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        view = WorkflowLevel1ViewSet()
        result = view._get_user_org_role(self.tola_user.user)
        self.assertEqual(result, ROLE_ORGANIZATION_ADMIN)

    def test_get_user_org_role_is_view_only(self):
        group_view_only = factories.Group(name=ROLE_VIEW_ONLY)
        self.tola_user.user.groups.add(group_view_only)

        view = WorkflowLevel1ViewSet()
        result = view._get_user_org_role(self.tola_user.user)
        self.assertEqual(result, ROLE_VIEW_ONLY)

    def test_get_user_org_role_is_mixed(self):
        group_view_only = factories.Group(name=ROLE_VIEW_ONLY)
        self.tola_user.user.groups.add(group_view_only)
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        view = WorkflowLevel1ViewSet()
        result = view._get_user_org_role(self.tola_user.user)
        self.assertEqual(result, ROLE_ORGANIZATION_ADMIN)

    def test_permission_serializer_match(self):
        group_org_admin = factories.Group(name=ROLE_VIEW_ONLY)
        self.tola_user.user.groups.add(group_org_admin)
        factories.WorkflowLevel1(organization=self.tola_user.organization)

        view = WorkflowLevel1ViewSet()
        data = {
            'role_org': ROLE_VIEW_ONLY,
        }
        permissions = view._get_permissions(self.tola_user.user,
                                            ROLE_VIEW_ONLY)
        data['permissions'] = permissions

        serializer = WorkflowLevel1PermissionsSerializer(data=data)
        serializer.is_valid(raise_exception=True)

    def test_permission_serializer_not_match(self):
        group_org_admin = factories.Group(name=ROLE_VIEW_ONLY)
        self.tola_user.user.groups.add(group_org_admin)
        factories.WorkflowLevel1(organization=self.tola_user.organization)

        view = WorkflowLevel1ViewSet()
        data = {
            'role_org': 'Invented',
        }
        permissions = view._get_permissions(self.tola_user.user,
                                            ROLE_VIEW_ONLY)
        data['permissions'] = permissions

        serializer = WorkflowLevel1PermissionsSerializer(data=data)
        self.assertRaises(ValidationError, serializer.is_valid,
                          raise_exception=True)


class WorkflowLevel1CreateViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()
        factories.Group()

    def test_create_workflowlevel1_superuser(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        organization_url = reverse(
            'organization-detail',
            kwargs={'pk': self.tola_user.organization.pk})
        data = {'name': 'Save the Children', 'organization': organization_url}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], u'Save the Children')

        WorkflowTeam.objects.get(
            workflowlevel1__id=response.data['id'],
            workflow_user=self.tola_user,
            role__name=ROLE_PROGRAM_ADMIN)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertEqual(wflvl1.organization, self.tola_user.organization)
        self.assertEqual(wflvl1.user_access.all().count(), 1)
        self.assertEqual(wflvl1.user_access.first(), self.tola_user)

    def test_create_workflowlevel1_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        data = {'name': 'Save the Children'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], u'Save the Children')

        WorkflowTeam.objects.get(
            workflowlevel1__id=response.data['id'],
            workflow_user=self.tola_user,
            role__name=ROLE_PROGRAM_ADMIN)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertEqual(wflvl1.organization, self.tola_user.organization)
        self.assertEqual(wflvl1.user_access.all().count(), 1)
        self.assertEqual(wflvl1.user_access.first(), self.tola_user)

    def test_create_workflowlevel1_program_admin(self):
        """
        A ProgramAdmin member of any other program can create a new program
        in the same organization.
        """
        organization_url = reverse(
            'organization-detail',
            kwargs={'pk': self.tola_user.organization.pk})
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=factories.WorkflowLevel1(
                organization=self.tola_user.organization),
            role=factories.Group(name=ROLE_PROGRAM_ADMIN))

        data = {'name': 'Save the Children'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], u'Save the Children')
        self.assertIn(organization_url, response.data['organization'])

        WorkflowTeam.objects.get(
            workflowlevel1__id=response.data['id'],
            workflow_user=self.tola_user,
            role__name=ROLE_PROGRAM_ADMIN)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertEqual(wflvl1.organization, self.tola_user.organization)
        self.assertEqual(wflvl1.user_access.all().count(), 1)
        self.assertEqual(wflvl1.user_access.first(), self.tola_user)

    def test_create_workflowlevel1_program_admin_json(self):
        """
        A ProgramAdmin member of any other program can create a new program
        in the same organization.
        """
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=factories.WorkflowLevel1(
                organization=self.tola_user.organization),
            role=factories.Group(name=ROLE_PROGRAM_ADMIN))

        data = {'name': 'Save the Children'}
        request = self.factory.post('/api/workflowlevel1/', json.dumps(data),
                                    content_type='application/json')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], u'Save the Children')

        WorkflowTeam.objects.get(
            workflowlevel1__id=response.data['id'],
            workflow_user=self.tola_user,
            role__name=ROLE_PROGRAM_ADMIN)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertEqual(wflvl1.organization, self.tola_user.organization)
        self.assertEqual(wflvl1.user_access.all().count(), 1)
        self.assertEqual(wflvl1.user_access.first(), self.tola_user)

    def test_create_workflowlevel1_program_team(self):
        """
        A ProgramTeam member of any other program can create a new program in
        the same organization.
        """
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=factories.WorkflowLevel1(
                organization=self.tola_user.organization),
            role=factories.Group(name=ROLE_PROGRAM_TEAM))

        data = {'name': 'Save the Children'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], u'Save the Children')

        WorkflowTeam.objects.get(
            workflowlevel1__id=response.data['id'],
            workflow_user=self.tola_user,
            role__name=ROLE_PROGRAM_ADMIN)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertEqual(wflvl1.organization, self.tola_user.organization)
        self.assertEqual(wflvl1.user_access.all().count(), 1)
        self.assertEqual(wflvl1.user_access.first(), self.tola_user)

    def test_create_workflowlevel1_normal_user(self):
        data = {'name': 'Save the Children'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user

        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)

    def test_create_workflowlevel1_uuid_is_self_generated(self):
        data = {
            'name': 'Save the Children',
            'level1_uuid': '75e4c912-4149-11e8-842f-0ed5f89f718b'
        }
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data['level1_uuid'],
                            '75e4c912-4149-11e8-842f-0ed5f89f718b')


class WorkflowLevel1UpdateViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()
        factories.Group()

    def test_update_unexisting_workflowlevel1(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        data = {'salary': '10'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'update'})
        response = view(request, pk=288)
        self.assertEqual(response.status_code, 404)

    def test_update_workflowlevel1_superuser(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        wflvl1 = factories.WorkflowLevel1()
        data = {'name': 'Save the Lennons'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'update'})
        response = view(request, pk=wflvl1.pk)
        self.assertEqual(response.status_code, 200)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertEquals(wflvl1.name, data['name'])

    def test_update_workflowlevel1_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        data = {'name': 'Save the Lennons'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'update'})
        response = view(request, pk=wflvl1.pk)
        self.assertEqual(response.status_code, 200)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertEquals(wflvl1.name, data['name'])

    def test_update_workflowlevel1_different_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wflvl1 = factories.WorkflowLevel1(
            organization=factories.Organization(name='Other Org'))
        data = {'name': 'Save the Lennons'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'update'})
        response = view(request, pk=wflvl1.pk)
        self.assertEqual(response.status_code, 403)

    def test_update_workflowlevel1_program_admin(self):
        data = {'name': 'Save the Children'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)

        data = {'name': 'Save the Lennons'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'update'})
        response = view(request, pk=response.data['id'])
        self.assertEqual(response.status_code, 200)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertEquals(wflvl1.name, data['name'])

    def test_update_workflowlevel1_program_admin_json(self):
        data = {'name': 'Save the Children'}
        request = self.factory.post('/api/workflowlevel1/', json.dumps(data),
                                    content_type='application/json')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)

        data = {'name': 'Save the Lennons'}
        request = self.factory.post('/api/workflowlevel1/', json.dumps(data),
                                    content_type='application/json')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'update'})
        response = view(request, pk=response.data['id'])
        self.assertEqual(response.status_code, 200)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertEquals(wflvl1.name, data['name'])

    def test_update_workflowlevel1_program_team(self):
        wflvl1 = factories.WorkflowLevel1()
        group_program_team = factories.Group(name=ROLE_PROGRAM_TEAM)
        wflvl1.organization = self.tola_user.organization
        wflvl1.user_access.add(self.tola_user)
        wflvl1.save()
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user, workflowlevel1=wflvl1,
            role=group_program_team)

        data = {'name': 'Save the Lennons'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'update'})
        response = view(request, pk=wflvl1.pk)
        self.assertEqual(response.status_code, 200)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertEquals(wflvl1.name, data['name'])

    def test_update_workflowlevel1_same_org_different_program_team(self):
        wflvl1_other = factories.WorkflowLevel1()
        group_program_team = factories.Group(name=ROLE_PROGRAM_TEAM)
        wflvl1_other.organization = self.tola_user.organization
        wflvl1_other.user_access.add(self.tola_user)
        wflvl1_other.save()
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user, workflowlevel1=wflvl1_other,
            role=group_program_team)

        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)

        data = {'name': 'Save the Lennons'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'update'})
        response = view(request, pk=wflvl1.pk)
        self.assertEqual(response.status_code, 403)

    def test_update_workflowlevel1_uuid_is_self_generated(self):
        data = {'name': 'Save the Children'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)
        first_level1_uuid = response.data['level1_uuid']
        data = {'name': 'Save the Children',
                'level1_uuid': 'fb6cf416-4148-11e8-842f-0ed5f89f718b'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'update'})
        response = view(request, pk=response.data['id'])
        self.assertEqual(response.status_code, 200)

        wflvl1 = WorkflowLevel1.objects.get(pk=response.data['id'])
        self.assertNotEqual(wflvl1.level1_uuid,
                            'fb6cf416-4148-11e8-842f-0ed5f89f718b')
        self.assertEqual(wflvl1.level1_uuid, first_level1_uuid)


class WorkflowLevel1DeleteViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()
        factories.Group()

    def test_delete_workflowlevel1_superuser(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        wflvl1 = factories.WorkflowLevel1()
        request = self.factory.delete('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=wflvl1.pk)
        self.assertEquals(response.status_code, 204)
        self.assertRaises(
            WorkflowLevel1.DoesNotExist,
            WorkflowLevel1.objects.get, pk=wflvl1.pk)

    def test_delete_workflowlevel1_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        request = self.factory.delete('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=wflvl1.pk)
        self.assertEquals(response.status_code, 204)
        self.assertRaises(
            WorkflowLevel1.DoesNotExist,
            WorkflowLevel1.objects.get, pk=wflvl1.pk)

    def test_delete_workflowlevel1_different_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        org_other = factories.Organization(name='Other Org')
        wflvl1 = factories.WorkflowLevel1(organization=org_other)
        request = self.factory.delete('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=wflvl1.pk)
        self.assertEquals(response.status_code, 403)
        WorkflowLevel1.objects.get(pk=wflvl1.pk)

    def test_delete_workflowlevel1_program_admin(self):
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            partner_org=self.tola_user.organization,
            role=factories.Group(name=ROLE_PROGRAM_ADMIN))

        # Create a program
        data = {'name': 'Save the Children'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)

        # Delete the program created before
        request = self.factory.delete('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'delete': 'destroy'})
        view(request, pk=response.data['id'])
        self.assertRaises(
            WorkflowLevel1.DoesNotExist,
            WorkflowLevel1.objects.get, pk=response.data['id'])

    def test_delete_workflowlevel1_different_org(self):
        group_other = factories.Group(name='other')
        self.tola_user.user.groups.add(group_other)

        wflvl1 = factories.WorkflowLevel1()
        request = self.factory.delete('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=wflvl1.pk)
        self.assertEquals(response.status_code, 403)
        WorkflowLevel1.objects.get(pk=wflvl1.pk)

    def test_delete_workflowlevel1_normal_user(self):
        wflvl1 = factories.WorkflowLevel1()
        request = self.factory.delete('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=wflvl1.pk)
        self.assertEquals(response.status_code, 403)
        WorkflowLevel1.objects.get(pk=wflvl1.pk)

    def test_delete_workflowlevel1_program_admin_just_one(self):
        # Create a program
        data = {'name': 'Save the Pandas'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)
        first_program_id = response.data['id']

        # Create another program
        data = {'name': 'Save the Children'}
        request = self.factory.post('/api/workflowlevel1/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'post': 'create'})
        response = view(request)

        # Delete only the latter program
        request = self.factory.delete('/api/workflowlevel1/')
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'delete': 'destroy'})
        view(request, pk=response.data['id'])
        self.assertRaises(
            WorkflowLevel1.DoesNotExist,
            WorkflowLevel1.objects.get, pk=response.data['id'])
        WorkflowLevel1.objects.get(pk=first_program_id)


class WorkflowLevel1FilterViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()
        factories.Group()

    def test_filter_workflowlevel1_superuser(self):
        wflvl1 = factories.WorkflowLevel1()
        factories.WorkflowLevel1(name='Population Health Initiative')

        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        request = self.factory.get('/api/workflowlevel1/?name=%s' %
                                   wflvl1.name)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wflvl1.name)

    def test_filter_workflowlevel1_org_admin(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        factories.WorkflowLevel1(name='Population Health Initiative',
                                 organization=self.tola_user.organization)
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        request = self.factory.get('/api/workflowlevel1/?name=%s' %
                                   wflvl1.name)
        request.user = self.tola_user.user
        view = WorkflowLevel1ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wflvl1.name)