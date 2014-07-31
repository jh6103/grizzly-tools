#!/usr/bin/env python

import ConfigParser
import MySQLdb
import MySQLdb.cursors
import os

# Terminal info
colorize = True
if os.environ['TERM'] == "xterm" and colorize:
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
            self._dbclose()
            return results
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
# NOVA QUERIES
##############################################################################
    def vm_list(self, key, val=''):
        """ """
        if key == "all":
            querystr = "SELECT id,host,project_id,uuid,vm_state,hostname \
                        FROM instances \
                        WHERE deleted=0 ORDER BY host"
        elif key == "host":
            querystr = "SELECT id,host,project_id,uuid,vm_state,hostname \
                        FROM instances \
                        WHERE host='%s' AND deleted=0" % (val)
        elif key == "project_id":
            querystr = "SELECT id,host,project_id,uuid,vm_state,hostname \
                        FROM instances \
                        WHERE project_id='%s' AND deleted=0" % (val)
        elif key == "hostname":
            querystr = "SELECT id,host,project_id,uuid,vm_state,hostname \
                        FROM instances \
                        WHERE deleted=0 AND hostname like '%%%s%%'" % (val)

        results = self._query(querystr, 'vm_list', 'nova', True)
        return results

    def vm_info(self, key, val):
        """ """
        if key == "instance_id":
            querystr = "SELECT created_at,id,user_id,project_id,vm_state,hostname,host,instance_type_id,uuid \
                        FROM instances \
                        WHERE id='%s' AND deleted=0" % (val)
        if key == "uuid":
            querystr = "SELECT created_at,id,user_id,project_id,vm_state,hostname,host,instance_type_id,uuid \
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
        querystr = "SELECT compute_nodes.vcpus,compute_nodes.memory_mb,compute_nodes.vcpus_used, \
                    compute_nodes.memory_mb_used,compute_nodes.running_vms,services.host,services.disabled \
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

    def project_by_id(self,projectid):
        """ """
        querystr = "SELECT name,extra,description FROM project WHERE id='%s'" % (projectid)

        results = self._query(querystr, 'project_by_id', 'keystone', False)
        return results

##############################################################################
# QUANTUM QUERIES
##############################################################################
    def network_by_uuid(self,uuid):
        """ """
        querystr = "SELECT ports.id, \
                    ports.network_id, \
                    ports.mac_address, \
                    ipallocations.ip_address, \
                    ipallocations.subnet_id, \
                    ipallocations.expiration, \
                    subnets.cidr, \
                    floatingips.floating_ip_address, \
                    floatingips.router_id, \
                    subnets.name as sn_name, \
                    routers.name as rt_name, \
                    networks.name as nt_name \
                    FROM ports \
                    LEFT JOIN ipallocations ON ports.id = ipallocations.port_id \
                    LEFT JOIN floatingips ON ipallocations.port_id = floatingips.fixed_port_id \
                    LEFT JOIN subnets ON ipallocations.subnet_id = subnets.id \
                    LEFT JOIN routers ON floatingips.router_id = routers.id \
                    LEFT JOIN networks ON ports.network_id = networks.id \
                    WHERE ports.device_id='%s'" % (uuid)

        results = self._query(querystr, 'network_by_uuid', 'quantum', False)
        return results

    def secgroups_by_port_id(self,port_id):
        """ """
        querystr = "SELECT securitygroupportbindings.security_group_id, \
                    securitygroups.name, \
                    securitygroups.description \
                    FROM securitygroupportbindings \
                    JOIN securitygroups ON securitygroupportbindings.security_group_id = securitygroups.id \
                    WHERE securitygroupportbindings.port_id='%s'" % (port_id)

        results = self._query(querystr, 'secgroups_by_port_id', 'quantum', True)
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
                    JOIN floatingips ON ports.id = floatingips.fixed_port_id \
                    WHERE floatingips.floating_ip_address='%s'" % (ip)

        results = self._query(querystr, 'uuid_by_floating_ip', 'quantum', False)
        return results

##############################################################################
# CINDER QUERIES
##############################################################################
    def volume_by_uuid(self,uuid):
        """ """
        querystr = "SELECT * FROM volumes WHERE deleted=0 AND instance_uuid='%s' ORDER BY display_name" % (uuid)

        results = self._query(querystr, 'volume_by_uuid', 'cinder', True)
        return results
