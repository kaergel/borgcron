
## borgcron

A wrapper around [borgbackup](https://github.com/borgbackup/borg) intended to run borg without user interaction via cron.

### Installation

* clone the repo

```$ git clone git@github.com:kaergel/borgcron.git```

* change to the cloned directory and install via pip

```$ cd borgcron```

```$ sudo pip install .```


### Configuration

An example configuration file can be forund at _/etc/borcron/cfg_exampl.yml_.

```
config:
    borg_options: "-v -s"
    target_repository: /your/backup/archive.attic
    wake_remote_host: False
    shutdown_remote_host: False
    remote_host_address: "192.168.2.100"
    remote_network_bcast: "192.168.2.255"
    wol_mac_address: "90:2b:34:af:c3:2d"
    shutdown_command: "sudo shutdown -h +1"
    compression: "lz4"
    prerun_script: ""
    postrun_script: ""
    directories:
        - name: /your/important/data
          namedepth: 0
          prune: True
          days: 5
          month: 12
          years: 3
        - name: /more/important/data
          namedepth: 2
          prune: True
          days: 5
          month: 12
          years: 3
        - name: /your/wifes/data
          namedepth: 1
          prune: True
          days: 5
          month: 12
          years: 3
```

**borg_options:** 
Additonal options to pass to borg backup archiver.

**target_repository:**
The path to the borg repository. See [Repository URLs](https://borgbackup.readthedocs.io/en/stable/usage/general.html#repository-urls) in borg documentation.

**wake_remote_host:**
If set to True borgcron will try to wake up the target host via WakeOnLAN.

**shutdown_remote_host:**
If set to True borgcron will try to shutdown the target after the backup.

**remote_host_address:**
Ip address of target host.

**remote_network_bcast:**
Broadcast address of target network where the WoL MagicPaket is sent.

**wol_mac_address:**
Mac address of host to turn on vi WakeOnLAN.

**shutdown_command:**
Shutdown command to be to the taget host.

**compression:**
Compression algorythm used. See [borg help compression](https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-help-compression) for details.

**prerun_script:**
Script run prior execution of borg.

**postrun_script:**
Script run after execution of borg has finished.

**directories:**
A list of dictionaries, each specifying a location to backup and related options.

**name:**
The path to a directory which is supposed to be backuped

**namedepth:**
How many parts of the source-path should be used to build the archive-name. The example configuration above would result in an borg-repository with three archives, i.e:

```
# borg list /your/backup/archive.attic
data-2018-01-15_010339                     Mon, 2018-01-15 01:03:42 [0adb14268547a3a678481ba9d07c919c17c64a71bfaf572c5bd6827c6dbb599f]
more°important°data-2018-01-15_010359      Mon, 2018-01-15 01:04:00 [0817993d27b28e1cf63b24efebcdda438ab1f57dbd4f96ac13a4c34e182406ba]
wifes°data-2018-01-15_010431               Mon, 2018-01-15 01:04:32 [952cc996416934cd5fd03c5132ebce7226823939aad2e86b81c3b4a7581288b9]
```

**prune:**
If old archives should be pruned. See [borg prune docs](https://borgbackup.readthedocs.io/en/stable/usage/prune.html).

**days:**
Number of daily archives to keep. See [borg prune docs](https://borgbackup.readthedocs.io/en/stable/usage/prune.html).

**month:**
Number of monthly archives to keep. See [borg prune docs](https://borgbackup.readthedocs.io/en/stable/usage/prune.html).

**years:**
Number of yearly archives to keep. See [borg prune docs](https://borgbackup.readthedocs.io/en/stable/usage/prune.html).

### Usage

**via cmdline:**

```borgcron /etc/borgcron/test.yml -l /root/borgcron.log```

**via cron:**

```vi /etc/cron.d/borgcron```

```
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  *     user-name   command to be executed
  0  1  *  *  *     root        /usr/bin/borgcron /etc/borgcron/test.yml -l /root/borgcron.log
```
