import fixtures
import testtools
import os
from connections import ContrailConnections
from contrail_test_init import *
from vn_test import *
from vm_test import *
from quantum_test import *
from vnc_api_test import *
from nova_test import *
from testresources import OptimisingTestSuite, TestResource 

class SolnSetup( fixtures.Fixture ):
    def __init__(self, test_resource):
        super (SolnSetup, self).__init__()
        self.test_resource= test_resource

    def setUp(self):
        super (SolnSetup, self).setUp()
        if 'PARAMS_FILE' in os.environ :
            self.ini_file= os.environ.get('PARAMS_FILE')
        else:
            self.ini_file= 'params.ini'
        self.inputs=self.useFixture(ContrailTestInit( self.ini_file))
        self.connections= ContrailConnections(self.inputs)
        self.quantum_fixture= self.connections.quantum_fixture
        self.nova_fixture = self.connections.nova_fixture
        self.vnc_lib= self.connections.vnc_lib
        self.logger= self.inputs.logger
        self.setup_common_objects()
        return self
    #end setUp

    def setup_common_objects(self):
        (self.vn1_name, self.vn1_subnets)= ("vn1", ["192.168.1.0/24"])
        (self.vn2_name, self.vn2_subnets)= ("vn2", ["192.168.2.0/24"])
        (self.fip_vn_name, self.fip_vn_subnets)= ("fip_vn", ['100.1.1.0/24'])
        (self.vn1_vm1_name, self.vn1_vm2_name)=( 'vn1_vm1', 'vn1_vm2')
        (self.vn1_vm3_name, self.vn1_vm4_name)=( 'vn1_vm3', 'vn1_vm4')
        (self.vn1_vm5_name, self.vn1_vm6_name)=( 'netperf_vn1_vm1', 'netperf_vn1_vm2')
        self.vn2_vm1_name= 'vn2_vm1'
        self.vn2_vm2_name= 'vn2_vm2'
        self.fvn_vm1_name= 'fvn_vm1'

        # Configure 3 VNs, one of them being Floating-VN
        self.vn1_fixture=self.useFixture( VNFixture(project_name= self.inputs.project_name, connections= self.connections, inputs= self.inputs, vn_name= self.vn1_name, subnets= self.vn1_subnets))
        self.vn2_fixture=self.useFixture( VNFixture(project_name= self.inputs.project_name, connections= self.connections, inputs= self.inputs, vn_name= self.vn2_name, subnets= self.vn2_subnets))
        self.fvn_fixture=self.useFixture( VNFixture(project_name= self.inputs.project_name, connections= self.connections, inputs= self.inputs, vn_name= self.fip_vn_name, subnets= self.fip_vn_subnets))

        # Making sure VM falls on diffrent compute host
        host_list=[]
        for host in self.inputs.compute_ips: host_list.append(self.inputs.host_data[host]['name'])
        compute_1 = host_list[0]
        compute_2 = host_list[0]
        if len(host_list) > 1:
            compute_1 = host_list[0]
            compute_2 = host_list[1]
        # Configure 6 VMs in VN1, 1 VM in VN2, and 1 VM in FVN
        self.vn1_vm5_fixture=self.useFixture(VMFixture(project_name= self.inputs.project_name, connections= self.connections, vn_obj= self.vn1_fixture.obj, vm_name= self.vn1_vm5_name, image_name='ubuntu-netperf'))
        self.vn1_vm6_fixture=self.useFixture(VMFixture(project_name= self.inputs.project_name, connections= self.connections, vn_obj= self.vn1_fixture.obj, vm_name= self.vn1_vm6_name, image_name='ubuntu-netperf'))
        self.vn1_vm3_fixture=self.useFixture(VMFixture(project_name= self.inputs.project_name, connections= self.connections, vn_obj= self.vn1_fixture.obj, vm_name= self.vn1_vm3_name))
        self.vn1_vm1_fixture=self.useFixture(VMFixture(project_name= self.inputs.project_name, connections= self.connections, vn_obj= self.vn1_fixture.obj, vm_name= self.vn1_vm1_name,image_name='ubuntu-traffic',ram='4096', node_name=compute_1))
        self.vn1_vm2_fixture=self.useFixture(VMFixture(project_name= self.inputs.project_name, connections= self.connections, vn_obj= self.vn1_fixture.obj, vm_name= self.vn1_vm2_name , image_name='ubuntu-traffic',ram='4096'))
        self.vn1_vm3_fixture=self.useFixture(VMFixture(project_name= self.inputs.project_name, connections= self.connections, vn_obj= self.vn1_fixture.obj, vm_name= self.vn1_vm3_name))
        self.vn1_vm4_fixture=self.useFixture(VMFixture( image_name = 'redmine-fe', project_name= self.inputs.project_name, connections= self.connections, vn_obj= self.vn1_fixture.obj, vm_name= self.vn1_vm4_name))
        self.vn2_vm1_fixture=self.useFixture(VMFixture( image_name = 'redmine-be', project_name= self.inputs.project_name, connections= self.connections, vn_obj= self.vn2_fixture.obj, vm_name= self.vn2_vm1_name))
        self.vn2_vm2_fixture=self.useFixture(VMFixture(project_name= self.inputs.project_name, connections= self.connections, vn_obj= self.vn2_fixture.obj, vm_name= self.vn2_vm2_name, image_name='ubuntu-traffic', ram='4096', node_name=compute_2))
        self.fvn_vm1_fixture=self.useFixture(VMFixture(project_name= self.inputs.project_name, connections= self.connections, vn_obj= self.fvn_fixture.obj, vm_name= self.fvn_vm1_name))
        self.verify_common_objects()
        self.set_sec_group_for_mx_tests(self.inputs.project_fq_name)
    #end setup_common_objects
    
    def set_sec_group_for_mx_tests(self, project_name):
        self.logger.info("Adding rules to the default security group")
        project = self.vnc_lib.project_read(fq_name = self.inputs.project_fq_name)
        def_sec_grp = self.vnc_lib.security_group_read(fq_name= [u'default-domain', u'admin', u'default'])
        rule1= [{'direction' : '>',
                 'protocol' : 'any',
                 'dst_addresses': [{'security_group': 'local', 'subnet' : None}],
                 'dst_ports': [{'start_port' : 0, 'end_port' : 65535}],
                 'src_ports': [{'start_port' : 0, 'end_port' : 65535}],
                 'src_addresses': [{'subnet' : {'ip_prefix' : '0.0.0.0', 'ip_prefix_len' : 0}}],
                 },
                 {'direction' : '>',
                  'protocol' : 'any',      
                  'src_addresses': [{'security_group': 'local', 'subnet' : None}],
                  'src_ports': [{'start_port' : 0, 'end_port' : 65535}],
                  'dst_ports': [{'start_port' : 0, 'end_port' : 65535}],
                  'dst_addresses': [{'subnet' : {'ip_prefix' : '0.0.0.0', 'ip_prefix_len' : 0}}],
                  },
                 ]
        rule_list= PolicyEntriesType(policy_rule=rule1)
        def_sec_grp = SecurityGroup(name= 'default', parent_obj= project, security_group_entries= rule_list)
        def_sec_grp.set_security_group_entries(rule_list)
        self.vnc_lib.security_group_update(def_sec_grp)
    #end set_sec_group_for_mx_tests

    def verify_common_objects(self):
        assert self.vn1_fixture.verify_on_setup()
        assert self.vn2_fixture.verify_on_setup()
        assert self.fvn_fixture.verify_on_setup()
        assert self.vn1_vm1_fixture.verify_on_setup()
        assert self.vn1_vm2_fixture.verify_on_setup()
        assert self.vn1_vm3_fixture.verify_on_setup()
        assert self.vn1_vm4_fixture.verify_on_setup()
        assert self.vn1_vm5_fixture.verify_on_setup()
        assert self.vn1_vm6_fixture.verify_on_setup()
        assert self.vn2_vm1_fixture.verify_on_setup()
        assert self.vn2_vm2_fixture.verify_on_setup()
        assert self.fvn_vm1_fixture.verify_on_setup()
    #end verify_common_objects
        
    def tearDown(self):
        print "Tearing down resources"
        super(SolnSetup, self).cleanUp()
        print"Deleting the rules of default SG" 
        def_sec_grp = self.vnc_lib.security_group_read(fq_name= [u'default-domain', u'admin', u'default'])
        rules_list= def_sec_grp.get_security_group_entries().get_policy_rule()
        for i in range(len(rules_list)):
            def_sec_grp = self.vnc_lib.security_group_read(fq_name= [u'default-domain', u'admin', u'default'])
            policy_rule= def_sec_grp.get_security_group_entries().get_policy_rule()[0]
            def_sec_grp.get_security_group_entries().delete_policy_rule(policy_rule)
            self.vnc_lib.security_group_update(def_sec_grp)

    def dirtied(self):
        self.test_resource.dirtied(self)

class _SolnSetupResource(TestResource):
    def make(self, dependencyresource):
        base_setup= SolnSetup( self)
        base_setup.setUp()
        return base_setup
    #end make

    def clean(self, base_setup):
        print "Am cleaning up here"
#        super(_SolnSetupResource,self).clean()
        base_setup.tearDown()
    #end

SolnSetupResource= _SolnSetupResource()


