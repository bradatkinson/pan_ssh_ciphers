#!/usr/bin/env python

# Copyright (c) 2019 Brad Atkinson <brad.scripting@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys
import time
import config
from pandevice import base
from pandevice import firewall
from pandevice import errors


def get_fw_connection():
    """
    Make firewall connection

    Returns
    -------
    fw : Firewall
        A PanDevice for firewall
    """
    key = config.paloalto['key']
    fw_ip = config.paloalto['firewall_ip']
    fw = firewall.Firewall(hostname=fw_ip, api_key=key)
    return fw


def check_ciphers(fw, service):
    """
    Check if ciphers are already set and if so add them to a list

    Parameters
    ----------
    fw : Firewall
        A PanDevice for firewall
    service : list
        A list of strings containing the SSH services

    Returns
    -------
    set_ciphers_list : list
        A list of strings containing the ciphers already set on the firewall
    """
    print('\nChecking {} ciphers...\n'.format(service))

    base_xpath = ("/config/devices/entry[@name='localhost.localdomain']"
                  "/deviceconfig/system/ssh/ciphers/{}".format(service))
    results = fw.xapi.get(xpath=base_xpath)

    xml_list = results.findall('./result/{}/'.format(service))

    set_ciphers_list = []

    for item in xml_list:
        set_ciphers_list.append(item.tag)

    return set_ciphers_list


def compare_ciphers(cipher_list, service, set_ciphers_list, results_list):
    """
    Compare the list of defined ciphers to be set to the list of set ciphers
    on the firewall

    Parameters
    ----------
    cipher_list : list
        A PanDevice for firewall
    service : list
        A list of strings containing the SSH services
    set_ciphers_list : list
        A list of strings containing the ciphers already set on the firewall
    results_list : list
        An empty list

    Returns
    -------
    results_list : list
        A list of strings containing the cipher status
    status : str
        A string telling if the cipher is set or not set
    """
    print('Comparing {} ciphers...\n'.format(service))

    if set(cipher_list).issubset(set_ciphers_list):
        print('Ciphers match!\n')
        status = 'ciphers_set'
        results_list.append(status)
    else:
        print('Ciphers need to be set...\n')
        status = 'ciphers_not_set'
        results_list.append(status)

    return(results_list, status)


def set_ciphers(fw, service, cipher_list):
    """
    Set the ciphers from the provided list

    Parameters
    ----------
    fw : Firewall
        A PanDevice for firewall
    service : list
        A list of strings containing the SSH services
    cipher_list : list
        A PanDevice for firewall
    """
    print('Setting {} ciphers...\n'.format(service))

    for cipher in cipher_list:
        base_xpath = ("/config/devices/entry[@name='localhost.localdomain']"
                      "/deviceconfig/system/ssh/ciphers/{}".format(service))
        entry_element = ('<{}/>'.format(cipher))
        results = fw.xapi.set(xpath=base_xpath, element=entry_element)    

        xml_list = results.findall('.')

        for item in xml_list:
            status_dict = item.attrib
            status = status_dict.get('status')
            print('{} install {}'.format(cipher, status))


def commit_config(fw):
    """
    Commit the firewall changes with the description provided

    Parameters
    ----------
    fw : Firewall
        A PanDevice for firewall
    """
    print('\nCommitting config...')

    command = "<commit><description>SSH Ciphers Commit</description></commit>"
    results = fw.commit(sync=True, cmd=command)

    print('Commit Status:\n')
    messages = results.get('messages')
    if isinstance(messages, list):
        for message in messages:
            print('{}\n'.format(message))
    else:
        print(messages)


def restart_service(fw, service):
    """
    Restart the provided service

    Parameters
    ----------
    fw : Firewall
        A PanDevice for firewall
    service : list
        A list of strings containing the SSH services
    """
    print('\nRestarting {} service...\n'.format(service))

    command = ('<set><ssh><service-restart><{0}></{0}></service-restart>'
               '</ssh></set>'.format(service))
    results = fw.op(cmd=command, cmd_xml=False)

    xml_list = results.findall('.')

    for item in xml_list:
        status_dict = item.attrib
        status = status_dict.get('status')
        message = item.find('./result/member').text
        print('{}...  {}\n'.format(message, status))


def restart_system(fw):
    """
    Restart the firewall

    Parameters
    ----------
    fw : Firewall
        A PanDevice for firewall
    """
    print('Restarting system...\n')

    try:
        command = '<request><restart><system></system></restart></request>'
        fw.op(cmd=command, cmd_xml=False)
    except:
        sys.exit()      


def check_device_up():
    """
    Check to see if the device is up, if not continue rechecking, and once
    back up reconnect to the firewall

    Returns
    -------
    fw : Firewall
        A PanDevice for firewall
    """
    print('Checking if device is up...\n')

    time.sleep(60)
    status = 'down'
    while status == 'down':
        try:
            print('Connecting to the device...')
            fw = get_fw_connection()
        except pandevice.errors.PanURLError:
            print('The device is still down.  Continuing to check...')
            status = 'down'
            time.sleep(60)
        else:
            print('The device is back up.  Continuing to next step...\n')
            status = 'up'

    return fw


def main():
    """
    Make the firewall connection, then check to see if ciphers are set. Next
    compare the set ciphers to the defined ciphers and if already set exit
    script.  If not, set the ciphers, commit the config, restart the services,
    and restart the firewall.
    """
    fw = get_fw_connection()

    service_list = ['mgmt', 'ha']
    cipher_list = ['aes128-cbc', 'aes192-cbc', 'aes256-cbc', 'aes128-ctr',
                   'aes192-ctr', 'aes256-ctr', 'aes128-gcm', 'aes256-gcm']
    results_list = []

    for service in service_list:
        set_ciphers_list = check_ciphers(fw, service)
        results_list, status = compare_ciphers(cipher_list, service, 
                                               set_ciphers_list, results_list)

        if status == 'ciphers_not_set':
            set_ciphers(fw, service, cipher_list)
            commit_config(fw)
            restart_service(fw, service)
            fw = check_device_up()

    results_list = list(set(results_list))

    if 'ciphers_not_set' in results_list:
        restart_system(fw)


if __name__ == '__main__':
    main()
