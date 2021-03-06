grizzly-tools
=============

Admin scripts for Grizzly that direct-access the DB instead of API

### Usage for vm_info

```
$ ./vm_info --help
usage: vm_info [-h] [-n] [-v] [-s] [-a] [-f FLOATING_IP] [-i INSTANCE]
               [-u UUID]

Lookup VM Information

optional arguments:
  -h, --help            show this help message and exit
  -n, --network         Include network information
  -v, --volumes         Include volume information
  -s, --secgroups       Include security group information
  -a, --all             Include network, volume & security group information
  -f FLOATING_IP, --floating_ip FLOATING_IP
  -i INSTANCE, --instance INSTANCE
  -u UUID, --uuid UUID

Use only ONE search parameter [floating_ip|instance|uuid]
```
### Sample Output for vm_info

```
$ ./vm_info -nvsu d9000d06-d6cc-4783-8b77-839b62b9ab8e

[ Virtual Machine ]
Hostname: docker01
 Display: docker01
 Created: 2014-07-28 21:21:08
 Updated: 2014-07-29 06:21:08
 Creator: 3dedc6ed0d4540e9b84d7f73c53a607c [jh6103]
  Flavor: m1.tiny [cpu:1   ram:512    root:12 GB  eph:0  GB]
   Image: 4c5d0874-933d-4eef-859e-697d44d51bd1 [Ubuntu-14.04]
 SSH Key: my_pubkey
    UUID: d9000d06-d6cc-4783-8b77-839b62b9ab8e
Instance: instance-00002cf8
 Project: ac85e3a9ada6457e8bdc2d0701c34159 [my_project]
 Compute: cnode01
   State: active

[ Networking ]
 VM Port: 1aa87b72-2d57-47f4-a7f6-d4bd47b203a9 [fa:16:3e:e7:9f:ce] [eth0]
 Network: d967ec9b-5f9e-43e4-97b8-53ad8e252ea0 [docker_network]
  Subnet: 78231522-11b6-4a06-b37f-c45061f6d723 [docker_subnet]
    DHCP: 31393d35-09a3-4cd8-84d4-04a7ea5ef630 [fa:16:3e:17:67:48] [192.168.0.2] [ACTIVE]
    DHCP: 4fec4e6d-3dd3-44ae-ad5c-4957b65c0eaf [fa:16:3e:a7:ee:8f] [192.168.0.3] [ACTIVE]
  Router: c72a6b43-b946-4477-8cd6-a5eb5cc3c2bc [fa:16:3e:67:fe:0a] [docker_router] [ACTIVE]
    L3GW: l3gw01.int.mydomain.com
    CIDR: 192.168.0.0/24
 Gateway: 192.168.0.1  
 Private: 192.168.0.5 [exp:2014-07-31 22:03:44]
Floating: XXX.XXX.XXX.XXX

[ Volumes ]
496b0760-cf01-408c-9d8a-f0322d786310 [docker_volume]
:: My Docker Volume
 Created: 2014-07-30 23:19:26
 Creator: 3dedc6ed0d4540e9b84d7f73c53a607c [jh6103]
    Size: 2 GB
Provider: n123456n3210a4002:/vol/v00_n123456n3210a4002_cinder_ZONE1
  Status: in-use [attached]

[ Security Groups ]
28b3f563-076f-44e4-bba5-5493aba7890a [docker_secgroup]
:: Docker Security Group
    PROT   MIN     MAX     CIDR                 ID
    icmp   None    None    0.0.0.0/0            395a5344-7f8d-427d-b27b-c8d1203fa713
    tcp    22      22      0.0.0.0/0            20f87541-d28e-4ce7-859f-3233144d9ff4
    tcp    3306    3306    192.168.0.0/24       176d64ea-330a-408f-7fb1-ae9b593ff059
    tcp    4444    4444    192.168.0.0/24       68c677de-5060-41a7-a472-5188639e17f7
    tcp    4500    4500    192.168.0.0/24       d1a37190-8ff6-4a76-973f-7ba5489e877b
    tcp    4567    4567    192.168.0.0/24       0c233f3e-7049-4b76-be68-38abc586663d
    tcp    4568    4568    192.168.0.0/24       64d69f69-0ece-4cec-a175-7674a47e1331
    tcp    5000    5000    192.168.0.0/24       6bfb8c4f-adbf-4d71-b110-9398d84b1b76

```
