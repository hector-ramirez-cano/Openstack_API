import requests
import sys
import json

# TODO: Replace with .env file
ENV = {
	"user": "admin",
	"password": "12345678",
	"domain": "default",
	"project": "demo",
	"host": "openstack",
	"availability_zone": "nova",
	"server": "http://10.147.20.2",
	"image_name": "Ubuntu-22.04.5",
	"flavor":"m1.small",
	"endpoints": {
		"token"   : "/identity/v3/auth/tokens",
		"images"  : "/image/v2/images",
		"compute" : "/compute/v2.1/servers",
		"flavors" : "/compute/v2.1/flavors",
		"networks": ":9696/networking/v2.0/networks",
		"projects": "/identity/v3/auth/projects",
	}
}

def find_by_name(arr, name: str):
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


def create_vm(token):
	url      = ENV["server"]+ENV["endpoints"]["compute"]
	headers  = {"Content-type":"application/json", "X-Auth-Token": token}
	images   = list_images  (token)
	flavors  = list_flavors (token)
	networks = list_networks(token)
	project  = list_projects(token)

	image   = find_by_name(images ["images" ], ENV["image_name"])
	flavor  = find_by_name(flavors["flavors"], ENV["flavor"]    )
	network = [
		find_by_name(networks["networks"], "public"),
		find_by_name(networks["networks"], "private"),
	]

	body = {
		"server": {
			# "host"      : ENV["host"],
			"name"      : "example-server",
			"imageRef"  : image["id"],
			"flavorRef" : flavor["id"],
			"networks"  : [
				{ "uuid": network[0]["id"] },
				# { "uuid": network[1]["id"] },
			],
			"key_name"         : "production_vm_key",
			"availability_zone": ENV["availability_zone"],
			"metadata": {
				"description": "Test server instance"
			},
		}
	}

	response = requests.post(url=url, json=body, headers=headers)

	print(body)
	print(response.status_code, json.loads(response.content.decode("utf-8")))


token = get_token()
instances = list_instances(token)

create_vm(token)

# print(find_by_name(flavors["flavors"], "m1.small"))
# print(find_by_name(images["images"], "Ubuntu-22.04.5"))

# print(servers)