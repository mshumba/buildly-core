import json
import re

from django.test import TestCase
import factories
from mock import patch, PropertyMock
from rest_framework.test import APIRequestFactory
from rest_framework.reverse import reverse
from workflow.models import (ApprovalWorkflow, WorkflowLevel2, WorkflowTeam,
                             ROLE_VIEW_ONLY, ROLE_ORGANIZATION_ADMIN,
                             ROLE_PROGRAM_ADMIN, ROLE_PROGRAM_TEAM)

from contact.tests import model_factories as mfactories
from ..views import WorkflowLevel2ViewSet


class WorkflowLevel2ListViewsTest(TestCase):
    def setUp(self):
        factories.WorkflowLevel2.create_batch(2)
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()

    def test_list_workflowlevel2_superuser(self):
        request = self.factory.get('/api/workflowlevel2/')
        request.user = factories.User.build(is_superuser=True,
                                            is_staff=True)
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_list_workflowlevel2_org_admin(self):
        request = self.factory.get('/api/workflowlevel2/')
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wflvl1 = factories.WorkflowLevel1()
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1)
        factories.WorkflowLevel2(workflowlevel1=wflvl1)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        wflvl1.organization = self.tola_user.organization
        wflvl1.save()
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['contact'], {})

    def test_list_workflowlevel2_program_admin(self):
        request = self.factory.get('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_ADMIN))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        factories.WorkflowLevel2(workflowlevel1=wflvl1)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_workflowlevel2_program_team(self):
        request = self.factory.get('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_TEAM))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        factories.WorkflowLevel2(workflowlevel1=wflvl1)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_workflowlevel2_view_only(self):
        request = self.factory.get('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_VIEW_ONLY))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        factories.WorkflowLevel2(workflowlevel1=wflvl1)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_workflowlevel2_products(self):
        request = self.factory.get('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        products = (
            factories.Product(name='Name1', type='Type1', reference_id='Ref1',
                              workflowlevel2=wflvl2),
            factories.Product(name='Name1', type='Type1', reference_id='Ref1',
                              workflowlevel2=wflvl2),
        )
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_VIEW_ONLY))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(len(response.data), 1)
        result = response.data[0]
        self.assertEqual(len(result['products']), len(products))
        self.assertEqual(result['products'][0]['name'], products[0].name)
        self.assertEqual(result['products'][0]['type'], products[0].type)
        self.assertEqual(result['products'][0]['reference_id'],
                         products[0].reference_id)
        self.assertEqual(result['products'][1]['name'], products[1].name)
        self.assertEqual(result['products'][1]['type'], products[1].type)
        self.assertEqual(result['products'][1]['reference_id'],
                         products[1].reference_id)

    def test_list_workflowlevel2_contact(self):
        request = self.factory.get('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        contact = mfactories.Contact(
            workflowlevel2_uuids=[str(wflvl2.level2_uuid)])
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_VIEW_ONLY))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(len(response.data), 1)
        result = response.data[0]
        contact_url = reverse('contact-detail', kwargs={'pk': contact.id},
                              request=request)
        self.assertEqual(
            result['contact'],
            {
                'id': contact.id,
                'uuid': contact.uuid,
                'url': contact_url,
                'first_name': contact.first_name,
                'middle_name': contact.middle_name,
                'last_name': contact.last_name,
                'title': contact.title,
                'contact_type': contact.contact_type,
                'customer_type': contact.customer_type,
                'company': contact.company,
            })

    @patch('api.views.DefaultCursorPagination.page_size',
           new_callable=PropertyMock)
    def test_list_workflowlevel2_pagination(self, page_size_mock):
        ''' For page_size 1 and pagination true, list wfl3 endpoint should
         return 1 wfl2 for each page'''
        # set page_size =1
        page_size_mock.return_value = 1
        wfl1_1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wfl2_1 = factories.WorkflowLevel2(name='1. wfl2',
                                          workflowlevel1=wfl1_1)
        wfl2_2 = factories.WorkflowLevel2(name='2. wfl2',
                                          workflowlevel1=wfl1_1)

        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        request = self.factory.get('?paginate=true')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)

        # page_size = 1, so it should return just one wfl1
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], wfl2_1.name)

        m = re.search('=(.*)&', response.data['next'])
        cursor = m.group(1)

        request = self.factory.get('?cursor={}&paginate=true'.format(
            cursor))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], wfl2_2.name)


class WorkflowLevel2CreateViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()
        factories.Group()

    def test_create_workflowlevel2_superuser(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1()
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)

        data = {'name': 'Help Syrians',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], u'Help Syrians')

    def test_create_workflowlevel2_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)

        data = {'name': 'Help Syrians',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], u'Help Syrians')

    def test_create_workflowlevel2_program_admin(self):
        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)
        tolauser_url = reverse('tolauser-detail',
                               kwargs={'pk': self.tola_user.id},
                               request=request)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_ADMIN))

        data = {'name': 'Help Syrians',
                'workflowlevel1': wflvl1_url,
                'staff_responsible': tolauser_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], u'Help Syrians')
        self.assertEqual(response.data['staff_responsible'], tolauser_url)

    def test_create_workflowlevel2_program_admin_json(self):
        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_ADMIN))

        data = {'name': 'Help Syrians',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', json.dumps(data),
                                    content_type='application/json')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], u'Help Syrians')

    def test_create_workflowlevel2_program_team(self):
        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_TEAM))

        data = {'name': 'Help Syrians',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], u'Help Syrians')

    def test_create_workflowlevel2_view_only(self):
        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_VIEW_ONLY))

        data = {'name': 'Help Syrians',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'create'})
        response = view(request)

        self.assertEqual(response.status_code, 403)

    def test_create_workflowlevel2_uuid_is_self_generated(self):
        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_TEAM))

        data = {
            'name': 'Save the Children',
            'level2_uuid': '84a9888-4149-11e8-842f-0ed5f89f718b',
            'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'create'})
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data['level2_uuid'],
                            '84a9888-4149-11e8-842f-0ed5f89f718b')


class WorkflowLevel2UpdateViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()
        factories.Group()

    def test_update_unexisting_workflowlevel2(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        data = {'name': 'Community awareness program conducted to plant trees'}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'update'})
        response = view(request, pk=288)
        self.assertEqual(response.status_code, 404)

    def test_update_workflowlevel2_superuser(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1()
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)

        data = {'name': 'Community awareness program conducted to plant trees',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'update'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEqual(response.status_code, 200)

        workflowlevel2 = WorkflowLevel2.objects.get(pk=response.data['id'])
        self.assertEquals(workflowlevel2.name, data['name'])

    def test_update_workflowlevel2_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)

        data = {'name': 'Community awareness program conducted to plant trees',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'update'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEqual(response.status_code, 200)

        workflowlevel2 = WorkflowLevel2.objects.get(pk=response.data['id'])
        self.assertEquals(workflowlevel2.name, data['name'])

    def test_update_workflowlevel2_diff_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        request = self.factory.post('/api/workflowlevel2/')
        another_org = factories.Organization(name='Another Org')
        wflvl1 = factories.WorkflowLevel1(organization=another_org)
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)

        data = {'name': 'Community awareness program conducted to plant trees',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'update'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEqual(response.status_code, 403)

    def test_update_workflowlevel2_program_admin(self):
        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_ADMIN))
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)

        data = {'name': 'Community awareness program conducted to plant trees',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'update'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEqual(response.status_code, 200)

        workflowlevel2 = WorkflowLevel2.objects.get(pk=response.data['id'])
        self.assertEquals(workflowlevel2.name, data['name'])

    def test_update_workflowlevel2_program_admin_json(self):
        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_ADMIN))
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)

        data = {'name': 'Community awareness program conducted to plant trees',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/indicator/', json.dumps(data),
                                    content_type='application/json')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'update'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEqual(response.status_code, 200)

        workflowlevel2 = WorkflowLevel2.objects.get(pk=response.data['id'])
        self.assertEquals(workflowlevel2.name, data['name'])

    def test_update_workflowlevel2_program_team(self):
        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_TEAM))
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)

        data = {'name': 'Community awareness program conducted to plant trees',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'update'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEqual(response.status_code, 200)

        workflowlevel2 = WorkflowLevel2.objects.get(pk=response.data['id'])
        self.assertEquals(workflowlevel2.name, data['name'])

    def test_update_workflowlevel2_view_only(self):
        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_VIEW_ONLY))
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)

        data = {'name': 'Community awareness program conducted to plant trees',
                'workflowlevel1': wflvl1_url}

        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'update'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEqual(response.status_code, 403)

    def test_update_workflowlevel2_uuid_is_self_generated(self):
        request = self.factory.post('/api/workflowlevel2/')
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_TEAM))
        wflvl1_url = reverse('workflowlevel1-detail',
                             kwargs={'pk': wflvl1.id},
                             request=request)

        data = {'name': 'Community awareness program conducted to plant trees',
                'workflowlevel1': wflvl1_url}
        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'create'})
        response = view(request)
        first_level2_uuid = response.data['level2_uuid']
        data = {'name': 'Community awareness program conducted to plant trees',
                'workflowlevel1': wflvl1_url,
                'level2_uuid': '84a9888-4149-11e8-842f-0ed5f89f718b'}
        request = self.factory.post('/api/workflowlevel2/', data)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'post': 'update'})
        response = view(request, pk=response.data['id'])
        self.assertEqual(response.status_code, 200)

        wflvl2 = WorkflowLevel2.objects.get(pk=response.data['id'])
        self.assertNotEqual(wflvl2.level2_uuid,
                            '84a9888-4149-11e8-842f-0ed5f89f718b')
        self.assertEqual(wflvl2.level2_uuid, first_level2_uuid)


class WorkflowLevel2DeleteViewsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()
        factories.Group()

    def test_delete_workflowlevel2_superuser(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        workflowlevel2 = factories.WorkflowLevel2()
        request = self.factory.delete('/api/workflowlevel2/')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEquals(response.status_code, 204)
        self.assertRaises(
            WorkflowLevel2.DoesNotExist,
            WorkflowLevel2.objects.get, pk=workflowlevel2.pk)

    def test_delete_workflowlevel2_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)

        request = self.factory.delete('/api/workflowlevel2/')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEquals(response.status_code, 204)
        self.assertRaises(
            WorkflowLevel2.DoesNotExist,
            WorkflowLevel2.objects.get, pk=workflowlevel2.pk)

    def test_delete_workflowlevel2_diff_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        another_org = factories.Organization(name='Another Org')
        wflvl1 = factories.WorkflowLevel1(organization=another_org)
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)

        request = self.factory.delete('/api/workflowlevel2/')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEquals(response.status_code, 403)
        WorkflowLevel2.objects.get(pk=workflowlevel2.pk)

    def test_delete_workflowlevel2_program_admin(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_ADMIN))
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)

        request = self.factory.delete('/api/workflowlevel2/')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEquals(response.status_code, 204)
        self.assertRaises(
            WorkflowLevel2.DoesNotExist,
            WorkflowLevel2.objects.get, pk=workflowlevel2.pk)

    def test_delete_workflowlevel2_diff_org(self):
        another_org = factories.Organization(name='Another Org')
        wflvl1 = factories.WorkflowLevel1(organization=another_org)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_ADMIN))
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)

        request = self.factory.delete('/api/workflowlevel2/')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEquals(response.status_code, 403)
        WorkflowLevel2.objects.get(pk=workflowlevel2.pk)

    def test_delete_workflowlevel2_program_team(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_PROGRAM_TEAM))
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)

        request = self.factory.delete('/api/workflowlevel2/')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEquals(response.status_code, 403)
        WorkflowLevel2.objects.get(pk=workflowlevel2.pk)

    def test_delete_workflowlevel2_view_only(self):
        wflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wflvl1,
            role=factories.Group(name=ROLE_VIEW_ONLY))
        workflowlevel2 = factories.WorkflowLevel2(workflowlevel1=wflvl1)

        request = self.factory.delete('/api/workflowlevel2/')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEquals(response.status_code, 403)
        WorkflowLevel2.objects.get(pk=workflowlevel2.pk)

    def test_delete_workflowlevel2_normal_user(self):
        workflowlevel2 = factories.WorkflowLevel2()
        request = self.factory.delete('/api/workflowlevel2/')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'delete': 'destroy'})
        response = view(request, pk=workflowlevel2.pk)
        self.assertEquals(response.status_code, 403)
        WorkflowLevel2.objects.get(pk=workflowlevel2.pk)


class WorkflowLevel2FilterViewsTest(TestCase):
    def setUp(self):
        factories.Organization(id=1)
        self.factory = APIRequestFactory()
        self.tola_user = factories.CoreUser()

    def test_filter_workflowlevel2_wkflvl1_country_superuser(self):
        self.tola_user.user.is_staff = True
        self.tola_user.user.is_superuser = True
        self.tola_user.user.save()

        country1 = factories.Country(country='Brazil', code='BR')
        country2 = factories.Country(country='Germany', code='DE')
        wkflvl1_1 = factories.WorkflowLevel1(country=[country1])
        wkflvl1_2 = factories.WorkflowLevel1(country=[country2])
        wkflvl2 = factories.WorkflowLevel2(workflowlevel1=wkflvl1_1)
        factories.WorkflowLevel2(
            name='Develop brief survey', workflowlevel1=wkflvl1_2)

        request = self.factory.get(
            '/api/workflowlevel2/?workflowlevel1__country__country=%s'
            % country1.country)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wkflvl2.name)

    def test_filter_workflowlevel2_wkflvl1_name_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wkflvl1_1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wkflvl1_2 = factories.WorkflowLevel1(
            name='Construction Project',
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1_1)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1_2)
        wkflvl2 = factories.WorkflowLevel2(workflowlevel1=wkflvl1_1)
        factories.WorkflowLevel2(
            name='Develop brief survey', workflowlevel1=wkflvl1_2)

        request = self.factory.get(
            '/api/workflowlevel2/?workflowlevel1__name=%s'
            % wkflvl1_1.name)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wkflvl2.name)

    def test_filter_workflowlevel2_wkflvl1_id_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wkflvl1_1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        wkflvl1_2 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1_1)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1_2)
        wkflvl2 = factories.WorkflowLevel2(workflowlevel1=wkflvl1_1)
        factories.WorkflowLevel2(
            name='Develop brief survey', workflowlevel1=wkflvl1_2)

        request = self.factory.get(
            '/api/workflowlevel2/?workflowlevel1__id=%s'
            % wkflvl1_1.pk)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wkflvl2.name)

    def test_filter_workflowlevel2_level2_uuid_org_admin(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wkflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1)
        wkflvl2 = factories.WorkflowLevel2(
            level2_uuid=111, workflowlevel1=wkflvl1)
        factories.WorkflowLevel2(
            name='Develop brief survey', level2_uuid=222,
            workflowlevel1=wkflvl1)

        request = self.factory.get(
            '/api/workflowlevel2/?level2_uuid=%s'
            % wkflvl2.level2_uuid)
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wkflvl2.name)

    def test_filter_workflowlevel2_progress(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wkflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1)
        wkflvl2 = factories.WorkflowLevel2(
            level2_uuid=111, workflowlevel1=wkflvl1,
            progress=WorkflowLevel2.PROGRESS_OPEN)
        factories.WorkflowLevel2(
            name='Develop brief survey', level2_uuid=222,
            workflowlevel1=wkflvl1,
            progress=WorkflowLevel2.PROGRESS_CLOSED)

        request = self.factory.get(
            '/api/workflowlevel2/?progress={}'.format(
                WorkflowLevel2.PROGRESS_OPEN))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wkflvl2.name)

    def test_filter_workflowlevel2_staff_responsible(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wkflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1)
        wkflvl2 = factories.WorkflowLevel2(
            workflowlevel1=wkflvl1,
            staff_responsible=self.tola_user)
        factories.WorkflowLevel2(
            name='Develop brief survey',
            workflowlevel1=wkflvl1)

        request = self.factory.get(
            '/api/workflowlevel2/?staff_responsible={}'.format(
                self.tola_user.id))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wkflvl2.name)

    def test_filter_workflowlevel2_approval_status(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wkflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1)
        wkflvl2 = factories.WorkflowLevel2(
            level2_uuid=111, workflowlevel1=wkflvl1)
        factories.WorkflowLevel2(
            name='Develop brief survey', level2_uuid=222,
            workflowlevel1=wkflvl1)

        approval = factories.ApprovalWorkflow(
            assigned_to=self.tola_user, requested_from=self.tola_user,
            status=ApprovalWorkflow.STATUS_OPEN)
        wkflvl2.approval.add(approval)

        request = self.factory.get(
            '/api/workflowlevel2/?approval__status={}'.format(
                ApprovalWorkflow.STATUS_OPEN))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wkflvl2.name)

    def test_filter_workflowlevel2_approval_assigned_to(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wkflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1)
        wkflvl2 = factories.WorkflowLevel2(
            level2_uuid=111, workflowlevel1=wkflvl1)
        factories.WorkflowLevel2(
            name='Develop brief survey', level2_uuid=222,
            workflowlevel1=wkflvl1)

        approval = factories.ApprovalWorkflow(
            assigned_to=self.tola_user, requested_from=self.tola_user,
            status=ApprovalWorkflow.STATUS_OPEN)
        wkflvl2.approval.add(approval)

        request = self.factory.get(
            '/api/workflowlevel2/?approval__assigned_to={}'.format(
                self.tola_user.id))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wkflvl2.name)

    def test_filter_workflowlevel2_nested_models(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wkflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1)
        wkflvl2 = factories.WorkflowLevel2(
            level2_uuid=111, workflowlevel1=wkflvl1)

        approval = factories.ApprovalWorkflow(
            assigned_to=self.tola_user, requested_from=self.tola_user,
            status=ApprovalWorkflow.STATUS_OPEN)
        wkflvl2.approval.add(approval)

        request = self.factory.get('/api/workflowlevel2/?nested_models=1')
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

        result_approvals = response.data[0]['approval']
        self.assertEqual(result_approvals[0]['id'], approval.id)

    def test_filter_workflowlevel2_nested_models_combine_filters(self):
        group_org_admin = factories.Group(name=ROLE_ORGANIZATION_ADMIN)
        self.tola_user.user.groups.add(group_org_admin)

        wkflvl1 = factories.WorkflowLevel1(
            organization=self.tola_user.organization)
        WorkflowTeam.objects.create(
            workflow_user=self.tola_user,
            workflowlevel1=wkflvl1)
        wkflvl2 = factories.WorkflowLevel2(
            level2_uuid=111, workflowlevel1=wkflvl1)
        factories.WorkflowLevel2(
            name='Develop brief survey', level2_uuid=222,
            workflowlevel1=wkflvl1)

        approval = factories.ApprovalWorkflow(
            assigned_to=self.tola_user, requested_from=self.tola_user,
            status=ApprovalWorkflow.STATUS_OPEN)
        wkflvl2.approval.add(approval)

        request = self.factory.get(
            '/api/workflowlevel2/?approval__status={}&nested_models=1'.format(
                ApprovalWorkflow.STATUS_OPEN))
        request.user = self.tola_user.user
        view = WorkflowLevel2ViewSet.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], wkflvl2.name)

        result_approvals = response.data[0]['approval']
        self.assertEqual(result_approvals[0]['id'], approval.id)