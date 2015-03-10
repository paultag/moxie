How to set up Moxie for local development
=========================================

 * Make a Python 3 virtualenv
 * `pip install -r requirements.txt`
 * `python setup.py develop`
 * `sudo apt-get install node-uglify coffeescript node-less`
 * `make` to build JS / Less
 * Setup PostgreSQL:

```
sudo su postgres
postgres=# CREATE ROLE moxie WITH LOGIN PASSWORD 'moxie';
CREATE ROLE
postgres=# CREATE DATABASE moxie OWNER moxie;
CREATE DATABASE
postgres=# \q
postgres@helios:/home/tag/dev/sunlight/moxie$ exit
(moxie)$ moxie-init 
INFO  [alembic.migration] Context impl PostgresqlImpl.
INFO  [alembic.migration] Will assume transactional DDL.
INFO  [alembic.migration] Running stamp_revision  -> f450aba2db
```
 * Load some test stuff in:

```
(moxie)$ moxie-load eg/users.yaml
Inserting:  Paul Tagliamonte
(moxie)$ moxie-load eg/manual.yaml 
Inserting:  Paul Tagliamonte
Inserting:  test
```
 * `mkdir keys`
 * `cd keys`
 * Create a keypair

```
$ ssh-keygen -f ./key
Generating public/private rsa key pair.
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in ./key.
Your public key has been saved in ./key.pub.
```
 * `cd ..`
 * Link the key in:
 * `ln -s keys/key ./ssh_host_keys`
 * Stub out authorized keys
 * `touch authorized_keys`
 * Run!
 * `moxied`
