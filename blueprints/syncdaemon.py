"""

with open('daemon.pid','r') as f:
    pid = int(f.read().strip())

process = psutil.Process(pid)

print(process.memory_info().rss/(1000*1024))
process.threads()
process.num_threads()
process.status()
process.io_counters()
process.is_running()

connections(kind='inet')

kill()
send_signal(signal)
suspend() SIGSTOP
resume() SIGCONT
terminate() SIGTERM
wait(timeout=None) wait for process termination

Pyro4.Proxy('PYRO:nif.integration@localhost:5555').shutdown()


"""

from flask import Blueprint, current_app as app, request, Response, abort, jsonify
import psutil
import Pyro4

Sync = Blueprint('Manage syncdaemon process', __name__)


def get_process():
    with open('/home/einar/Development/nif-integration/daemon.pid', 'r') as f:
        pid = int(f.read().strip())

    try:
        process = psutil.Process(pid)
        return process
    except:
        return False


@Sync.route("/process/info", methods=['GET'])
def process_info():
    p = get_process()

    # 'environ'  'memory_info', 'memory_maps','open_files','terminal',
    d = p.as_dict(attrs=['cmdline', 'connections', 'cpu_affinity', 'cpu_num', 'cpu_percent',
                         'cpu_times', 'create_time', 'cwd', 'exe', 'gids', 'io_counters', 'ionice',
                         'memory_full_info', 'memory_percent', 'name', 'nice',
                         'num_ctx_switches', 'num_threads',  'pid', 'ppid',
                         'status',  'threads', 'uids', 'username'])
    """
    mem = p.memory_info()
    # Build a dictionary
    d = {'memory': {'rss': mem.rss, 'vms': mem.vms, 'shared': mem.shared,
                    'text': mem.text, 'lib': mem.lib, 'data': mem.data, 'dirty': mem.dirty},
         'is_running': p.is_running(),
         'pid': p.pid,
         'status': p.status(),
         'num_threads': p.num_threads(),
         'threads': p.threads()
         }
    """
    # Jsonify the dictionary and return it
    return jsonify(**d)


@Sync.route("/process/kill/<int:pid>", methods=['POST'])
def process_kill(pid):
    p = get_process()

    if p.pid == int(pid) and p.is_running() and p.status() == 'sleeping':
        p.kill()
        return jsonify(**{'status': True})

    return jsonify(**{'status': False})


"""
Daemon
"""


@Sync.route("/shutdown", methods=['POST'])
def shutdown():
    s = Pyro4.Proxy('PYRO:nif.integration@localhost:5555').shutdown()


"""
workers
"""


@Sync.route("/workers/status", methods=['GET'])
def workers_status():
    """Returns dict of all workers"""
    s = Pyro4.Proxy('PYRO:nif.integration@localhost:5555').get_workers_status()

    return jsonify(**{'workers': s})


@Sync.route("/workers/failed/clubs", methods=['GET'])
def workers_failed_clubs():
    s = Pyro4.Proxy('PYRO:nif.integration@localhost:5555').get_failed_clubs()

    return jsonify(**{'clubs': s})


@Sync.route("/workers/logs", methods=['GET'])
def workers_logs():
    s = Pyro4.Proxy('PYRO:nif.integration@localhost:5555').get_logs()

    return jsonify(**s)


@Sync.route("/workers/reboot", methods=['POST'])
def workers_reboot():
    s = Pyro4.Proxy('PYRO:nif.integration@localhost:5555').reboot_workers()


@Sync.route("/workers/shutdown", methods=['POST'])
def workers_shutdown():
    s = Pyro4.Proxy('PYRO:nif.integration@localhost:5555').shutdown_workers()


@Sync.route("/workers/start", methods=['POST'])
def workers_start():
    s = Pyro4.Proxy('PYRO:nif.integration@localhost:5555').start_workers()


"""
/worker/<action>/index
restart_worker
get_worker_status
get_worker_log

"""


@Sync.route("/worker/status/<int:index>", defaults={'index': 0}, methods=['GET'])
def worker_status(index):
    s = Pyro4.Proxy('PYRO:nif.integration@localhost:5555').get_worker_status(index)
    return jsonify(**s)


@Sync.route("/worker/log/<int:index>", defaults={'index': 0}, methods=['GET'])
def worker_log(index):
    s = Pyro4.Proxy('PYRO:nif.integration@localhost:5555').get_worker_log(index)
    return jsonify(**s)


@Sync.route("/worker/restart/<int:index>", defaults={'index': 0}, methods=['POST'])
def worker_restart(index):
    s = Pyro4.Proxy('PYRO:nif.integration@localhost:5555').restart_worker(index)
    return jsonify(**s)
