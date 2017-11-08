#!/usr/bin/env python

# Copyright 2015 Michael Rice <michael@michaelrice.org>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from __future__ import print_function

import atexit

import requests
from py_vmware.tools import cli
from py_vmware.tools import tasks
import py_vmware.vmware_lib as vmware_lib

requests.packages.urllib3.disable_warnings()


def setup_args():
    """Adds additional ARGS to allow the vm name or uuid to
    be set.
    """
    parser = cli.build_arg_parser()
    # using j here because -u is used for user
    parser.add_argument('-j', '--uuid',
                        help='BIOS UUID of the VirtualMachine you want to destroy.')
    parser.add_argument('-n', '--vm-name',
                        help='DNS Name of the VirtualMachine you want to destroy.')
    parser.add_argument('-i', '--ip',
                        help='IP Address of the VirtualMachine you want to destroy')
    # empty values
    parser.add_argument('--template',
                        action='store',
                        help='Name of the template/VM \
                            you are cloning from')
    parser.add_argument('--vm-folder',
                        required=False,
                        action='store',
                        default=None,
                        help='Name of the VMFolder you wish\
                            the VM to be dumped in. If left blank\
                            The datacenter VM folder will be used')

    my_args = parser.parse_args()

    return cli.prompt_for_password(my_args)


def main():
    ARGS = setup_args()
    SI = None
    try:
        SI = vmware_lib.connect(
            ARGS.host,
            ARGS.user,
            ARGS.password,
            ARGS.port,
            ARGS.insecure
        )
        print("- connected to vmware")
    except IOError as ex:
        print("IOError: %s" % ex.message)
        pass
    
    if not SI:
        raise SystemExit("Unable to connect to host with supplied info.")
    VM = None
    if ARGS.uuid:
        print("- looking for VM by UUID: %s" % ARGS.uuid)
        VM = SI.content.searchIndex.FindByUuid(
            None, ARGS.uuid, True, False)
    elif ARGS.vm_name:
        print("- looking for VM by DNS Name: %s" % ARGS.vm_name)
        VM = SI.content.searchIndex.FindByDnsName(
            None, ARGS.vm_name, True)
    elif ARGS.ip:
        print("- looking for VM by IP: %s" % ARGS.ip)
        VM = SI.content.searchIndex.FindByIp(None, ARGS.ip, True)

    if VM is None:
        raise SystemExit("Unable to locate VirtualMachine.")
    
    print("Found: {0}".format(VM.name))
    print("The current powerState is: {0}".format(VM.runtime.powerState))
    if format(VM.runtime.powerState) == "poweredOn":
        print("Attempting to power off {0}".format(VM.name))
        TASK = VM.PowerOffVM_Task()
        tasks.wait_for_tasks(SI, [TASK])
        print("{0}".format(TASK.info.state))
        
        print("Destroying VM from vSphere.")
        TASK = VM.Destroy_Task()
        tasks.wait_for_tasks(SI, [TASK])
        print("Done.")

if __name__ == '__main__':
    main()
