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

# Ngrok



# on a Fedora linux system
# Creation of fedora coreos image
STREAM='stable'
coreos-installer download --decompress -s $STREAM -p openstack -f qcow2.xz
FILE=fedora-coreos-XX.XXXXXXXX.X.X-openstack.x86_64.qcow2
scp ./$FILE toor@10.0.11.101:~/

# On the ubuntu server
FILE=fedora-coreos-XX.XXXXXXXX.X.X-openstack.x86_64.qcow2
IMAGE=${FILE:0:-6} # remove extension .qcow2

# K8s intallation<
    sudo apt-get update
    # apt-transport-https may be a dummy package; if so, you can skip that package
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg


    # If the folder `/etc/apt/keyrings` does not exist, it should be created before the curl command, read the note below.
    # sudo mkdir -p -m 755 /etc/apt/keyrings
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
    sudo chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg # allow unprivileged APT programs to read this keyring

    # This overwrites any existing configuration in /etc/apt/sources.list.d/kubernetes.list
    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
    sudo chmod 644 /etc/apt/sources.list.d/kubernetes.list   # helps tools such as command-not-found to work correctly

    sudo apt-get update
    sudo apt-get install -y kubectl kubeadm kubelet
    # Hold, because k8s tends to be volatile with updates
    sudo apt-mark hold kubeadm kubectl kubelet

# Containerd installation
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo apt-get update
    sudo apt install -y containerd.io

    containerd config default | sudo tee /etc/containerd/config.toml > /dev/null
    sudo sed -i 's/\(SystemdCgroup = \)false$/\1true/' /etc/containerd/config.toml
    sudo service containerd restart

# Swap might negatively affect K8s
    sudo swapoff -a
    sudo sed -i '/swap/s/^/#/' /etc/fstab

# ip tables
    sudo modprobe br_netfilter
    echo br_netfilter | sudo tee /etc/modules-load.d/kubernetes.conf


# Create K8s cluster config
    sudo kubeadm init --pod-network-cidr=10.244.0.0/16
    mkdir -p $HOME/.kube
    sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Magnum CAPI installation
sudo usermod -aG docker toor
sudo docker exec -it -u0 magnum_api bash
    apt update
    apt install wget
    pip install magnum-cluster-api
    wget https://get.helm.sh/helm-v3.13.2-linux-amd64.tar.gz
    tar -zxvf helm-v3.13.2-linux-amd64.tar.gz
    mv linux-amd64/helm /usr/local/bin

sudo docker exec -it -u0 magnum_conductor bash
    apt update
    apt install wget
    pip install magnum-cluster-api
    wget https://get.helm.sh/helm-v3.13.2-linux-amd64.tar.gz
    tar -zxvf helm-v3.13.2-linux-amd64.tar.gz
    mv linux-amd64/helm /usr/local/bin

    sudo docker exec -it -u0 magnum_conductor mkdir /var/lib/magnum/.kube
    sudo docker exec -it -u0 magnum_api mkdir /var/lib/magnum/.kube
    sudo docker cp ~/.kube/  magnum_api:/var/lib/magnum/
    sudo docker cp ~/.kube/  magnum_conductor:/var/lib/magnum/
    sudo docker exec -it -u0 magnum_api chown magnum:magnum /var/lib/magnum/.kube/config
    sudo docker exec -it -u0 magnum_conductor chown magnum:magnum /var/lib/magnum/.kube/config

    sudo docker restart magnum_api magnum_conductor


# Openstack configuration
    source ~/kolla-openstack/bin/activate
    source /etc/kolla/admin-openrc.sh
    WEB_PASS=$(grep keystone_admin_password /etc/kolla/passwords.yml)
    openstack image create
        --disk-format=qcow2                                     \
        --min-disk=10                                           \
        --min-ram=2                                             \
        --progress                                              \
        --file=$FILE $IMAGE                                     \
        --property os_distro='fedora-coreos'                    
    
    openstack coe cluster template create base-cluster-template \
        --coe kubernetes                                        \
        --image $IMAGE                                          \
        --keypair mykey                                         \
        --external-network public1                              \
        --fixed-network demo-net                                \
        --fixed-subnet demo-subnet                              \
        --dns-nameserver 10.0.11.254                            \
        --flavor m1.medium                                      \
        --master-flavor m1.medium                               \
        --volume-driver cinder                                  \
        --docker-volume-size 5                                  \
        --network-driver flannel                                \
        --docker-storage-driver overlay2