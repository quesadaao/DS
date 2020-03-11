#**********************************************************************

#!/usr/bin/env python


from novaclient.v1_1 import client
from credentials import get_nova_creds
import time
import cinderclient.v1.client
import os
import cinderclient.v1.client as cclient

 

creds = get_nova_creds()
nova = client.Client(**creds)
m_name = "SERVER"
m_image = "2008R2SP1_STANDARD"
m_flavor = "1vCPU-2048MB"
m_network = "NETWORK"


image = nova.images.find(name=m_image)
flavor = nova.flavors.find(name=m_flavor)
network = nova.networks.find(label=m_network)


#Create Server
server = nova.servers.create(name = m_name, image = image.id, flavor = flavor.id, nics = [{'net-id':network.id}])

 

while nova.servers.find(id=server.id).status != "ACTIVE":
  server_status = nova.servers.find(id=server.id).status
print "Server created: ", nova.servers.find(id=server.id).status
#**********************************************************************
res = nova.floating_ips.list()
unused_ips = [addr for addr in nova.floating_ips.list() if addr.instance_id is None]
scell_ips = [u_ip for u_ip in unused_ips if u_ip.pool ==  "POOL"]
fip = scell_ips[0]
instance = nova.servers.find(name=m_name)
res = instance.add_floating_ip(fip)
print "Floating ip associated: ",fip
#**********************************************************************
try:
        instance=nova.servers.find(name=m_name)
        sginstances=nova.security_groups.list()
        if len(sginstances)>0:
                sginstance=instance.list_security_group()
                if len(sginstance)>0:
                        for sgservers in sginstances:
                                for sgserver in sginstance:
                                        if sgserver.name==sgservers.name:
#                                               print "deleting...",sgservers.name
                                                instance.remove_security_group(sgservers.name)
except:
        print "Server not found,check the name..."
print "Security group removed..."
#**********************************************************************

 

# Set credetials
cinder = cclient.Client(**creds)

 

# Create Volume D, S, T, L and Z 
volumeD = cinder.volumes.create(size=9, display_name='DATA',display_description='Data')
volumeT = cinder.volumes.create(size=9, display_name='TEMP',display_description='TEMP')
volumeL = cinder.volumes.create(size=9, display_name='LOGS',display_description='LOGS')
volumeZ = cinder.volumes.create(size=9, display_name='BACKUPS',display_description='BACKUPS')

 

#Create Volume from snapshot
snapshot= cinder.volume_snapshots.findall(display_name='S_Snapshot')
volumeS = cinder.volumes.create(size=10, snapshot_id=snapshot[0].id, display_name='SQL')

 

#array for check status
volumes=[volumeD,volumeT,volumeL,volumeZ,volumeS]

 

#wait the status for each volume, all of them shoul be available
count=0
while count<=len(volumes)-1:
        volume_status = cinder.volumes.get(volumes[count].id).status
        if volume_status == "available":
                count=count+1
print "Volumes created"

 

# Attach
count=0
while count<=len(volumes)-1:
       

       #get the current volume
       volume = cinder.volumes.findall(display_name=volumes[count].display_name)
       if len(volume[0].attachments)==0:
               

                # Attach volume
                nova.volumes.create_server_volume(instance.id, volume[0].id,None)
                instance=nova.servers.find(name=m_name)
                time.sleep(40)#this time its mandatory. Wait for the status of server for attach other volume.
                print volume[0].display_name
                count=count+1

print "Done!!!"
 

#**********************************************************************