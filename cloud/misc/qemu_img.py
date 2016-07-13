#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Jeroen Hoekx <jeroen.hoekx@dsquare.be> - Toshaan Bharvani <toshaan@vantosh.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.


DOCUMENTATION = '''
---
author: Jeroen Hoekx & Toshaan Bharvani
module: qemu_img
short_description: Create qemu images
description:
  - "This module creates images for qemu."
version_added: "1.1"
options:
  dest:
    description: The image file to create or remove
    required: true
  format:
    description: The image format
    default: qcow2
    required: false
  options:
    description: The disk format options
    required: false
  size:
    description: The size of the image
    required: false
  state:
    choices: [ "absent", "present", "resize" ]
    description:
    - If the image should be present or absent
    default: present
    required: false
notes:
  - This module does not change the type of the image.
'''

EXAMPLES = '''
  - description: Create a raw image of 5M.
    code: qemu_img dest=/tmp/testimg size=5 format=raw

  - description: Enlarge the image to 6M.
    code: qemu_img dest=/tmp/testimg size=6 format=raw

  - description: Remove the image
    code: qemu_img dest=/tmp/testimg state=absent
'''


import os
from ansible.module_utils.basic import *


def main():
    module = AnsibleModule(
        argument_spec = dict(
            dest=dict(type='str', required=True),
            format=dict(type='str', default='qcow2'),
            options=dict(type='str', default='preallocation=metadata'),
            size=dict(type='str'),
            state=dict(type='str', choices=['absent', 'present', 'resize'], default='present'),
        ),
        supports_check_mode=True,
    )

    result = dict(
        changed=False,
        failed=False,
    )

    dest = module.params['dest']
    img_format = module.params['format']
    img_options = module.params['options']
    size = module.params['size']

    qemu_img = module.get_bin_path('qemu-img', True)

    if module.params['state'] == 'present':
        if not size:
            module.fail_json(msg='No size defined, creating a disk image requires a size')
        if not os.path.exists(dest):
            if img_options:
                module.run_command('%s create -f %s -o "%s" "%s" %s' % (qemu_img, img_format, img_options, dest, size), check_rc=True)
            else:
                module.run_command('%s create -f %s "%s" %s' % (qemu_img, img_format, dest, size), check_rc=True)
            result['changed'] = True

    if module.params['state'] == 'resize':
        if not size:
            module.fail_json(msg='No size defined, resizing a disk image requires a size')
        rc, stdout, _ = module.run_command('%s info "%s"' % (qemu_img, dest), check_rc=True)
        current_size = None
        for line in stdout.splitlines():
            if 'virtual size' in line:
                ### virtual size: 5.0M (5242880 bytes)
                current_size = int(line.split('(')[1].split()[0])
        if not current_size:
            module.fail_json(msg='Unable to read virtual disk size of %s'%(dest))
        if current_size != size:
            module.run_command('%s resize "%s" %s' % (qemu_img, dest, size), check_rc=True)
            result.changed = True

    if module.params['state'] == 'absent':
        if os.path.exists(dest):
            os.remove(dest)
            result.changed = True

    if module.check_mode:
        # Check if any changes would be made but don't actually make those changes
        module.exit_json(changed=False)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
