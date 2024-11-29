import openstack
import time

# TODO: Replace with .env file
ENV = {
	"user"      : "admin",
	"password"  : "0DlK10VnOHvbgpJY5hzHkX1nRKTyajLuaW93qu8O",
	"domain"    : "default",
	"project"   : "admin",
	"host"      : "openstack",
	"server"    : "http://10.0.11.101",
	"key_name"  : "mykey",
    "stack_name": "web-page-stack",
	"availability_zone": "nova",
	"flavor":"ds1G",
    "endpoints": {
		"auth"     : ":5000/v3",
		"token"    : ":5000/v3/auth/tokens",
		"images"   : ":9292/v2/images",
		"compute"  : ":8774/v2.1/servers",
		"flavors"  : ":8774/v2.1/flavors",
		"networks" : ":9696/networking/v2.0/networks",
		"projects" : ":5000/v3/auth/projects",
        "container": "::9517/v1/containers"
	}
}


conn = openstack.connect(
    auth_url           =ENV["server"] + ENV["endpoints"]["auth"],
    project_name       =ENV["project"],
    username           =ENV["user"],
    password           =ENV["password"],
    user_domain_name   ="default",
    project_domain_name="default",
)

def create_stack(conn, template):
    stack_name = ENV["stack_name"]
    return conn.orchestration.create_stack(stack_name, template=template)

def update_stack(conn: openstack.connection.Connection) -> openstack.orchestration.v1.stack.Stack:
    
    stack_name = ENV["stack_name"]

    template_file = "zun_autoscale_template.yml"
    with open(template_file, 'r') as f:
        template = f.read()

    # if the stack doesn't exist, create it
    if conn.orchestration.find_stack(stack_name, ignore_missing=True) == None:
        return create_stack(conn, template)        
    
    # if the stack exists, update it
    return conn.orchestration.update_stack(stack_name, template=template)

def create_container(conn: openstack.connection.Connection):
    container_params = {
        "name": "barpo kabalto",
        "image": "alpine:latest",           # Specify the container image
        "command": "/bin/bash",             # Command to run in the container
        "cpu": 1.0,                         # Number of CPU units
        "memory": "512m",                   # Memory limit
        #"environment": {"KEY": "VALUE"},   # Environment variables
        "labels": {"app": "test"},          # Labels for the container
        "workdir": "/home",                 # Working directory inside the container
    }

    print(conn.container)
    #conn.container.create_container(**container_params)

def delete_containers(conn: openstack.connection.Connection, name):
    #conn.container
    pass

create_container(conn)