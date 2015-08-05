# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest2


class TestSchemaField(unittest2.TestCase):

    def _getTargetClass(self):
        from gcloud.bigquery.table import SchemaField
        return SchemaField

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_ctor_defaults(self):
        field = self._makeOne('test', 'STRING')
        self.assertEqual(field.name, 'test')
        self.assertEqual(field.field_type, 'STRING')
        self.assertEqual(field.mode, 'NULLABLE')
        self.assertEqual(field.description, None)
        self.assertEqual(field.fields, None)

    def test_ctor_explicit(self):
        field = self._makeOne('test', 'STRING', mode='REQUIRED',
                              description='Testing')
        self.assertEqual(field.name, 'test')
        self.assertEqual(field.field_type, 'STRING')
        self.assertEqual(field.mode, 'REQUIRED')
        self.assertEqual(field.description, 'Testing')
        self.assertEqual(field.fields, None)

    def test_ctor_subfields(self):
        field = self._makeOne('phone_number', 'RECORD',
                              fields=[self._makeOne('area_code', 'STRING'),
                                      self._makeOne('local_number', 'STRING')])
        self.assertEqual(field.name, 'phone_number')
        self.assertEqual(field.field_type, 'RECORD')
        self.assertEqual(field.mode, 'NULLABLE')
        self.assertEqual(field.description, None)
        self.assertEqual(len(field.fields), 2)
        self.assertEqual(field.fields[0].name, 'area_code')
        self.assertEqual(field.fields[0].field_type, 'STRING')
        self.assertEqual(field.fields[0].mode, 'NULLABLE')
        self.assertEqual(field.fields[0].description, None)
        self.assertEqual(field.fields[0].fields, None)
        self.assertEqual(field.fields[1].name, 'local_number')
        self.assertEqual(field.fields[1].field_type, 'STRING')
        self.assertEqual(field.fields[1].mode, 'NULLABLE')
        self.assertEqual(field.fields[1].description, None)
        self.assertEqual(field.fields[1].fields, None)


class TestTable(unittest2.TestCase):
    PROJECT = 'project'
    DS_NAME = 'dataset-name'
    TABLE_NAME = 'table-name'

    def _getTargetClass(self):
        from gcloud.bigquery.table import Table
        return Table

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _makeResource(self):
        import datetime
        import pytz
        self.WHEN_TS = 1437767599.006
        self.WHEN = datetime.datetime.utcfromtimestamp(self.WHEN_TS).replace(
            tzinfo=pytz.UTC)
        self.ETAG = 'ETAG'
        self.TABLE_ID = '%s:%s:%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        self.RESOURCE_URL = 'http://example.com/path/to/resource'
        self.NUM_BYTES = 12345
        self.NUM_ROWS = 67
        return {
            'creationTime': self.WHEN_TS * 1000,
            'tableReference':
                {'projectId': self.PROJECT,
                 'datasetId': self.DS_NAME,
                 'tableId': self.TABLE_NAME},
            'schema': {'fields': [
                {'name': 'full_name', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'age', 'type': 'INTEGER', 'mode': 'REQUIRED'}]},
            'etag': 'ETAG',
            'id': self.TABLE_ID,
            'lastModifiedTime': self.WHEN_TS * 1000,
            'location': 'US',
            'selfLink': self.RESOURCE_URL,
            'numRows': self.NUM_ROWS,
            'numBytes': self.NUM_BYTES,
            'type': 'TABLE',
        }

    def _verifyResourceProperties(self, table, resource):
        self.assertEqual(table.created, self.WHEN)
        self.assertEqual(table.etag, self.ETAG)
        self.assertEqual(table.num_rows, self.NUM_ROWS)
        self.assertEqual(table.num_bytes, self.NUM_BYTES)
        self.assertEqual(table.self_link, self.RESOURCE_URL)
        self.assertEqual(table.table_id, self.TABLE_ID)
        self.assertEqual(table.table_type,
                         'TABLE' if 'view' not in resource else 'VIEW')

        if 'expirationTime' in resource:
            self.assertEqual(table.expires, self.EXP_TIME)
        else:
            self.assertEqual(table.expires, None)
        self.assertEqual(table.description, resource.get('description'))
        self.assertEqual(table.friendly_name, resource.get('friendlyName'))
        self.assertEqual(table.location, resource.get('location'))
        if 'view' in resource:
            self.assertEqual(table.view_query, resource['view']['query'])
        else:
            self.assertEqual(table.view_query, None)

    def test_ctor(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        self.assertEqual(table.name, self.TABLE_NAME)
        self.assertTrue(table._dataset is dataset)
        self.assertEqual(
            table.path,
            '/projects/%s/datasets/%s/tables/%s' % (
                self.PROJECT, self.DS_NAME, self.TABLE_NAME))
        self.assertEqual(table.schema, [])

        self.assertEqual(table.created, None)
        self.assertEqual(table.etag, None)
        self.assertEqual(table.modified, None)
        self.assertEqual(table.num_bytes, None)
        self.assertEqual(table.num_rows, None)
        self.assertEqual(table.self_link, None)
        self.assertEqual(table.table_id, None)
        self.assertEqual(table.table_type, None)

        self.assertEqual(table.description, None)
        self.assertEqual(table.expires, None)
        self.assertEqual(table.friendly_name, None)
        self.assertEqual(table.location, None)
        self.assertEqual(table.view_query, None)

    def test_ctor_w_schema(self):
        from gcloud.bigquery.table import SchemaField
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        full_name = SchemaField('full_name', 'STRING', mode='REQUIRED')
        age = SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = self._makeOne(self.TABLE_NAME, dataset,
                              schema=[full_name, age])
        self.assertEqual(table.schema, [full_name, age])

    def test_schema_setter_non_list(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        with self.assertRaises(TypeError):
            table.schema = object()

    def test_schema_setter_invalid_field(self):
        from gcloud.bigquery.table import SchemaField
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        full_name = SchemaField('full_name', 'STRING', mode='REQUIRED')
        with self.assertRaises(ValueError):
            table.schema = [full_name, object()]

    def test_schema_setter(self):
        from gcloud.bigquery.table import SchemaField
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        full_name = SchemaField('full_name', 'STRING', mode='REQUIRED')
        age = SchemaField('age', 'INTEGER', mode='REQUIRED')
        table.schema = [full_name, age]
        self.assertEqual(table.schema, [full_name, age])

    def test_props_set_by_server(self):
        import datetime
        import pytz
        from gcloud.bigquery._helpers import _millis
        CREATED = datetime.datetime(2015, 7, 29, 12, 13, 22, tzinfo=pytz.utc)
        MODIFIED = datetime.datetime(2015, 7, 29, 14, 47, 15, tzinfo=pytz.utc)
        TABLE_ID = '%s:%s:%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        URL = 'http://example.com/projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        table._properties['creationTime'] = _millis(CREATED)
        table._properties['etag'] = 'ETAG'
        table._properties['lastModifiedTime'] = _millis(MODIFIED)
        table._properties['numBytes'] = 12345
        table._properties['numRows'] = 66
        table._properties['selfLink'] = URL
        table._properties['id'] = TABLE_ID
        table._properties['type'] = 'TABLE'

        self.assertEqual(table.created, CREATED)
        self.assertEqual(table.etag, 'ETAG')
        self.assertEqual(table.modified, MODIFIED)
        self.assertEqual(table.num_bytes, 12345)
        self.assertEqual(table.num_rows, 66)
        self.assertEqual(table.self_link, URL)
        self.assertEqual(table.table_id, TABLE_ID)
        self.assertEqual(table.table_type, 'TABLE')

    def test_description_setter_bad_value(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        with self.assertRaises(ValueError):
            table.description = 12345

    def test_description_setter(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        table.description = 'DESCRIPTION'
        self.assertEqual(table.description, 'DESCRIPTION')

    def test_expires_setter_bad_value(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        with self.assertRaises(ValueError):
            table.expires = object()

    def test_expires_setter(self):
        import datetime
        import pytz
        WHEN = datetime.datetime(2015, 7, 28, 16, 39, tzinfo=pytz.utc)
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        table.expires = WHEN
        self.assertEqual(table.expires, WHEN)

    def test_friendly_name_setter_bad_value(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        with self.assertRaises(ValueError):
            table.friendly_name = 12345

    def test_friendly_name_setter(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        table.friendly_name = 'FRIENDLY'
        self.assertEqual(table.friendly_name, 'FRIENDLY')

    def test_location_setter_bad_value(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        with self.assertRaises(ValueError):
            table.location = 12345

    def test_location_setter(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        table.location = 'LOCATION'
        self.assertEqual(table.location, 'LOCATION')

    def test_view_query_setter_bad_value(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        with self.assertRaises(ValueError):
            table.view_query = 12345

    def test_view_query_setter(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        table.view_query = 'select * from foo'
        self.assertEqual(table.view_query, 'select * from foo')

    def test_view_query_deleter(self):
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset)
        table.view_query = 'select * from foo'
        del table.view_query
        self.assertEqual(table.view_query, None)

    def test__build_schema_resource_defaults(self):
        from gcloud.bigquery.table import SchemaField
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        full_name = SchemaField('full_name', 'STRING', mode='REQUIRED')
        age = SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = self._makeOne(self.TABLE_NAME, dataset,
                              schema=[full_name, age])
        resource = table._build_schema_resource()
        self.assertEqual(len(resource), 2)
        self.assertEqual(resource[0],
                         {'name': 'full_name',
                          'type': 'STRING',
                          'mode': 'REQUIRED'})
        self.assertEqual(resource[1],
                         {'name': 'age',
                          'type': 'INTEGER',
                          'mode': 'REQUIRED'})

    def test__build_schema_resource_w_description(self):
        from gcloud.bigquery.table import SchemaField
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        DESCRIPTION = 'DESCRIPTION'
        full_name = SchemaField('full_name', 'STRING', mode='REQUIRED',
                                description=DESCRIPTION)
        age = SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = self._makeOne(self.TABLE_NAME, dataset,
                              schema=[full_name, age])
        resource = table._build_schema_resource()
        self.assertEqual(len(resource), 2)
        self.assertEqual(resource[0],
                         {'name': 'full_name',
                          'type': 'STRING',
                          'mode': 'REQUIRED',
                          'description': DESCRIPTION})
        self.assertEqual(resource[1],
                         {'name': 'age',
                          'type': 'INTEGER',
                          'mode': 'REQUIRED'})

    def test__build_schema_resource_w_subfields(self):
        from gcloud.bigquery.table import SchemaField
        client = _Client(self.PROJECT)
        dataset = _Dataset(client)
        full_name = SchemaField('full_name', 'STRING', mode='REQUIRED')
        ph_type = SchemaField('type', 'STRING', 'REQUIRED')
        ph_num = SchemaField('number', 'STRING', 'REQUIRED')
        phone = SchemaField('phone', 'RECORD', mode='REPEATABLE',
                            fields=[ph_type, ph_num])
        table = self._makeOne(self.TABLE_NAME, dataset,
                              schema=[full_name, phone])
        resource = table._build_schema_resource()
        self.assertEqual(len(resource), 2)
        self.assertEqual(resource[0],
                         {'name': 'full_name',
                          'type': 'STRING',
                          'mode': 'REQUIRED'})
        self.assertEqual(resource[1],
                         {'name': 'phone',
                          'type': 'RECORD',
                          'mode': 'REPEATABLE',
                          'fields': [{'name': 'type',
                                      'type': 'STRING',
                                      'mode': 'REQUIRED'},
                                     {'name': 'number',
                                      'type': 'STRING',
                                      'mode': 'REQUIRED'}]})

    def test_create_w_bound_client(self):
        from gcloud.bigquery.table import SchemaField
        PATH = 'projects/%s/datasets/%s/tables' % (self.PROJECT, self.DS_NAME)
        RESOURCE = self._makeResource()
        conn = _Connection(RESOURCE)
        client = _Client(project=self.PROJECT, connection=conn)
        dataset = _Dataset(client)
        full_name = SchemaField('full_name', 'STRING', mode='REQUIRED')
        age = SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = self._makeOne(self.TABLE_NAME, dataset,
                              schema=[full_name, age])

        table.create()

        self.assertEqual(len(conn._requested), 1)
        req = conn._requested[0]
        self.assertEqual(req['method'], 'POST')
        self.assertEqual(req['path'], '/%s' % PATH)
        SENT = {
            'tableReference': {
                'projectId': self.PROJECT,
                'datasetId': self.DS_NAME,
                'tableId': self.TABLE_NAME},
            'schema': {'fields': [
                {'name': 'full_name', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'age', 'type': 'INTEGER', 'mode': 'REQUIRED'}]},
        }
        self.assertEqual(req['data'], SENT)
        self._verifyResourceProperties(table, RESOURCE)

    def test_create_w_alternate_client(self):
        import datetime
        import pytz
        from gcloud.bigquery.table import SchemaField
        from gcloud.bigquery._helpers import _millis
        PATH = 'projects/%s/datasets/%s/tables' % (self.PROJECT, self.DS_NAME)
        DESCRIPTION = 'DESCRIPTION'
        TITLE = 'TITLE'
        QUERY = 'select fullname, age from person_ages'
        RESOURCE = self._makeResource()
        RESOURCE['description'] = DESCRIPTION
        RESOURCE['friendlyName'] = TITLE
        self.EXP_TIME = datetime.datetime(2015, 8, 1, 23, 59, 59,
                                          tzinfo=pytz.utc)
        RESOURCE['expirationTime'] = _millis(self.EXP_TIME)
        RESOURCE['view'] = {}
        RESOURCE['view']['query'] = QUERY
        RESOURCE['type'] = 'VIEW'
        conn1 = _Connection()
        client1 = _Client(project=self.PROJECT, connection=conn1)
        conn2 = _Connection(RESOURCE)
        client2 = _Client(project=self.PROJECT, connection=conn2)
        dataset = _Dataset(client=client1)
        full_name = SchemaField('full_name', 'STRING', mode='REQUIRED')
        age = SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = self._makeOne(self.TABLE_NAME, dataset=dataset,
                              schema=[full_name, age])
        table.friendly_name = TITLE
        table.description = DESCRIPTION
        table.view_query = QUERY

        table.create(client=client2)

        self.assertEqual(len(conn1._requested), 0)
        self.assertEqual(len(conn2._requested), 1)
        req = conn2._requested[0]
        self.assertEqual(req['method'], 'POST')
        self.assertEqual(req['path'], '/%s' % PATH)
        SENT = {
            'tableReference': {
                'projectId': self.PROJECT,
                'datasetId': self.DS_NAME,
                'tableId': self.TABLE_NAME},
            'schema': {'fields': [
                {'name': 'full_name', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'age', 'type': 'INTEGER', 'mode': 'REQUIRED'}]},
            'description': DESCRIPTION,
            'friendlyName': TITLE,
            'view': {'query': QUERY},
        }
        self.assertEqual(req['data'], SENT)
        self._verifyResourceProperties(table, RESOURCE)

    def test_exists_miss_w_bound_client(self):
        PATH = 'projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        conn = _Connection()
        client = _Client(project=self.PROJECT, connection=conn)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset=dataset)

        self.assertFalse(table.exists())

        self.assertEqual(len(conn._requested), 1)
        req = conn._requested[0]
        self.assertEqual(req['method'], 'GET')
        self.assertEqual(req['path'], '/%s' % PATH)
        self.assertEqual(req['query_params'], {'fields': 'id'})

    def test_exists_hit_w_alternate_client(self):
        PATH = 'projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        conn1 = _Connection()
        client1 = _Client(project=self.PROJECT, connection=conn1)
        conn2 = _Connection({})
        client2 = _Client(project=self.PROJECT, connection=conn2)
        dataset = _Dataset(client1)
        table = self._makeOne(self.TABLE_NAME, dataset=dataset)

        self.assertTrue(table.exists(client=client2))

        self.assertEqual(len(conn1._requested), 0)
        self.assertEqual(len(conn2._requested), 1)
        req = conn2._requested[0]
        self.assertEqual(req['method'], 'GET')
        self.assertEqual(req['path'], '/%s' % PATH)
        self.assertEqual(req['query_params'], {'fields': 'id'})

    def test_reload_w_bound_client(self):
        PATH = 'projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        RESOURCE = self._makeResource()
        conn = _Connection(RESOURCE)
        client = _Client(project=self.PROJECT, connection=conn)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset=dataset)

        table.reload()

        self.assertEqual(len(conn._requested), 1)
        req = conn._requested[0]
        self.assertEqual(req['method'], 'GET')
        self.assertEqual(req['path'], '/%s' % PATH)
        self._verifyResourceProperties(table, RESOURCE)

    def test_reload_w_alternate_client(self):
        PATH = 'projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        RESOURCE = self._makeResource()
        conn1 = _Connection()
        client1 = _Client(project=self.PROJECT, connection=conn1)
        conn2 = _Connection(RESOURCE)
        client2 = _Client(project=self.PROJECT, connection=conn2)
        dataset = _Dataset(client1)
        table = self._makeOne(self.TABLE_NAME, dataset=dataset)

        table.reload(client=client2)

        self.assertEqual(len(conn1._requested), 0)
        self.assertEqual(len(conn2._requested), 1)
        req = conn2._requested[0]
        self.assertEqual(req['method'], 'GET')
        self.assertEqual(req['path'], '/%s' % PATH)
        self._verifyResourceProperties(table, RESOURCE)

    def test_patch_w_invalid_expiration(self):
        RESOURCE = self._makeResource()
        conn = _Connection(RESOURCE)
        client = _Client(project=self.PROJECT, connection=conn)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset=dataset)

        with self.assertRaises(ValueError):
            table.patch(expires='BOGUS')

    def test_patch_w_bound_client(self):
        PATH = 'projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        DESCRIPTION = 'DESCRIPTION'
        TITLE = 'TITLE'
        RESOURCE = self._makeResource()
        RESOURCE['description'] = DESCRIPTION
        RESOURCE['friendlyName'] = TITLE
        conn = _Connection(RESOURCE)
        client = _Client(project=self.PROJECT, connection=conn)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset=dataset)

        table.patch(description=DESCRIPTION,
                    friendly_name=TITLE,
                    view_query=None)

        self.assertEqual(len(conn._requested), 1)
        req = conn._requested[0]
        self.assertEqual(req['method'], 'PATCH')
        SENT = {
            'description': DESCRIPTION,
            'friendlyName': TITLE,
            'view': None,
        }
        self.assertEqual(req['data'], SENT)
        self.assertEqual(req['path'], '/%s' % PATH)
        self._verifyResourceProperties(table, RESOURCE)

    def test_patch_w_alternate_client(self):
        import datetime
        import pytz
        from gcloud.bigquery._helpers import _millis
        PATH = 'projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        QUERY = 'select fullname, age from person_ages'
        LOCATION = 'EU'
        RESOURCE = self._makeResource()
        RESOURCE['view'] = {'query': QUERY}
        RESOURCE['type'] = 'VIEW'
        RESOURCE['location'] = LOCATION
        self.EXP_TIME = datetime.datetime(2015, 8, 1, 23, 59, 59,
                                          tzinfo=pytz.utc)
        RESOURCE['expirationTime'] = _millis(self.EXP_TIME)
        conn1 = _Connection()
        client1 = _Client(project=self.PROJECT, connection=conn1)
        conn2 = _Connection(RESOURCE)
        client2 = _Client(project=self.PROJECT, connection=conn2)
        dataset = _Dataset(client1)
        table = self._makeOne(self.TABLE_NAME, dataset=dataset)

        table.patch(client=client2, view_query=QUERY, location=LOCATION,
                    expires=self.EXP_TIME)

        self.assertEqual(len(conn1._requested), 0)
        self.assertEqual(len(conn2._requested), 1)
        req = conn2._requested[0]
        self.assertEqual(req['method'], 'PATCH')
        self.assertEqual(req['path'], '/%s' % PATH)
        SENT = {
            'view': {'query': QUERY},
            'location': LOCATION,
            'expirationTime': _millis(self.EXP_TIME),
        }
        self.assertEqual(req['data'], SENT)
        self._verifyResourceProperties(table, RESOURCE)

    def test_update_w_bound_client(self):
        from gcloud.bigquery.table import SchemaField
        PATH = 'projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        DESCRIPTION = 'DESCRIPTION'
        TITLE = 'TITLE'
        RESOURCE = self._makeResource()
        RESOURCE['description'] = DESCRIPTION
        RESOURCE['friendlyName'] = TITLE
        conn = _Connection(RESOURCE)
        client = _Client(project=self.PROJECT, connection=conn)
        dataset = _Dataset(client)
        full_name = SchemaField('full_name', 'STRING', mode='REQUIRED')
        age = SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = self._makeOne(self.TABLE_NAME, dataset=dataset,
                              schema=[full_name, age])
        table.description = DESCRIPTION
        table.friendly_name = TITLE

        table.update()

        self.assertEqual(len(conn._requested), 1)
        req = conn._requested[0]
        self.assertEqual(req['method'], 'PUT')
        SENT = {
            'tableReference':
                {'projectId': self.PROJECT,
                 'datasetId': self.DS_NAME,
                 'tableId': self.TABLE_NAME},
            'schema': {'fields': [
                {'name': 'full_name', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'age', 'type': 'INTEGER', 'mode': 'REQUIRED'}]},
            'description': DESCRIPTION,
            'friendlyName': TITLE,
        }
        self.assertEqual(req['data'], SENT)
        self.assertEqual(req['path'], '/%s' % PATH)
        self._verifyResourceProperties(table, RESOURCE)

    def test_update_w_alternate_client(self):
        import datetime
        import pytz
        from gcloud.bigquery._helpers import _millis
        from gcloud.bigquery.table import SchemaField
        PATH = 'projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        DEF_TABLE_EXP = 12345
        LOCATION = 'EU'
        QUERY = 'select fullname, age from person_ages'
        RESOURCE = self._makeResource()
        RESOURCE['defaultTableExpirationMs'] = 12345
        RESOURCE['location'] = LOCATION
        self.EXP_TIME = datetime.datetime(2015, 8, 1, 23, 59, 59,
                                          tzinfo=pytz.utc)
        RESOURCE['expirationTime'] = _millis(self.EXP_TIME)
        RESOURCE['view'] = {'query': QUERY}
        RESOURCE['type'] = 'VIEW'
        conn1 = _Connection()
        client1 = _Client(project=self.PROJECT, connection=conn1)
        conn2 = _Connection(RESOURCE)
        client2 = _Client(project=self.PROJECT, connection=conn2)
        dataset = _Dataset(client1)
        full_name = SchemaField('full_name', 'STRING', mode='REQUIRED')
        age = SchemaField('age', 'INTEGER', mode='REQUIRED')
        table = self._makeOne(self.TABLE_NAME, dataset=dataset,
                              schema=[full_name, age])
        table.default_table_expiration_ms = DEF_TABLE_EXP
        table.location = LOCATION
        table.expires = self.EXP_TIME
        table.view_query = QUERY

        table.update(client=client2)

        self.assertEqual(len(conn1._requested), 0)
        self.assertEqual(len(conn2._requested), 1)
        req = conn2._requested[0]
        self.assertEqual(req['method'], 'PUT')
        self.assertEqual(req['path'], '/%s' % PATH)
        SENT = {
            'tableReference':
                {'projectId': self.PROJECT,
                 'datasetId': self.DS_NAME,
                 'tableId': self.TABLE_NAME},
            'schema': {'fields': [
                {'name': 'full_name', 'type': 'STRING', 'mode': 'REQUIRED'},
                {'name': 'age', 'type': 'INTEGER', 'mode': 'REQUIRED'}]},
            'expirationTime': _millis(self.EXP_TIME),
            'location': 'EU',
            'view': {'query': QUERY},
        }
        self.assertEqual(req['data'], SENT)
        self._verifyResourceProperties(table, RESOURCE)

    def test_delete_w_bound_client(self):
        PATH = 'projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        conn = _Connection({})
        client = _Client(project=self.PROJECT, connection=conn)
        dataset = _Dataset(client)
        table = self._makeOne(self.TABLE_NAME, dataset=dataset)

        table.delete()

        self.assertEqual(len(conn._requested), 1)
        req = conn._requested[0]
        self.assertEqual(req['method'], 'DELETE')
        self.assertEqual(req['path'], '/%s' % PATH)

    def test_delete_w_alternate_client(self):
        PATH = 'projects/%s/datasets/%s/tables/%s' % (
            self.PROJECT, self.DS_NAME, self.TABLE_NAME)
        conn1 = _Connection()
        client1 = _Client(project=self.PROJECT, connection=conn1)
        conn2 = _Connection({})
        client2 = _Client(project=self.PROJECT, connection=conn2)
        dataset = _Dataset(client1)
        table = self._makeOne(self.TABLE_NAME, dataset=dataset)

        table.delete(client=client2)

        self.assertEqual(len(conn1._requested), 0)
        self.assertEqual(len(conn2._requested), 1)
        req = conn2._requested[0]
        self.assertEqual(req['method'], 'DELETE')
        self.assertEqual(req['path'], '/%s' % PATH)


class _Client(object):

    def __init__(self, project='project', connection=None):
        self.project = project
        self.connection = connection


class _Dataset(object):

    def __init__(self, client, name=TestTable.DS_NAME):
        self._client = client
        self.name = name

    @property
    def path(self):
        return '/projects/%s/datasets/%s' % (
            self._client.project, self.name)

    @property
    def project(self):
        return self._client.project


class _Connection(object):

    def __init__(self, *responses):
        self._responses = responses
        self._requested = []

    def api_request(self, **kw):
        from gcloud.exceptions import NotFound
        self._requested.append(kw)

        try:
            response, self._responses = self._responses[0], self._responses[1:]
        except:
            raise NotFound('miss')
        else:
            return response
