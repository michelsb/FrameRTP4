# FrameRTP4 Prototype

## Introduction

Repository for SFCMon, an efficient and scalable monitoring solution to keep track network  ows in SFC-enabled domains.

## Software requirements

The virtualization software is portable and should run on a few OSes:

  * Linux
  * Windows PowerShell 3 or later
  * FreeBSD
  * Mac OS X
  * Solaris

## Obtaining required software

The following applications are required:

  * Vagrant: https://www.vagrantup.com/downloads.html
  * VirtualBox: https://www.virtualbox.org/wiki/Downloads

You will need to build a virtual machine. For this, follow the steps below:

 1. Install VirtualBox;
 2. Install Vagrant (use the site installer even on Linux);
 3. Install Vagrant plugins:
 
        # Install vagrant-disksize plugin.
        vagrant plugin install vagrant-disksize
        
 4. Download or clone the SFCMon repository: 
 
         # Clone the git repo.
         git clone https://github.com/michelsb/SFCMon.git
 
 5. Deploy the VM with vagrant (install all P4 dependencies):
 
         # Go to the appropriated directory.
         cd SFCMon/create-dev-env

         # Deploy the VM with vagrant.
         vagrant up
 
Other auxiliary commands:

         # Access the VM: 
         vagrant ssh
        
         # Halt the VM: 
         vagrant halt (outside VM)
         sudo shutdown -h now (inside VM)
      
         # Destroy the VM: 
         vagrant destroy

## Custom hash functions

The SFCMon requires custom hash functions that use different unique primes for each stage, so that the same flow can be hashed to multiple slots in the hash table in multiple stages. Below, we describe the operations required to enable the new hash functions.

First, we need to access the VM:

         # Go to the appropriated directory.
         cd SFCMon/create-dev-env

         # Access the VM.
         vagrant ssh

Second, we need to extend behavioral-model (bmv2), a public-domain P4 virtual switch, to enable support for multiple pairwise independent hash functions. For this, we implemented the algorithm MurmurHash35, which yields the 32-bit hash value. Next, we define 22 independent hash functions by just varying the seed of MurmurHash3. Adding these hash functions to the behavioral-model is simple. Please, follow the steps below:

 1. Replace the original simple_switch.cpp for our extended file:

        sudo cp /srv/p4-extensions/simple_switch.cpp ~/behavioral-model/targets/simple_switch/simple_switch.cpp

 2. Once doing this remake bmv2:

        NUM_CORES=`grep -c ^processor /proc/cpuinfo`
        cd ~/behavioral-model
        ./autogen.sh
        ./configure --enable-debugger --with-pi
        make -j${NUM_CORES}
        sudo make install

        # Simple_switch_grpc target
        cd targets/simple_switch_grpc
        ./autogen.sh
        ./configure --with-thrift
        make -j${NUM_CORES}
        sudo make install

Finally, we need to update some p4c files in order to make the new hash functions available for P4 programs. Please, follow the steps below:

 1. Replace the following files for our extending files:

        sudo cp /srv/p4-extensions/v1model.p4 ~/p4c/p4include/v1model.p4
        sudo cp /srv/p4-extensions/v1model.h ~/p4c/frontends/p4/fromv1.0/v1model.h
        sudo cp /srv/p4-extensions/simpleSwitch.cpp ~/p4c/backends/bmv2/simpleSwitch.cpp

 2. Once doing this remake p4c:

        cd ~/p4c/build
        sudo make uninstall
        cd ..
        rm -rf build
        mkdir -p build
        cd build
        cmake ..
        make -j${NUM_CORES}
        make -j${NUM_CORES} check
        sudo make install

## Usage

For the WPIETF 2019, we performed two experiments:

 1. To evaluate the SFCMon's ability to detect large flows, we developed a Python program that simulates its execution.
* [SFCMon Simulator](./project/wpietf2019/sfcmon-simulator)
 
 2. We implement a Proof-of-Concept (PoC) framework aiming to validate and evaluate the SFCMon. By using our PoC framework, we perform experiments aiming to evaluate the SFCMon regarding its performance and scalability.
* [SFCMon's PoC](./project/wpietf2019/testbed) 

## Notes

This work was partially funded by the National Science Foundation (NSF-USA) and the Rede Nacional de Ensino e Pesquisa (RNP-Brazil) under the "EAGER: USBRCCR: Securing Networks in the Programmable Data Plane" project.
