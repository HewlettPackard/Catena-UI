# (C) Copyright 2017 Hewlett Packard Enterprise Development LP.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import uuid

import requests

ENDPOINT = "http://localhost:1989"


def new_id():
    return str(uuid.uuid4())

# ##########
# ## API ###
# ##########


def get_blockchains():
    return requests.get(ENDPOINT + "/v1/chains").json()


def get_blockchain_by_id(id):
    return requests.get(ENDPOINT + "/v1/chains/{}".format(id)).json()


def get_backends_info():
    return requests.get(ENDPOINT + "/v1/backends/").json()


def add_blockchain(
        name,
        cloud_id,
        chain_type,
        chain_backend,
        controller_flavour,
        network,
        jumpbox,
        jumpbox_keyfile,
        mining_account,
        genesis=None,
        network_id=None,
        external_bootnodes=None):

    file = open(jumpbox_keyfile, "r")
    jumpbox_key = file.read()
    file.close()

    data = {
        "name": name,
        "backend": chain_backend,
        "cloud_id": cloud_id,
        "chain_config": {
            "type": chain_type,
            "mining_account": mining_account,
            "genesis": genesis,
            "network_id": network_id,
            "external_bootnodes": external_bootnodes
        },
        "cloud_config": {
            "controller_flavour": controller_flavour,
            "jumpbox": jumpbox,
            "jumpbox_key": jumpbox_key,
            "network": network
        }
    }

    response = requests.post(ENDPOINT + "/v1/chains", data=json.dumps(data))
    response.raise_for_status()


def add_node(blockchain, type, flavour, name):
    data = {
        "type": type,
        "flavour": flavour,
        "name": name
    }

    requests.post(ENDPOINT + "/v1/chains/{}/nodes".format(blockchain['id']), data=json.dumps(data))


def remove_node(blockchain, node):
    requests.delete(ENDPOINT + "/v1/chains/{}/nodes/{}".format(blockchain['id'], node['id']))


def remove_blockchain(blockchain):
    return requests.delete(ENDPOINT + "/v1/chains/" + blockchain['id']).json()


def get_nodes(blockchain):
    return requests.get(ENDPOINT + "/v1/chains/{}/nodes".format(blockchain['id'])).json()


def get_clouds():
    return requests.get(ENDPOINT + "/v1/clouds").json()


def add_cloud(type, name, authentication, image, user_data_file, proxy):
    config = {}

    # Read user data file (if any)
    if user_data_file is not None and len(user_data_file) > 0:
        with open(user_data_file, 'r') as f:
            config['user_data'] = f.read()

    # Parse image (OpenStack vs Azure vs AWS)
    try:
        config['image'] = json.loads(image)
    except ValueError:
        config['image_name'] = image

    # Set proxy (if any)
    if proxy is not None and len(proxy) > 0:
        config['proxy'] = proxy

    data = {
        "type": type,
        "name": name,
        "authentication": json.loads(authentication),
        "config": config
    }

    response = requests.post(ENDPOINT + "/v1/clouds", data=json.dumps(data))
    response.raise_for_status()


def get_cloud_types():
    return requests.get(ENDPOINT + "/v1/clouds/types").json()


def get_node_flavours(cloud_id):
    return requests.get(ENDPOINT + "/v1/clouds/{}/node_flavours".format(cloud_id)).json()


def get_instances(cloud_id):
    return requests.get(ENDPOINT + "/v1/clouds/{}/instances".format(cloud_id)).json()


def get_networks(cloud_id):
    return requests.get(ENDPOINT + "/v1/clouds/{}/networks".format(cloud_id)).json()


def get_node_by_id(blockchain, id):
    return requests.get(ENDPOINT + "/v1/chains/{}/nodes/{}".format(blockchain['id'], id)).json()
