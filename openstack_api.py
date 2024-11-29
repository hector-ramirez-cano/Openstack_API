import requests
import sys
import json

from time import sleep

# TODO: Replace with .env file
ENV = {
	"user"      : "admin",
	"password"  : "0DlK10VnOHvbgpJY5hzHkX1nRKTyajLuaW93qu8O",
	"domain"    : "default",
	"project"   : "admin",
	"host"      : "openstack",
	"server"    : "http://10.0.11.101",
	"key_name"  : "mykey",
	"availability_zone": "nova",
	"container_name": "barpo-kabalto",
	"flavor":"ds1G",
	"endpoints": {
		"token"   : ":5000/v3/auth/tokens",
		"images"  : ":9292/v2/images",
		"compute" : ":8774/v2.1/servers",
		"flavors" : ":8774/v2.1/flavors",
		"networks": ":9696/v2.0/networks",
		"projects": ":5000/v3/auth/projects",
		"container": ":9517/v1/containers"
	}
}

def find_all_by_name(arr, name:str):
	found = []
	for element in arr:
		if element["name"] == name:
			found.append(element)
	
	return found

def find_first_by_name(arr, name: str):
	for element in arr:
		if element["name"] == name:
			return element


def get_token():
	headers = {"Content-type":"application/json"}

	data = {
		"auth": {
			"identity": {
				"methods": ["password"],
				"password": {
					"user": {
						"name": ENV["user"],
						"domain": { "name": ENV["domain"] },
						"password": ENV["password"]
					}
				}
			},
			"scope": {
				"project": {
					"name": ENV["project"],
					"domain": { "name": ENV["domain"] }
				}
			}
		}
	}

	url = ENV["server"] + ENV["endpoints"]["token"]
	response = requests.post(url, headers=headers, json=data)

	if response.status_code != 201:
		print("[ERROR]Failed to obtain token. Server returned error:", response.status_code, response.content, file=sys.stderr, flush=True)
		exit(1)
	
	print("[INFO ]Obtained Token successfully")
	return response.headers["X-Subject-Token"]


def list_endpoint(token, endpoint, expected_code, on_success_msg, unwrap_message):
	headers = {"Content-type":"application/json", "X-Auth-Token": token}

	url = ENV["server"]+endpoint

	response = requests.get(url, headers=headers)

	if response.status_code != expected_code:
		print(unwrap_message, "Http code=", response.status_code, response.content, file=sys.stderr, flush=True)
		sys.exit(1)
	
	print(on_success_msg)
	return json.loads(response.content.decode("utf-8"))


def list_images(token):
	endpoint = ENV["endpoints"]["images"]
	expected_code = 200
	on_success_msg = "[INFO ]Listed images successfully"
	unwrap_message = "[ERROR]Failed to list images. "
	return list_endpoint(token, endpoint, expected_code, on_success_msg, unwrap_message)
	

def list_flavors(token):
	endpoint = ENV["endpoints"]["flavors"]
	expected_code = 200
	on_success_msg = "[INFO ]Listed flavors successfully"
	unwrap_message = "[ERROR]Failed to list flavors. "
	return list_endpoint(token, endpoint, expected_code, on_success_msg, unwrap_message)


def list_instances(token):
	endpoint = ENV["endpoints"]["compute"]
	expected_code = 200
	on_success_msg = "[INFO ]Listed instances successfully"
	unwrap_message = "[ERROR]Failed to list instances. "
	return list_endpoint(token, endpoint, expected_code, on_success_msg, unwrap_message)


def list_networks(token):
	endpoint = ENV["endpoints"]["networks"]
	expected_code = 200
	on_success_msg = "[INFO ]Listed instances successfully"
	unwrap_message = "[ERROR]Failed to list instances. "
	return list_endpoint(token, endpoint, expected_code, on_success_msg, unwrap_message)


def list_projects(token):
	endpoint = ENV["endpoints"]["projects"]
	expected_code = 200
	on_success_msg = "[INFO ]Listed projects successfully"
	unwrap_message = "[ERROR]Failed to list projects."
	return list_endpoint(token, endpoint, expected_code, on_success_msg, unwrap_message)


def list_containers(token):
	endpoint = ENV["endpoints"]["container"]
	expected_code = 200
	on_success_msg = "[INFO ]Listed containers successfully"
	unwrap_message = "[ERROR]Failed to list containers."
	return list_endpoint(token, endpoint, expected_code, on_success_msg, unwrap_message)


def create_vm(token, image):
	url      = ENV["server"]+ENV["endpoints"]["compute"]
	headers  = {"Content-type":"application/json", "X-Auth-Token": token}
	images   = list_images  (token)
	flavors  = list_flavors (token)
	networks = list_networks(token)
	project  = list_projects(token)

	image   = find_first_by_name(images ["images" ], image)
	flavor  = find_first_by_name(flavors["flavors"], ENV["flavor"]    )
	network = [
		find_first_by_name(networks["networks"], "public"),
		find_first_by_name(networks["networks"], "private"),
	]

	body = {
		"server": {
			"name"      : "example-server",
			"imageRef"  : image["id"],
			"flavorRef" : flavor["id"],
			"networks"  : [
				{ "uuid": network[0]["id"] },
				{ "uuid": network[1]["id"] },
			],
			"key_name"         : ENV["key_name"],
			"availability_zone": ENV["availability_zone"],
			"metadata": {
				"description": "Test server instance"
			},
		}
	}

	response = requests.post(url=url, json=body, headers=headers)

	print(body)
	print(response.status_code, json.loads(response.content.decode("utf-8")))



def create_container(token, image):
	url      = ENV["server"]+ENV["endpoints"]["container"]
	headers  = {"Content-type":"application/json", "X-Auth-Token": token}
	networks = list_networks(token)
	
	network = [
		find_first_by_name(networks["networks"], "net-ext"),
		#find_first_by_name(networks["networks"], "private"),
	]

	body = {
		"name"      : ENV["container_name"],
		"image"     : image,
		"cpu"       : 1.0,
		"memory"    : 512,
		"availability_zone": ENV["availability_zone"],
		"nets": [
			{
				"v4-fixed-ip": "192.168.1.80",
				"network": network[0]["id"],
			}
    	],
		"security_groups": ["default"],
	}

	print(body)
	
	response = requests.post(url=url, json=body, headers=headers)
	response_body = json.loads(response.content.decode("utf-8"))

	if response.status_code != 202:
		print(f"[ERROR]Failed to create container with error {response.status_code}\n {response_body}")
		exit(1)

	url = url + "/" + response_body["uuid"]+"/start"

	sleep(10)

	response = requests.post(url=url, headers=headers)
	response_body = json.loads(response.content.decode("utf-8"))

	if response.status_code != 202:
		print(f"[ERROR]Failed to start container with error {response.status_code}\n {response_body}")
		exit(1)




def delete_containers_by_name(token, name):
	containers = list_containers(token)
	containers = find_all_by_name(containers["containers"], name)
	headers = {"Content-type":"application/json", "X-Auth-Token": token}
	url = ENV["server"]+ENV["endpoints"]["container"]

	for container in containers:
		response = requests.post(url+"/"+container["uuid"]+"/stop", headers=headers)
		print(response.status_code)

	sleep(5)


	for container in containers:
		response = requests.delete(url+"/"+container["uuid"], headers=headers)
		print(response.status_code, response.content)



def delete_vms_by_name(token, name):
	instances = list_instances(token)
	instances = find_all_by_name(instances["instances"], name)
	headers = {"Content-type":"application/json", "X-Auth-Token": token}
	url = ENV["server"]+ENV["endpoints"]["compute"]

	for instance in instances:
		response = request.post(url+"/"+instance["id"]+"/stop", headers=headers)
		print(response.status_code)

	sleep(10)

	for instance in instances:
		response = requests.delete(url+"/"+instance["id"], headers=headers)
		print(response.status_code)

def refresh_container(token):
	print("[INFO ]Deleting old containers")
	delete_containers_by_name(token, ENV["container_name"])

	print("[INFO ]Creating new containers")
	create_container(token, "jaimelegor/vite-react-app:v5")

token = get_token()
#create_container(token, "jaimelegor/vite-react-app:latest")
#delete_containers_by_name(token, ENV["container_name"])

refresh_container(token)