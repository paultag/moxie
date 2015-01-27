Installation for AWS Debian Jessie
==================================


Security Groups
---------------

Make sure port 80 is usable; same with port 2222, and in the SG for whatever
it needs to talk with.


Notes
-----

I highly encourage using Docker with Overlay, not aufs, nor devicemapper. This
requires kernel 3.18+; so we'll have to fix that. Feel free to not do that
and use aufs if you'd like.


Initial Setup
-------------

    # apt-get update
    # apt-get dist-upgrade -y

Great. Now we need to install some experimental stuff. Literally. The Debian
Kernel for 3.18 is only present in the `experimental` / `rc-buggy` suite
(because of the Jessie freeze), so let's roll with that.

    # nano /etc/apt/sources.list

Append:

    deb http://cloudfront.debian.net/debian experimental main
    deb-src http://cloudfront.debian.net/debian experimental main

to the file. Now let's install the new kernel:

    # apt-get update && apt-get install linux-image-3.18
    # update-grub

Now, let's bounce the instance (from the AWS console run
Actions -> Instance State -> Reboot)

Wait a hot second, and ssh back in. Let's ensure the kernel's running:

    # uname -a
    Linux ip-10-111-189-167 3.18.0-trunk-amd64 #1 SMP Debian 3.18.3-1~exp1 (2015-01-18) x86_64 GNU/Linux

Fannntastic. Now, let's set up the EBS.

    # mkfs.ext4 /dev/xvdf
    # mkdir /projects
    # nano /etc/fstab

and append:

    /dev/xvdf /projects ext4 defaults 1 1

Now mount:

    # mount /projects
    # ln -s /projects/docker /var/lib/docker
    # mkdir /projects/docker

Yay. OK. So; let's get Docker installed.

    # apt-get install docker.io
    # usermod -a -G docker admin
    $ wget https://get.docker.com/builds/Linux/x86_64/docker-latest -O docker
    $ chmod +x docker
    # cp docker /usr/bin/docker
    # nano /etc/default/docker

Set content to:

    DOCKER_OPTS="-H unix:///var/run/docker.sock -s overlay"

Great; now let's restart:

    # service docker restart

And, log out and back in to see your new group (check with `groups(1)`)

Now, let's verify the setup:

    # docker info | grep Storage
    Storage Driver: overlay


