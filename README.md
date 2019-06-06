# pan_ssh_ciphers

The purpose of this script is to set the SSH Mgmt and HA ciphers, restart the Mgmt and HA services, and restart the device.

## Built With

[Palo Alto Networks Device Framework (pandevice)](https://github.com/PaloAltoNetworks/pandevice)

## Deployment

All files within the folder should be deployed in the same directory for proper file execution.

## Prerequisites

Update `config.py` file with correct values before operating.

## Operating

The below command will execute the script.

```bash
python pan_ssh_ciphers.py
```

## Changelog

See the [CHANGELOG](CHANGELOG) file for details