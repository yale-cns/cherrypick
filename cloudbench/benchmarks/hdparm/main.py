from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug

import re

TIMEOUT=3600

def hdparm(vm, env):
    output = {}

    # Warm up
    for i in range(0, 5):
        vm.script("hdparm -t %s | tail -n 1" % vm.root_disk())

    res = vm.script("hdparm -t %s | tail -n 1" % vm.root_disk())
    speed = float(re.search('(\d+(\.\d*)?) (?:MB/sec)', res).group(1))

    res = vm.script("hdparm --direct -t %s | tail -n 1" % vm.root_disk())
    raw_speed = float(re.search('(\d+(\.\d*)?) (?:MB/sec)', res).group(1))

    res = vm.script("sync; ( time bash -c '(dd if=/dev/zero of=bf bs=8k count=500000; sync)' ) |& tail -n 3 | head -n 1")
    match = re.search("(\d+)m(\d+)\.(\d+)s", res)
    minutes = float(match.group(1))
    seconds = float(match.group(2))
    milliseconds = float(match.group(3))
    write = (500000*8192/((minutes * 60 + seconds + milliseconds/1000.0) * 1024 * 1024))

    output = {}
    output['server_location'] = vm.location().location
    output['hdparm_read'] = speed
    output['hdparm_raw_read'] = raw_speed
    output['hdparm_write'] = write

    return output

def hdparm_test(vms, env):
    vm = vms[0]

    # Install the new kernel
    #vm.install('kernel4')
    vm.install('hdparm')

    results = hdparm(vm, env)
    print results

def run(env):
    vm1 = env.vm('vm1')

    env.benchmark.executor([vm1], hdparm_test)
    env.benchmark.executor.run()
    #env.benchmark.executor.stop()

