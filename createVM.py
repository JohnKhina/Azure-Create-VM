from azure.common.credentials import UserPassCredentials
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient

LOCATION = 'australiaeast'


AZURE_TENANT_ID = '11111-1111-1111-1111-111111111111'
AZURE_CLIENT_ID = '11111111-1111-1111-1111-111111111111'
AZURE_CLIENT_SECRET = '1111111122222222333333334444444455555'
AZURE_SUBSCRIPTION_ID = '1111111122222222333333334444444455'

GROUP_NAME = 'dev-aue-rg'               #resource group name
VNET_NAME = 'dev-aue-vnet'              #VNET name
SUBNET_NAME = 'dev-aue-subnet'          #subnet name
OS_DISK_NAME = 'devapp01-osdisk'        #VM disk name
STORAGE_ACCOUNT_NAME = 'appdevstorage'  #Storage account name
IP_CONFIG_NAME = 'devapp01-ip-config' 
NIC_NAME = 'devapp01-nic'               #network interface name
USERNAME = 'devlogin'                   #login username
PASSWORD = 'creative99Secret#@!'        #login password
VM_NAME = 'devapp01'                    #vm name

VM_REFERENCE = {                        #image type to use
        'publisher': 'RedHat',
        'offer': 'RHEL',
        'sku': '7.3',
        'version': 'latest'
    }

def run_example():
    
    subscription_id = os.environ.get(
        AZURE_SUBSCRIPTION_ID,
        '1111111122222222333333334444444455') # your Azure Subscription Id
    credentials = ServicePrincipalCredentials(
        client_id = AZURE_CLIENT_ID,
        secret = AZURE_CLIENT_SECRET,
        tenant = AZURE_TENANT_ID
    )
    resource_client = ResourceManagementClient(credentials, subscription_id)
    compute_client = ComputeManagementClient(credentials, subscription_id)
    storage_client = StorageManagementClient(credentials, subscription_id)
    network_client = NetworkManagementClient(credentials, subscription_id)

    # Create Resource group
    print('\nCreate Resource Group')
    resource_client.resource_groups.create_or_update(GROUP_NAME, {'location':LOCATION})


    # Create a storage account
    print('\nCreate a storage account')
    storage_async_operation = storage_client.storage_accounts.create(
        GROUP_NAME,
        STORAGE_ACCOUNT_NAME,
        {
            'sku': {'name': 'standard_lrs'},
            'kind': 'storage',
            'location': LOCATION
        }
    )

    storage_async_operation.wait()

     # Create a NIC
    nic = create_nic(network_client)

    # Create Linux VM
    print('\nCreating Red Hat Enterprise Linux Virtual Machine')
    vm_parameters = create_vm_parameters(nic.id, VM_REFERENCE)
    async_vm_creation = compute_client.virtual_machines.create_or_update(
        GROUP_NAME, VM_NAME, vm_parameters)
    async_vm_creation.wait()

    # Start the VM
    print('\nStart VM')
    async_vm_start = compute_client.virtual_machines.start(GROUP_NAME, VM_NAME)
    async_vm_start.wait()

def create_nic(network_client):
    """Create a Network Interface for a VM.
    """
    # Create VNet
    print('\nCreate Vnet')
    async_vnet_creation = network_client.virtual_networks.create_or_update(
        GROUP_NAME,
        VNET_NAME,
        {
            'location': LOCATION,
            'address_space': {
                'address_prefixes': ['172.16.0.0/12']
            }
        }
    )
    async_vnet_creation.wait()

    # Create Subnet
    print('\nCreate Subnet')
    async_subnet_creation = network_client.subnets.create_or_update(
        GROUP_NAME,
        VNET_NAME,
        SUBNET_NAME,
        {'address_prefix': '172.16.0.0/24'}
    )
    subnet_info = async_subnet_creation.result()

    # Create NIC
    print('\nCreate NIC')
    async_nic_creation = network_client.network_interfaces.create_or_update(
        GROUP_NAME,
        NIC_NAME,
        {
            'location': LOCATION,
            'ip_configurations': [{
                'name': IP_CONFIG_NAME,
                'subnet': {
                    'id': subnet_info.id
                }
            }]
        }
    )
    return async_nic_creation.result()

def create_vm_parameters(nic_id, vm_reference):
    """Create the VM parameters structure.
    """
    return {
        'location': LOCATION,
        'os_profile': {
            'computer_name': VM_NAME,
            'admin_username': USERNAME,
            'admin_password': PASSWORD
        },
        'hardware_profile': {
            'vm_size': 'Standard_A4_v2'
        },
        'storage_profile': {
            'image_reference': {
                'publisher': vm_reference['publisher'],
                'offer': vm_reference['offer'],
                'sku': vm_reference['sku'],
                'version': vm_reference['version']
            },
            'os_disk': {
                'name': OS_DISK_NAME,
                'caching': 'None',
                'create_option': 'fromImage',
                'vhd': {
                    'uri': 'https://{}.blob.core.windows.net/vhds/{}.vhd'.format(
                        STORAGE_ACCOUNT_NAME, VM_NAME)
                }
            },
        },
        'network_profile': {
            'network_interfaces': [{
                'id': nic_id,
            }]
        },
    }


if __name__ == "__main__":
    run_example()

