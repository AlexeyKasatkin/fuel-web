# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json

from nailgun.api.models import AllowedNetworks
from nailgun.api.models import Cluster
from nailgun.api.models import NetworkAssignment
from nailgun.test.base import BaseIntegrationTest
from nailgun.test.base import reverse


class TestClusterHandlers(BaseIntegrationTest):

    def test_assigned_networks_when_node_added(self):
        mac = '123'
        meta = self.env.default_metadata()
        self.env.set_interfaces_in_meta(
            meta,
            [{'name': 'eth0', 'mac': mac},
             {'name': 'eth1', 'mac': '654'}])

        node = self.env.create_node(api=True, meta=meta, mac=mac)
        self.env.create_cluster(api=True, nodes=[node['id']])

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)

        self.assertEquals(resp.status, 200)

        response = json.loads(resp.body)

        for resp_nic in response:
            if resp_nic['mac'] == mac:
                self.assertEquals(len(resp_nic['assigned_networks']), 1)
            else:
                self.assertGreater(len(resp_nic['assigned_networks']), 0)

    def test_allowed_networks_when_node_added(self):
        mac = '123'
        meta = self.env.default_metadata()
        self.env.set_interfaces_in_meta(
            meta,
            [{'name': 'eth0', 'mac': mac},
             {'name': 'eth1', 'mac': 'abc'}])
        node = self.env.create_node(api=True, meta=meta, mac=mac)
        self.env.create_cluster(api=True, nodes=[node['id']])

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)

        for resp_nic in response:
            self.assertGreater(len(resp_nic['allowed_networks']), 0)

    def test_assignment_is_removed_when_delete_node_from_cluster(self):
        mac = '123'
        meta = self.env.default_metadata()
        self.env.set_interfaces_in_meta(
            meta,
            [{'name': 'eth0', 'mac': mac},
             {'name': 'eth1', 'mac': 'abc'}])
        node = self.env.create_node(api=True, meta=meta, mac=mac)
        cluster = self.env.create_cluster(api=True, nodes=[node['id']])
        resp = self.app.put(
            reverse('ClusterHandler', kwargs={'cluster_id': cluster['id']}),
            json.dumps({'nodes': []}),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        for resp_nic in response:
            self.assertEquals(resp_nic['assigned_networks'], [])
            self.assertEquals(resp_nic['allowed_networks'], [])

    def test_assignment_is_removed_when_delete_cluster(self):
        mac = '12364759'
        meta = self.env.default_metadata()
        self.env.set_interfaces_in_meta(
            meta,
            [{'name': 'eth0', 'mac': mac},
             {'name': 'eth1', 'mac': 'abc'}])
        node = self.env.create_node(api=True, meta=meta, mac=mac)
        cluster = self.env.create_cluster(api=True, nodes=[node['id']])
        cluster_db = self.db.query(Cluster).get(cluster['id'])
        self.db.delete(cluster_db)
        self.db.commit()

        net_assignment = self.db.query(NetworkAssignment).all()
        self.assertEquals(len(net_assignment), 0)
        allowed_nets = self.db.query(AllowedNetworks).all()
        self.assertEquals(len(allowed_nets), 0)


class TestNodeHandlers(BaseIntegrationTest):

    def test_network_assignment_when_node_created_and_added(self):
        cluster = self.env.create_cluster(api=True)
        mac = '123'
        meta = self.env.default_metadata()
        self.env.set_interfaces_in_meta(
            meta,
            [{'name': 'eth0', 'mac': mac},
             {'name': 'eth1', 'mac': '654'}])
        node = self.env.create_node(api=True, meta=meta, mac=mac,
                                    cluster_id=cluster['id'])
        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        for resp_nic in response:
            if resp_nic['mac'] == mac:
                self.assertEquals(len(resp_nic['assigned_networks']), 1)
            else:
                self.assertGreater(len(resp_nic['assigned_networks']), 0)
            self.assertGreater(len(resp_nic['allowed_networks']), 0)

    def test_network_assignment_when_node_added(self):
        cluster = self.env.create_cluster(api=True)
        mac = '123'
        meta = self.env.default_metadata()
        self.env.set_interfaces_in_meta(
            meta,
            [{'name': 'eth0', 'mac': mac},
             {'name': 'eth1', 'mac': 'abc'}])
        node = self.env.create_node(api=True, meta=meta, mac=mac)
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{'id': node['id'], 'cluster_id': cluster['id']}]),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        for resp_nic in response:
            if resp_nic['mac'] == mac:
                self.assertEquals(len(resp_nic['assigned_networks']), 1)
            else:
                self.assertGreater(len(resp_nic['assigned_networks']), 0)
            self.assertGreater(len(resp_nic['allowed_networks']), 0)

    def test_assignment_is_removed_when_delete_node_from_cluster(self):
        cluster = self.env.create_cluster(api=True)
        mac = '123'
        meta = self.env.default_metadata()
        self.env.set_interfaces_in_meta(
            meta,
            [{'name': 'eth0', 'mac': mac},
             {'name': 'eth1', 'mac': 'abc'}])
        node = self.env.create_node(api=True, meta=meta, mac=mac,
                                    cluster_id=cluster['id'])
        resp = self.app.put(
            reverse('NodeCollectionHandler'),
            json.dumps([{'id': node['id'], 'cluster_id': None}]),
            headers=self.default_headers
        )
        self.assertEquals(resp.status, 200)

        resp = self.app.get(
            reverse('NodeNICsHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers)
        self.assertEquals(resp.status, 200)
        response = json.loads(resp.body)
        for resp_nic in response:
            self.assertEquals(resp_nic['assigned_networks'], [])
            self.assertEquals(resp_nic['allowed_networks'], [])

    def test_getting_default_nic_information_for_node(self):
        cluster = self.env.create_cluster(api=True)
        macs = ('123', 'abc')
        meta = self.env.default_metadata()
        self.env.set_interfaces_in_meta(
            meta,
            [{'name': 'eth0', 'mac': macs[0]},
             {'name': 'eth1', 'mac': macs[1]}])
        node = self.env.create_node(api=True, meta=meta, mac=macs[0],
                                    cluster_id=cluster['id'])
        resp = self.app.get(
            reverse('NodeNICsDefaultHandler', kwargs={'node_id': node['id']}),
            headers=self.default_headers
        )
        resp_macs = map(
            lambda interface: interface["mac"],
            json.loads(resp.body)
        )
        self.assertEquals(resp.status, 200)
        self.assertItemsEqual(macs, resp_macs)
