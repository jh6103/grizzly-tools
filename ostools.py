#!/usr/bin/env python

import ConfigParser
import MySQLdb
import MySQLdb.cursors
import os

# Terminal info
colorize = True
if (os.environ['TERM'] == "xterm" or os.environ['TERM'] == "xterm-color") and colorize:
    bld = "\033[1m"       # bold
    uln = "\033[4m"       # underline
    nrm = "\033[0m"       # reset
    red = "\033[01;31m"   # hi red
    grn = "\033[01;32m"   # hi green
    ylw = "\033[01;33m"   # hi yellow
    blu = "\033[01;34m"   # hi blue
    vlt = "\033[01;35m"   # hi violet
    cyn = "\033[01;36m"   # hi cyan
    wht = "\033[01;37m"   # hi white
else:
    bld = ''
    uln = ''
    nrm = ''
    red = ''
    grn = ''
    ylw = ''
    blu = ''
    vlt = ''
    cyn = ''
    wht = ''


class OSTools:

    def __init__(self, configfile):
        """ """
        self.configfile = configfile

    def _query(self, querystr, queryname, db, multirec=True):
        """ """
        self.dbhost,self.dbuser,self.dbpass,self.dbname = self._db_creds(self.configfile, db)
        self.db = MySQLdb.connect(host=self.dbhost,
                                  user=self.dbuser,
                                  passwd=self.dbpass,
                                  db=self.dbname,
                                  cursorclass=MySQLdb.cursors.DictCursor)
        self.cursor = self.db.cursor()

        try:
            self.cursor.execute(querystr)
        except:
            print("Error: [%s]" % queryname)

        if multirec:
            results = self.cursor.fetchall()
        else:
            results = self.cursor.fetchone()

        self._dbclose()
        return results

    def _dbclose(self):
        """ """
        self.cursor.close()
        self.db.close()

    def _db_creds(self, configfile, db):
        """ """
        config = ConfigParser.ConfigParser()

        try:
            config.read(configfile)
        except:
            print("Unable to open config file: %s" % configfile)
            sys.exit(1)

        name = config.get(db, 'name')
        user = config.get(db, 'user')
        password = config.get(db, 'pass')
        host = config.get(db, 'host')

        return (host,user,password,name)

##############################################################################
# MIXED QUERIES
##############################################################################
    def project_quotas(self, projectid):
        querystr = "SELECT resource,hard_limit \
                    FROM quotas \
                    WHERE deleted=0 \
                    AND project_id='%s' \
                    ORDER BY resource" % (projectid)
        nova_quotas = self._query(querystr, 'nova_quotas', 'nova', True)
        cndr_quotas = self._query(querystr, 'cndr_quotas', 'cinder', True)
        quotas = nova_quotas + cndr_quotas

        querystr = "SELECT resource,in_use,reserved \
                    FROM quota_usages \
                    WHERE deleted=0 \
                    AND project_id='%s' \
                    ORDER BY resource" % (projectid)
        nova_quotause = self._query(querystr, 'nova_quota_usage', 'nova', True)
        cndr_quotause = self._query(querystr, 'cndr_quota_usage', 'cinder', True)
        quotause = nova_quotause + cndr_quotause

        querystr = "SELECT count(*) AS instances, sum(vcpus) AS cores, sum(memory_mb) AS ram \
                    FROM instances WHERE deleted=0 AND project_id='%s'" % (projectid)
        nova_actual = self._query(querystr, 'nova_actual', 'nova', False)

        # Build results
        results = []
        for q in quotas:
            x = {'resource': '--',
                 'hard_limit': '--',
                 'in_use': '--',
                 'reserved': '--',
                 'actual': '--'}
            x.update(q)

            # Set nova actual values
            if q['resource'] == 'instances':
                x['actual'] = nova_actual['instances']
            if q['resource'] == 'cores':
                x['actual'] = nova_actual['cores']
            if q['resource'] == 'ram':
                x['actual'] = nova_actual['ram']

            # Manually obtain floatingip usage
            if q['resource'] == 'floating_ips':
                querystr = "SELECT count(*) AS fips \
                            FROM floatingips \
                            WHERE tenant_id='%s'" % (projectid)
                fips = self._query(querystr, 'fips', 'quantum', False)
                x['actual'] = fips['fips']

            # Manually obtain secgroup usage
            if q['resource'] == 'security_groups':
                querystr = "SELECT count(*) AS sgs \
                            FROM securitygroups \
                            WHERE tenant_id='%s'" % (projectid)
                sgs = self._query(querystr, 'sgs', 'quantum', False)
                x['actual'] = sgs['sgs']

            for qu in quotause:
                if qu['resource'] == q['resource']:
                    x.update(qu)
            results.append(x)

        return results

    def vm_list_by_fixed_ip(self,ip):
        """ """
        results = []
        querystr = "SELECT ports.device_id \
                    FROM ports \
                    JOIN ipallocations ON ports.id = ipallocations.port_id \
                    WHERE ipallocations.ip_address='%s'" % (ip)

        uuidlist = self._query(querystr, 'vm_list_by_fixed_ip', 'quantum', True)

        for uuid in uuidlist:
            vminfo = self.vm_info('uuid', uuid['device_id'])
            if vminfo:
                results.append(vminfo)

        return results

##############################################################################
# NOVA QUERIES
##############################################################################
    def vm_list(self, key, val=''):
        """ """
        if key == "all":
            querystr = "SELECT id,project_id,uuid,vm_state,hostname,host \
                        FROM instances \
                        WHERE deleted=0 ORDER BY host"
        elif key == "host":
            querystr = "SELECT id,project_id,uuid,vm_state,hostname,host \
                        FROM instances \
                        WHERE host='%s' AND deleted=0" % (val)
        elif key == "project_id":
            querystr = "SELECT id,project_id,uuid,vm_state,hostname,host \
                        FROM instances \
                        WHERE project_id='%s' AND deleted=0" % (val)
        elif key == "hostname":
            querystr = "SELECT id,project_id,uuid,vm_state,hostname,host \
                        FROM instances \
                        WHERE deleted=0 AND hostname like '%%%s%%'" % (val)

        results = self._query(querystr, 'vm_list', 'nova', True)
        return results

    def vm_info(self, key, val):
        """ """
        if key == "instance_id":
            querystr = "SELECT created_at, \
                               updated_at, \
                               id, \
                               user_id, \
                               project_id, \
                               image_ref, \
                               key_name, \
                               vm_state, \
                               hostname, \
                               host, \
                               display_name, \
                               display_description, \
                               instance_type_id,uuid \
                        FROM instances \
                        WHERE id='%s' AND deleted=0" % (val)
        elif key == "uuid":
            querystr = "SELECT created_at, \
                               updated_at, \
                               id, \
                               user_id, \
                               project_id, \
                               image_ref, \
                               key_name, \
                               vm_state, \
                               hostname, \
                               host, \
                               display_name, \
                               display_description, \
                               instance_type_id,uuid \
                        FROM instances \
                        WHERE uuid='%s' AND deleted=0" % (val)

        nova_results = self._query(querystr, 'vm_info', 'nova', False)
        return nova_results

    def flavor_by_id(self,typeid):
        """ """
        # Removed 'where deleted=0' from query as some flavors decom'd
        querystr = "SELECT * FROM instance_types WHERE id='%s'" % (typeid)

        results = self._query(querystr, 'flavor_by_id', 'nova', False)
        return results

    def cnode_info(self,sort='ASC'):
        querystr = "SELECT compute_nodes.vcpus,compute_nodes.memory_mb, \
                    compute_nodes.vcpus_used,compute_nodes.memory_mb_used, \
                    compute_nodes.running_vms,services.host,services.disabled \
                    FROM compute_nodes \
                    JOIN services ON compute_nodes.service_id=services.id \
                    ORDER BY compute_nodes.running_vms %s" % (sort)
        results = self._query(querystr, 'cnode_info', 'nova', True)
        return results

##############################################################################
# KEYSTONE QUERIES
##############################################################################
    def user_by_id(self,userid):
        """ """
        querystr = "SELECT name,extra FROM user WHERE id='%s'" % (userid)

        results = self._query(querystr, 'user_by_id', 'keystone', False)
        return results

    def project_info(self, key, val=''):
        """ """
        if key == "name":
            querystr = "SELECT id,name,description,enabled \
                        FROM project \
                        WHERE name='%s'" % (val)
        elif key == "id":
            querystr = "SELECT id,name,description,enabled \
                        FROM project \
                        WHERE id='%s'" % (val)

        results = self._query(querystr, 'project_info', 'keystone', False)
        return results

    def project_list(self):
        """ """
        querystr = "SELECT id,name,description,enabled \
                    FROM project \
                    ORDER BY name"

        results = self._query(querystr, 'projects', 'keystone', True)
        return results

    def project_members(self,projectid):
        """ """
        querystr = "SELECT user.id,user.name,user.extra,user.enabled \
                    FROM user \
                    JOIN user_project_metadata \
                    ON user.id=user_project_metadata.user_id \
                    WHERE project_id='%s' \
                    ORDER BY user.name" % (projectid)

        results = self._query(querystr, 'project_members', 'keystone', True)
        return results

##############################################################################
# QUANTUM QUERIES
##############################################################################
    def vm_ports(self,uuid):
        """ """
        querystr = "SELECT id FROM ports WHERE device_id='%s'" % (uuid)

        results = self._query(querystr, 'vm_ports', 'quantum', True)
        return results

    def netinfo_by_port_id(self,portid):
        """ """
        querystr = "SELECT ports.name as pt_name, \
                    ports.network_id, \
                    ports.mac_address, \
                    ipallocations.ip_address, \
                    ipallocations.subnet_id, \
                    ipallocations.expiration, \
                    subnets.name as sn_name, \
                    subnets.cidr, \
                    subnets.gateway_ip, \
                    floatingips.floating_ip_address, \
                    floatingips.router_id, \
                    networks.name as nt_name \
                    FROM ports \
                    LEFT JOIN ipallocations ON ports.id=ipallocations.port_id \
                    LEFT JOIN floatingips ON ipallocations.port_id=floatingips.fixed_port_id \
                    LEFT JOIN subnets ON ipallocations.subnet_id=subnets.id \
                    LEFT JOIN networks ON ports.network_id=networks.id \
                    WHERE ports.id='%s'" % (portid)

        results = self._query(querystr, 'netinfo_by_port_id', 'quantum', False)
        return results

    def dhcp_ports(self,networkid):
        """ """
        querystr = "SELECT p.id, p.mac_address, p.status, a.ip_address \
                    FROM ports p \
                    JOIN ipallocations a ON p.id = a.port_id \
                    WHERE p.device_owner='network:dhcp' \
                    AND p.network_id='%s'" % (networkid)

        results = self._query(querystr, 'dhcp_ports', 'quantum', True)
        return results

    def router(self,networkid):
        """ """
        querystr = "SELECT ports.device_id,ports.mac_address,ports.status,routers.name \
                    FROM ports \
                    JOIN routers ON ports.device_id=routers.id \
                    WHERE device_owner='network:router_interface' \
                    AND ports.network_id='%s'" % (networkid)

        results = self._query(querystr, 'router', 'quantum', False)
        return results

    def secgroups_by_port_id(self,port_id):
        """ """
        querystr = "SELECT securitygroupportbindings.security_group_id, \
                    securitygroups.name, \
                    securitygroups.description \
                    FROM securitygroupportbindings \
                    JOIN securitygroups \
                    ON securitygroupportbindings.security_group_id=securitygroups.id \
                    WHERE securitygroupportbindings.port_id='%s'" % (port_id)

        results = self._query(querystr, 'secgroups_by_port_id', 'quantum', True)
        return results

    def secgroups_by_project_id(self,projectid):
        """ """
        querystr = "SELECT id,name,description \
                    FROM securitygroups \
                    WHERE tenant_id='%s'" % (projectid)

        results = self._query(querystr, 'secgroups_by_project_id', 'quantum', True)
        return results

    def secgroup_rules(self,security_group_id):
        """ """
        querystr = "SELECT id,protocol,port_range_min,port_range_max,remote_ip_prefix \
                    FROM securitygrouprules \
                    WHERE direction='ingress' \
                    AND ethertype='IPv4' \
                    AND security_group_id='%s' \
                    ORDER BY port_range_min" % (security_group_id)

        results = self._query(querystr, 'secgroup_rules', 'quantum', True)
        return results

    def uuid_by_floating_ip(self,ip):
        """ """
        querystr = "SELECT ports.device_id as uuid\
                    FROM ports \
                    JOIN floatingips ON ports.id=floatingips.fixed_port_id \
                    WHERE floatingips.floating_ip_address='%s'" % (ip)

        results = self._query(querystr, 'uuid_by_floating_ip', 'quantum', False)
        return results

    def l3_gw(self,router_id):
        """ """
        querystr = "SELECT agents.host \
                    FROM agents \
                    JOIN routerl3agentbindings \
                    ON agents.id=routerl3agentbindings.l3_agent_id \
                    WHERE routerl3agentbindings.router_id='%s'" % (router_id)

        results = self._query(querystr, 'l3_gw', 'quantum', False)
        return results

    def floatingips(self,projectid):
        """ """
        querystr = "SELECT * \
                    FROM floatingips \
                    WHERE tenant_id='%s' \
                    ORDER BY floating_ip_address" % (projectid)

        results = self._query(querystr, 'floatingips', 'quantum', True)
        return results

##############################################################################
# CINDER QUERIES
##############################################################################
    def volume_by_uuid(self,uuid):
        """ """
        querystr = "SELECT * \
                    FROM volumes \
                    WHERE deleted=0 \
                    AND instance_uuid='%s' \
                    ORDER BY display_name" % (uuid)

        results = self._query(querystr, 'volume_by_uuid', 'cinder', True)
        return results

##############################################################################
# GLANCE QUERIES
##############################################################################
    def image_name(self,image_id):
        """ """
        querystr = "SELECT name FROM images WHERE id='%s'" % (image_id)

        results = self._query(querystr, 'image_name', 'glance', False)
        return results
