#!/bin/bash
    SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

    sudo timedatectl set-timezone America/Mexico_City
    sudo apt install ntp -y
    sudo service ntp stop
    sudo ntpd -gq
    sudo service ntp start

    sudo apt install git python3-dev libffi-dev python3-venv gcc libssl-dev git python3-pip python3-full
    python3 -m venv $HOME/kolla-openstack
    source $HOME/kolla-openstack/bin/activate
    pip install -U pip
    pip install 'ansible>=8,<9'
    mkdir kolla-openstack-ansible
    cd kolla-openstack-ansible
    cp $SCRIPT_DIR/ansible.cfg ansible.cfg
    pip install git+https://opendev.org/openstack/kolla-ansible@stable/2024.1
    sudo mkdir /etc/kolla
    sudo chown $USER:$USER /etc/kolla
    cp $HOME/kolla-openstack/share/kolla-ansible/etc_examples/kolla/* /etc/kolla/
    cp $HOME/kolla-openstack/share/kolla-ansible/ansible/inventory/all-in-one .
    cd $HOME/kolla-openstack
    sudo chown $USER:$USER /etc/kolla
    source ~/kolla-openstack/bin/activate
    source /etc/kolla/admin-openrc.sh
    kolla-ansible install-deps
    kolla-genpwd
    kolla-ansible -i all-in-one bootstrap-servers
    kolla-ansible -i all-in-one prechecks
    kolla-ansible -i all-in-one deploy

    pip install python-openstackclient -c https://releases.openstack.org/constraints/upper/2024.1
    pip install python-neutronclient -c https://releases.openstack.org/constraints/upper/2024.1
    pip install python-glanceclient -c https://releases.openstack.org/constraints/upper/2024.1
    pip install python-heatclient -c https://releases.openstack.org/constraints/upper/2024.1
    pip install python-magnumclient -c https://releases.openstack.org/constraints/upper/2024.1

    kolla-ansible post-deploy
    cp $SCRIPT_DIR/init-runonce init-runonce
    ./init-runonce

# Jenkins
    sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
    https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
    echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc]" \
    https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
    /etc/apt/sources.list.d/jenkins.list > /dev/null
    sudo apt-get update
    sudo apt-get install jenkins

# Ngrok

# Containerd installation
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo apt-get update
    sudo apt install -y containerd.io

    containerd config default | sudo tee /etc/containerd/config.toml > /dev/null
    sudo sed -i 's/\(SystemdCgroup = \)false$/\1true/' /etc/containerd/config.toml
    sudo service containerd restart


# Openstack configuration
    source ~/kolla-openstack/bin/activate
    source /etc/kolla/admin-openrc.sh
    WEB_PASS=$(grep keystone_admin_password /etc/kolla/passwords.yml)
    