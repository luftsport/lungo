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

Pyro4.Proxy(RPC_SERVICE).shutdown()

Pyro4.errors.CommunicationError

"""

from flask import Blueprint, current_app as app, request, Response, abort, jsonify
import psutil
import Pyro4
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response

Sync = Blueprint('Manage syncdaemon process', __name__)

RPC_SERVICE_NAME = 'integration.service'
RPC_SERVICE_PORT = 5555
RPC_SERVICE_HOST = 'localhost'
RPC_SERVICE = 'PYRO:{0}@{1}:{2}'.format(RPC_SERVICE_NAME, RPC_SERVICE_HOST, RPC_SERVICE_PORT)

def get_process():
    with open('/home/einar/nif-integration/syncdaemon.pid', 'r') as f:
        pid = int(f.read().strip())

    try:
        process = psutil.Process(pid)
        return process
    except:
        return False


@Sync.route("/process/info", methods=['GET'])
@require_token()
def process_info():
    p = get_process()

    # 'environ'  'memory_info', 'memory_maps','open_files','terminal',
    d = p.as_dict(attrs=['cmdline', 'connections', 'cpu_affinity', 'cpu_num', 'cpu_percent',
                         'cpu_times', 'create_time', 'cwd', 'exe', 'gids', 'io_counters', 'ionice',
                         'memory_full_info', 'memory_percent', 'name', 'nice',
                         'num_ctx_switches', 'num_threads',  'pid', 'ppid',
                         'status',  'threads', 'uids', 'username'])

    # Jsonify the dictionary and return it
    return jsonify(**d)


@Sync.route("/process/kill/<int:pid>", methods=['POST'])
@require_token()
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
@require_token()
def shutdown():
    s = Pyro4.Proxy(RPC_SERVICE).shutdown()


"""
workers
"""


@Sync.route("/workers/status", methods=['GET'])
@require_token()
def workers_status():
    """Returns dict of all workers"""
    try:
        s = Pyro4.Proxy(RPC_SERVICE).get_workers_status()

        return eve_response(data=s, status=200)
    except Exception as e:
        return eve_response(data={'_error': {'message': '%s' % e}})
        # return jsonify(**{'_items': s})


@Sync.route("/workers/failed/clubs", methods=['GET'])
@require_token()
def workers_failed_clubs():
    s = Pyro4.Proxy(RPC_SERVICE).get_failed_clubs()

    return jsonify(**{'_items': s})


@Sync.route("/workers/logs", methods=['GET'])
@require_token()
def workers_logs():
    s = Pyro4.Proxy(RPC_SERVICE).get_logs()

    return jsonify(**{'_items': s})


@Sync.route("/workers/reboot", methods=['POST'])
@require_token()
def workers_reboot():
    s = Pyro4.Proxy(RPC_SERVICE).reboot_workers()


@Sync.route("/workers/shutdown", methods=['POST'])
@require_token()
def workers_shutdown():
    s = Pyro4.Proxy(RPC_SERVICE).shutdown_workers()


@Sync.route("/workers/start", methods=['POST'])
@require_token()
def workers_start():
    s = Pyro4.Proxy(RPC_SERVICE).start_workers()


"""
/worker/<action>/index
restart_worker
get_worker_status
get_worker_log

"""


@Sync.route("/worker/status/<int:index>", defaults={'index': 0}, methods=['GET'])
@require_token()
def worker_status(index):
    s = Pyro4.Proxy(RPC_SERVICE).get_worker_status(index)
    return jsonify(**{'_items': s})


@Sync.route("/worker/log/<int:index>", defaults={'index': 0}, methods=['GET'])
@require_token()
def worker_log(index):
    s = Pyro4.Proxy(RPC_SERVICE).get_worker_log(index)
    return jsonify(**{'_items': s})


@Sync.route("/worker/restart/<int:index>", defaults={'index': 0}, methods=['POST'])
@require_token()
def worker_restart(index):
    s = Pyro4.Proxy(RPC_SERVICE).restart_worker(index)
    return jsonify(**{'_items': s})
