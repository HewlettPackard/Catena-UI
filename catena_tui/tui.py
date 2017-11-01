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
import os
import pprint
import re
import subprocess

from whiptail import Whiptail

from catena_tui.accounts import create_ethereum_account
from catena_tui.accounts import get_ethereum_account
from catena_tui.accounts import get_ethereum_addresses
from catena_tui.api import add_blockchain
from catena_tui.api import add_cloud
from catena_tui.api import add_node
from catena_tui.api import get_backends_info
from catena_tui.api import get_blockchain_by_id
from catena_tui.api import get_blockchains
from catena_tui.api import get_cloud_types
from catena_tui.api import get_clouds
from catena_tui.api import get_instances
from catena_tui.api import get_networks
from catena_tui.api import get_node_by_id
from catena_tui.api import get_node_flavours
from catena_tui.api import get_nodes
from catena_tui.api import remove_blockchain
from catena_tui.api import remove_node

stty_output = subprocess.check_output(['stty', 'size'])
stty_parts = stty_output.split()
height = int(stty_parts[0]) - 4  # Subtract a bit to allow for a border. It looks better that way.
width = int(stty_parts[1]) - 4
w = Whiptail(title="Catena", height=height, width=width, auto_exit=True)


def pretty_json(data):
    return json.dumps(data, indent=4, sort_keys=True)


def ui_list_clouds():
    w.menu("Choose a cloud", ["{} ({})".format(b["name"], b["id"]) for b in get_clouds()])


def ui_create_cloud():
    name = w.prompt("Cloud name")
    type = w.menu("Cloud type", get_cloud_types())
    authentication = w.prompt("Authentication")
    user_data_file = w.prompt("File for userdata (e.g. cloud-init), if any")
    proxy = w.prompt("Enter proxy, if any")
    image = w.prompt("Enter the VM image")

    add_cloud(
        name=name,
        type=type,
        authentication=authentication,
        proxy=proxy,
        user_data_file=user_data_file,
        image=image)


def ui_create_blockchain(chain_type=None, chain_backend=None, network_id=None, genesis=None, external_bootnodes=None):
    """Create a new blockchain or import configuration from an existing one.

       Parameters set to None will be populated by the backend.
    """

    backends = get_backends_info()
    name = w.prompt("Blockchain name")
    cloud = w.menu("Choose cloud", ["{} ({})".format(b["name"], b["id"]) for b in get_clouds()])

    cloud_id = re.findall(r'^.*\((.*)\)$', cloud)[0]

    if chain_backend is None:
        chain_backend = w.menu("Chooses a blockchain backend", backends.keys())

    if chain_type is None:
        chain_type = w.menu("Choose a blockchain type", backends[chain_backend]['chain_types'])

    account = w.prompt("Enter the account to which mining rewards will be send")
    controller_flavour = w.menu("Choose a flavour for the controller", get_node_flavours(cloud_id))
    network = w.menu("Choose a network for the blockchain", get_networks(cloud_id))
    jumpbox = w.menu("Choose a jumpbox", get_instances(cloud_id))
    jumpbox_keyfile = w.prompt("Enter the jumpbox key file")

    add_blockchain(
        name=name,
        cloud_id=cloud_id,
        chain_backend=chain_backend,
        chain_type=chain_type,
        controller_flavour=controller_flavour,
        jumpbox=jumpbox,
        jumpbox_keyfile=jumpbox_keyfile,
        network=network,
        mining_account=account,
        genesis=genesis,
        network_id=network_id,
        external_bootnodes=external_bootnodes)


def ui_list_blockchains():
    items = ["{} ({})".format(b["name"], b["id"]) for b in get_blockchains()]

    result = w.menu("Choose a blockchain", items)

    # Extract id from menu text. Example: "Blockchain 2 (fcf07498-d8cc-4534-be3f-6a3898d7343c)".
    blockchain_id = re.findall(r'^.*\((.*)\)$', result)[0]
    blockchain = get_blockchain_by_id(blockchain_id)
    ui_choose_blockchain_action(blockchain)


def ui_blockchain_info(blockchain):
    w.alert(pretty_json(blockchain))


def ui_node_info(node):
    w.alert(pprint.pformat(node))


def ui_add_node(blockchain):
    info = get_backends_info()
    nodes = get_nodes(blockchain)
    node_types = info[blockchain['chain_backend']]['node_types']
    type = w.menu("Choose a node type", node_types)
    flavour = w.menu("Choose a flavour", get_node_flavours(blockchain['cloud_id']))
    recommended_name = blockchain['name'] + "_" + type + "_" + str(len(nodes))
    name = w.prompt("Enter a name for the new node", recommended_name)

    add_node(blockchain=blockchain, type=type, flavour=flavour, name=name)


def ui_list_nodes(blockchain):
    test = get_nodes(blockchain)
    items = ["{} ({})".format(b["name"], b["id"]) for b in test]

    if len(items) == 0:
        return w.alert("No nodes.")

    selection = w.menu("Choose a node", items)

    node_id = re.findall(r'^.*\((.*)\)$', selection)[0]

    node = get_node_by_id(blockchain, node_id)
    ui_choose_node_action(blockchain, node)


def ui_choose_node_action(blockchain, node):
    items = [
        "Info"
    ]

    if node['type'] != 'controller':
        items.insert(0, "Remove node")

    result = w.menu("Choose an action", items)

    if result == "Info":
        ui_node_info(node)
    elif result == "Remove node":
        ui_remove_node(blockchain, node)


def ui_account_info(address):
    account = get_ethereum_account(address)
    w.alert(pretty_json(account))


def ui_create_account():
    pw = w.prompt("Enter password")
    pw2 = w.prompt("Repeat password")

    if pw != pw2:
        w.alert("Passwords are not the same!")
        ui_create_account()
    else:
        account, path = create_ethereum_account(pw)
        w.alert("The address for the new account is:\n\n"
                "{}\n\nThe json data is stored under:\n\n"
                "{}\n\n"
                "ATTENTION: It is important to remember the password and the account and to keep the json file safe."
                .format(account, path))


def ui_list_accounts():
    addresses = get_ethereum_addresses()
    address = w.menu("Choose an account", addresses)

    ui_account_info(address)


def ui_choose_main_action():
    items = [
        "Create a new cloud",
        "Create a new blockchain from existing config",
        "Create a new account"
    ]

    if len(get_clouds()) > 0:
        items.insert(0, "List clouds")
        items.insert(0, "Create a new blockchain")

    if get_blockchains():
        items.insert(0, "List blockchains")

    if get_ethereum_addresses():
        items.append("List accounts")

    result = w.menu("Choose an action", items)

    if result == "Create a new blockchain":
        ui_create_blockchain()
    elif result == "Create a new blockchain from existing config":
        ui_import_blockchain()
    elif result == "List blockchains":
        ui_list_blockchains()
    elif result == "Create a new account":
        ui_create_account()
    elif result == "List accounts":
        ui_list_accounts()
    elif result == "List clouds":
        ui_list_clouds()
    elif result == "Create a new cloud":
        ui_create_cloud()


def ui_remove_node(blockchain, node):
    result = w.confirm("Are you sure that you want to remove the node '{}' from blockchain '{}'?".format(
        node["id"],
        blockchain["id"]))

    if result:
        remove_node(blockchain, node)


def ui_remove_blockchain(blockchain):
    result = w.confirm("Are you sure that you want to remove the blockchain '{}'?".format(blockchain["id"]))

    if result:
        remove_blockchain(blockchain)


def ui_get_external_bootnodes(blockchain):
    external_nodes = []

    nodes = get_nodes(blockchain)
    items = ["{} ({})".format(b["name"], b["id"]) for b in nodes if b["id"] not in external_nodes]

    selected_items = w.checklist("Select all externally available nodes", items)

    for selected_item in selected_items:
        ip = w.prompt("Enter externally available ip for: {}".format(selected_item))
        selected_node_id = re.findall(r'^.*\((.*)\)$', selected_item)[0]
        selected_node = get_node_by_id(blockchain, selected_node_id)
        selected_node_chain_config = json.loads(selected_node['chain_config'])
        selected_enode = 'enode://{}@{}:30303'.format(selected_node_chain_config['eth_node_id'], ip)

        external_nodes.append(selected_enode)

    return external_nodes


def ui_export_blockchain(blockchain):
    chain_config = json.loads(blockchain['chain_config'])
    chain_backend = blockchain['chain_backend']
    chain_type = chain_config['type']
    network_id = chain_config['network_id']
    genesis = chain_config['genesis']
    name = blockchain['name']

    path = w.prompt("Enter a path for the export")
    os.mkdir(path)

    external_bootnodes = ui_get_external_bootnodes(blockchain)

    with open(os.path.join(path, 'external_bootnodes.json'), 'w') as file:
        json.dump(external_bootnodes, file)

    with open(os.path.join(path, 'genesis.json'), 'w') as file:
        json.dump(genesis, file)

    with open(os.path.join(path, 'chain_config.json'), 'w') as file:
        data = {
            "backend": chain_backend,
            "network_id": network_id,
            "type": chain_type
        }

        json.dump(data, file)

    base_script = """#!/bin/bash
set -e # Exit on error

ipc=$HOME/.catena/ethereum/{}/geth.ipc

""".format(name)

    with open(os.path.join(path, 'run-geth.sh'), 'w') as file:
        file.write(base_script)
        file.write("""parameters=""

if (whiptail --title "MetaMask" --yesno "Do you want to use MetaMask?" 8 78) then
    metamask_id=$(whiptail --inputbox "Enter MetaMask's Chome extenstion id.\n\nTo find the id, open Chome, navigate to Preferences -> More tools -> Extensions and enable 'Developer mode'" 11 78 --title "MetaMask" 3>&1 1>&2 2>&3)
    parameters=' --rpccorsdomain "chrome-extension://$metamask_id"'
fi

""")  # noqa
        file.write("geth --datadir ~/.catena/ethereum/{}/ init genesis.json\n".format(name))
        file.write("geth --datadir ~/.catena/ethereum/{}/ --networkid {} --bootnodes {} --rpc\n".format(
            name,
            network_id,
            ",".join(external_bootnodes)))

    check_ipc_script = """if [ ! -S $ipc ]
then
    whiptail --title "Error" --msgbox "'run-geth.sh' must run before this script!" 8 78
    exit 1
fi
""".format(name)

    with open(os.path.join(path, 'attach-geth.sh'), 'w') as file:
        file.write(base_script)
        file.write(check_ipc_script)
        file.write("geth attach ipc://$ipc\n".format(name))

    with open(os.path.join(path, 'run-mist.sh'), 'w') as file:
        file.write(base_script)
        file.write(check_ipc_script)
        file.write("mist --rpc $ipc\n".format(name))

    w.alert("Config and scripts written to {}".format(path))


def ui_import_blockchain():
    path = w.prompt("Enter the path with the config")

    with open(os.path.join(path, "genesis.json")) as in_file:
        genesis = json.load(in_file)

    with open(os.path.join(path, "external_bootnodes.json")) as in_file:
        external_bootnodes = json.load(in_file)

    with open(os.path.join(path, "chain_config.json")) as in_file:
        config = json.load(in_file)

    ui_create_blockchain(
        chain_type=config['type'],
        chain_backend=config['backend'],
        network_id=config['network_id'],
        genesis=genesis,
        external_bootnodes=external_bootnodes
    )


def ui_choose_blockchain_action(blockchain):
    items = [
        "Add node",
        "Remove blockchain",
        "Export config and scripts",
        "List nodes",
        "Info"
    ]

    # if get_nodes(blockchain):
    #     items.insert(0, "List nodes")

    result = w.menu("Choose an action", items)

    if result == "Info":
        ui_blockchain_info(blockchain)
    elif result == "Add node":
        ui_add_node(blockchain)
    elif result == "List nodes":
        ui_list_nodes(blockchain)
    elif result == "Remove blockchain":
        ui_remove_blockchain(blockchain)
    elif result == "Export config and scripts":
        ui_export_blockchain(blockchain)
