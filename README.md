
## borgcron

A wrapper around [borgbackup](https://github.com/borgbackup/borg) intended to run without user interaction via cron.

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
    # dir_attic_flags: additional flags for borg
    # dir_target_repo: attic repository where dirs get stored
    dir_attic_flags: "-v -s"
    dir_target_repo: /your/backup/archive.attic
    dir_script_pre: ""
    dir_script_post: ""
    dirs:
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

**dir_attic_flags:** 
Additonal options to pass to borg backup archiver.

**dir_target_repo:**
The path to the borg repository. See [Repository URLs](https://borgbackup.readthedocs.io/en/stable/usage/general.html#repository-urls) in borg documentation.

**dir_script_pre:**
Script run prior execution of borg-

**dir_script_post:**
Script run after execution of borg has finished.

**dirs:**
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
