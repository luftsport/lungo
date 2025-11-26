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
from ext.app.eve_blueprint_helper import SwaggerBlueprint # parse_request, format_response,
import psutil
import Pyro4
from ext.auth.decorators import require_token
from ext.app.eve_helper import eve_response

Syncdaemon = SwaggerBlueprint('Manage syncdaemon process', __name__, url_prefix='syncdaemon')

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
        return eve_response({'status': False}, 200)

@Syncdaemon.route('/api-doc', methods=['GET'])
@require_token()
def get_paths():
    resp = [str(p) for p in app.url_map.iter_rules() if str(p).startswith('/api/v1/syncdaemon')]
    return eve_response(resp)

@Syncdaemon.route("/process/info", methods=['GET'])
@require_token()
def process_info():
    p = get_process()

    # 'environ'  'memory_info', 'memory_maps','open_files','terminal',
    d = p.as_dict(attrs=['cmdline', 'connections', 'cpu_affinity', 'cpu_num', 'cpu_percent',
                         'cpu_times', 'create_time', 'cwd', 'exe', 'gids', 'io_counters', 'ionice',
                         'memory_full_info', 'memory_percent', 'name', 'nice',
                         'num_ctx_switches', 'num_threads', 'pid', 'ppid',
                         'status', 'threads', 'uids', 'username'])

    # Jsonify the dictionary and return it
    return eve_response(d, 200)


@Syncdaemon.route("/process/kill/<int:pid>", methods=['POST'])
@require_token()
def process_kill(pid):
    p = get_process()

    if p.pid == int(pid) and p.is_running() and p.status() == 'sleeping':
        p.kill()
        return eve_response({'status': True}, 200)

    return eve_response({'status': False}, 200)


"""
Daemon
"""


@Syncdaemon.route("/shutdown", methods=['POST'])
@require_token()
def shutdown():
    try:
        Pyro4.Proxy(RPC_SERVICE).shutdown()
        return eve_response({'status': True}, 200)
    except:
        return eve_response({'status': False}, 200)


@Syncdaemon.route("/status", methods=['GET'])
@require_token()
def status():
    try:
        Pyro4.Proxy(RPC_SERVICE).status()
        return eve_response({'status': True}, 200)
    except:
        return eve_response({'status': False}, 200)


"""
workers
"""


@Syncdaemon.route("/workers/status", methods=['GET'])
@require_token()
def workers_status():
    """Returns dict of all workers"""
    try:
        s = Pyro4.Proxy(RPC_SERVICE).get_workers_status()
        return eve_response(data=s, status=200)
    except Exception as e:
        return eve_response(data={'_error': {'message': str(e)}}, status=200)


@Syncdaemon.route("/workers/failed/clubs", methods=['GET'])
@require_token()
def workers_failed_clubs():
    try:
        s = Pyro4.Proxy(RPC_SERVICE).get_failed_clubs()
    except:
        s = []

    return eve_response(s, 200)


@Syncdaemon.route("/workers/logs", methods=['GET'])
@require_token()
def workers_logs():
    try:
        s = Pyro4.Proxy(RPC_SERVICE).get_logs()
    except:
        s = []

    return eve_response(s, 200)


@Syncdaemon.route("/workers/reboot", methods=['POST'])
@require_token()
def workers_reboot():
    try:
        Pyro4.Proxy(RPC_SERVICE).reboot_workers()
        return eve_response({'status': True}, 200)
    except:
        return eve_response({'status': False}, 200)


@Syncdaemon.route("/workers/shutdown", methods=['POST'])
@require_token()
def workers_shutdown():
    try:
        Pyro4.Proxy(RPC_SERVICE).shutdown_workers()
        return eve_response({'status': True}, 200)
    except:
        return eve_response({'status': False}, 200)


@Syncdaemon.route("/workers/start", methods=['POST'])
@require_token()
def workers_start():
    try:
        s = Pyro4.Proxy(RPC_SERVICE).start_workers()
        return eve_response({'status': True}, 200)
    except:
        return eve_response({'status': False}, 200)


"""
/worker/<action>/index
restart_worker
get_worker_status
get_worker_log

"""


@Syncdaemon.route("/worker/status/<int:index>", methods=['GET'])
@require_token()
def worker_status(index):
    try:
        s = Pyro4.Proxy(RPC_SERVICE).get_worker_status(index)
        return eve_response(s, 200)
    except:
        return eve_response({}, 200)


@Syncdaemon.route("/worker/log/<int:index>", methods=['GET'])
@require_token()
def worker_log(index):
    try:
        s = Pyro4.Proxy(RPC_SERVICE).get_worker_log(index)
        return eve_response(s, 200)
    except:
        return eve_response({}, 200)


@Syncdaemon.route("/worker/reboot/<int:index>", methods=['POST'])
@require_token()
def worker_restart(index):
    try:
        s = Pyro4.Proxy(RPC_SERVICE).restart_worker(index)
        return eve_response({'status': s}, 200)
    except:
        return eve_response({'status': False}, 200)
