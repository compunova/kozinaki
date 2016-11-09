========
Overview
========

Kozinaki is an OpenStack multi-cloud driver which aims to enable full lifecycle management of resource through OpenStack in public cloud providers (AWS, Azure, with more to come). We beleive that building a multi-cloud driver will open possiblities for true hybrid OpenStack use case and provide the uniformity in access to public clouds resources through versatile community developed OpenStack APIs. This driver gives an option to optimize on performance, price, avilability while preserving time and money investment into work deployment and management be it on prem or cloud resources.

Kozinaki is intended to be completely pluggable into OpenStack architecture without changing the code of core OpenStack components. The driver has modular architecture which makes adding new cloud providers fairly easy. Kozinaki architecture relies on provider developed SDKs to interface with their APIs, where it is not feasible we are open to evaluate the use of libcloud.

========
Support
========

We are open to help you with issues that you might have with te driver.glad

----------------------------
Installation & Configuration
----------------------------

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Install the python modules.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For example::

  $ pip install git+https://github.com/compunova/kozinaki.git#egg=kozinaki


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2. Enable the driver in Nova's configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In nova.conf::

  compute_driver=kozinaki.driver.KozinakiDriver

  [kozinaki]
  prefix=os
  bridge=br818
  bridge_interface=eth0.818
  network_name=test
  proxy_url=False


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
3. Enable AWS support in Nova's configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In AWS console interface:

1. Create new user `Services -> IAM -> USERS -> CREATE NEW USERs` and get his access and secret access key
2. Add permissions to new user `Permissions -> Attach Policy`:
    * AdministratorAccess
    * AmazonEC2FullAccess

In nova.conf::

  [kozinaki_AWS]
  aws_access_key_id=<access_key>
  aws_secret_access_key=<secret_key>
  region=us-west-2


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
4. Enable Azure support in Nova's configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Create new app in Azure portal `App reg`:
    * Name:  OpenStackClient
    * Type: Web or API
    * url: https://any_url.com

2. Go to created app `Settings -> Keys` and get access key
3. Add permissions to new app:
    * Windows Azure Active Directory
    * Windows Azure Service Management API

4. Get app tenant ID `Azure Active Directory -> App registrations -> Endpoints -> OAuth 2.0 Authorization Endpoint` (ID `c03fbc0f-ed1c-48d8-9c97-e6090ef58180` in url)::

    https://login.windows.net/c03fbc0f-ed1c-48d8-9c97-e6090ef58180/oauth2/authorize

5. Upload certificate to Azure
    * Go to old portal https://manage.windowsazure.com/  Left menu -> Settings
    * Select Upload in Management Certificates


In nova.conf::

  [kozinaki_AZURE]
  subscription_id=<subscription_id>
  key_file=<path_to_key_file>

  # Azure app conf
  app_client_id=<app_client_id>
  app_secret=<app_secret>
  app_tenant=<app_tenant>

  # New VM default params
  username=userlogin
  password=pa$$w0rd
  resource_group_name=openstack-virtual-machines
  storage_account_name=quietbird2295
  location=westeurope
  os_disk_name=openstack-sample-osdisk
  vnet_name=openstack-sample-vnet
  subnet_name=openstack-sample-subnet
  ip_config_name=openstack-sample-ip-config
  nic_name=openstack-sample-nic

