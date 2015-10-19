from cloudbench.ssh import WaitUntilFinished, WaitForSeconds
from cloudbench.util import Debug, parallel

from cloudbench.apps.hadoop import HADOOP_USER
from cloudbench.cluster.hadoop import HadoopCluster
from cloudbench.cluster.hive import HiveCluster

import re
import time

TIMEOUT=21600

TERASORT_INPUT='/home/{0}/terasort-input'.format(HADOOP_USER)
TERASORT_OUTPUT='/home/{0}/terasort-output'.format(HADOOP_USER)


def terasort_with_argos_run(vms, env):
    def collect_stats(vms, fname):
        for vm in vms:
            cpu  = vm.script("cat /proc/stat")
            disk = vm.script("cat /proc/diskstats")
            netw = vm.script("cat /proc/net/dev")
            time = vm.script("cat /proc/uptime")

            t = time.strip().split(" ")[0]

            with open(vm.name + '-' + fname + '-' + t + '.cpu', 'w+') as f:
                f.write(cpu)

            with open(vm.name + '-' + fname + '-' + t + '.disk', 'w+') as f:
                f.write(disk)

            with open(vm.name + '-' + fname + '-' + t + '.net', 'w+') as f:
                f.write(netw)

    parallel(lambda vm: vm.install('hadoop'), vms)
    parallel(lambda vm: vm.install('ntp'), vms)
    parallel(lambda vm: vm.install('argos'), vms)

    cluster = HadoopCluster(vms[0], vms[1:], env.param('terasort:use_local_disk'))
    cluster.setup()
    cluster.reset()

    collect_stats(vms, 'teragen')
    output = cluster.execute('"/usr/bin/time -f \'%e\' -o terasort.out hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar teragen -Dmapred.map.tasks={1} {2} {0}"'.format(TERASORT_INPUT, env.param('terasort:mappers'), env.param('terasort:rows')))
    teragen_time = cluster.master.script('sudo su - hduser -c "tail -n1 terasort.out"').strip()
    collect_stats(vms, 'teragen-end')

    parallel(lambda vm: vm.script('rm -rf ~/argos/proc'), vms)
    parallel(lambda vm: vm.script('cd argos; sudo nohup src/argos >argos.out 2>&1 &'), vms)
    time.sleep(2)

    collect_stats(vms, 'terasort')
    cluster.execute('"/usr/bin/time -f \'%e\' -o terasort.out hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar terasort -Dmapred.reduce.tasks={2} {0} {1} >output.log 2>&1"'.format(TERASORT_INPUT, TERASORT_OUTPUT, env.param('terasort:reducers')))
    collect_stats(vms, 'terasort-end')

    terasort_time = cluster.master.script('sudo su - hduser -c "tail -n1 terasort.out"').strip()
    terasort_out = cluster.master.script('sudo su - hduser -c "cat output.log"').strip()

    parallel(lambda vm: vm.script('sudo killall -SIGINT argos'), vms)
    time.sleep(30)
    parallel(lambda vm: vm.script('chmod -R 777 ~/argos/proc'), vms)
    parallel(lambda vm: vm.recv('~/argos/proc', vm.name + '-proc'), vms)
    parallel(lambda vm: vm.recv('~/argos/argos.out', vm.name + '-argos.out'), vms)

    file_name = str(time.time()) + '-' + cluster.master.type
    with open(file_name + ".time", 'w+') as f:
        f.write(str(teragen_time) + "," + str(terasort_time))

    with open(file_name + ".out", 'w+') as f:
        f.write(terasort_out)

def terasort_run_on_cluster(vms, env):
    pass

def terasort_no_argos_run(vms, env):
    parallel(lambda vm: vm.install('hadoop'), vms)
    parallel(lambda vm: vm.install('ntp'), vms)

    cluster = HadoopCluster(vms[0], vms[1:], env.param('terasort:use_local_disk'))
    cluster.setup()
    cluster.reset()

    output = cluster.execute('"/usr/bin/time -f \'%e\' -o terasort.out hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar teragen -Dmapred.map.tasks={1} {2} {0}"'.format(TERASORT_INPUT, env.param('terasort:mappers'), env.param('terasort:rows')))
    teragen_time = cluster.master.script('sudo su - hduser -c "tail -n1 terasort.out"').strip()

    time.sleep(2)
    cluster.execute('"/usr/bin/time -f \'%e\' -o terasort.out hadoop jar /usr/local/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-examples-2.7.1.jar terasort -Dmapred.reduce.tasks={2} {0} {1} >output.log 2>&1"'.format(TERASORT_INPUT, TERASORT_OUTPUT, env.param('terasort:reducers')))

    terasort_time = cluster.master.script('sudo su - hduser -c "tail -n1 terasort.out"').strip()
    terasort_out = cluster.master.script('sudo su - hduser -c "cat output.log"').strip()

    file_name = str(time.time()) + '-' + cluster.master.type
    with open(file_name + ".time", 'w+') as f:
        f.write(str(teragen_time) + "," + str(terasort_time))

    with open(file_name + ".out", 'w+') as f:
        f.write(terasort_out)

def hive_test(vms, env):
    parallel(lambda vm: vm.install('hadoop'), vms)
    parallel(lambda vm: vm.install('hive'), vms)
    parallel(lambda vm: vm.install('mahout'), vms)
    parallel(lambda vm: vm.install('bigbench'), vms)

    vms[0].install('bigbench')

    hadoop = HadoopCluster(vms[0], vms[1:], env.param('terasort:use_local_disk'))
    hadoop.setup()
    hadoop.reset()

    hive = HiveCluster(hadoop)
    hive.setup()

terasort_run = terasort_with_argos_run

def run(env):
    vms = env.virtual_machines().values()
    env.benchmark.executor(vms, terasort_run)
    env.benchmark.executor.run()
