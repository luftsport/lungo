import daemon
import daemon.pidfile
import sys
import datetime
import lockfile
import argparse
import random
import logging
import logging.handlers
import time
import sched

# Init Logger
#logger = logging.getLogger('myLogger')
#logger.setLevel(logging.INFO)
# add handler to the logger
#handler = logging.handlers.SysLogHandler('/dev/log')
# add formatter to the handler
#formatter = logging.Formatter('Python: { "loggerName":"%(name)s", "timestamp":"%(asctime)s", "pathName":"%(pathname)s", "logRecordCreationTime":"%(created)f", "functionName":"%(funcName)s", "levelNo":"%(levelno)s", "lineNo":"%(lineno)d", "time":"%(msecs)d", "levelName":"%(levelname)s", "message":"%(message)s"}')
#handler.formatter = formatter
#logger.addHandler(handler)

"""logging.basicConfig(filename='/tmp/ka.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
"""


PID_PATH = '/var/run/ka.pid'

s = sched.scheduler(time.time, time.sleep)

def ka_daemon(args):

    print('Daemon getting here')

    chroot_directory = None
    working_directory = "/"
    umask = 0
    uid = None
    gid = None
    initgroups = False
    prevent_core = True
    detach_process = None
    files_preserve = None
    pidfile = lockfile.LockFile('/tmp/ka.pid')
    stdin = None
    stdout = None
    stderr = None
    signal_map = None

    ctx = daemon.DaemonContext(pidfile=pidfile)
    # ctx.open()

    if args.command == "status":
        sys, exit(1 if ctx.is_open else 0)

    elif args.command == "stop":
        ctx.close()

    elif args.command == "start":
        with ctx:
            s.enter(10, 1, do_shit)
            s.run()
    else:
        raise Exception("Unexpected daemon command {!r}".format(args.command))


def open_io_redirect_file(fname):
    fobj = open(fname, "w")
    fobj.write("\n\n\n===== {} =====\n\n\n".format(
        datetime.datetime.now().isoformat()
    ))
    return fobj


def do_shit():
    # create logger with 'spam_application'
    logger = logging.getLogger('ka_app')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('/tmp/ka.log')
    fh.setLevel(logging.DEBUG)


    formatter = logging.Formatter(
        'Python: { "loggerName":"%(name)s", "timestamp":"%(asctime)s", "pathName":"%(pathname)s", "logRecordCreationTime":"%(created)f", "functionName":"%(funcName)s", "levelNo":"%(levelno)s", "lineNo":"%(lineno)d", "time":"%(msecs)d", "levelName":"%(levelname)s", "message":"%(message)s"}')
    fh.formatter = formatter
    logger.addHandler(fh)

    logger.warning("Running Urban Planning %i" % random.randrange(1, 99))
    i = 60

    print('do shaitolainen')

    while i > 0:
        logger.warning("Running Urban Planning %i" % random.randrange(1,99))
        s = random.randrange(1, 5)
        time.sleep(s)
        i -= s


def run_daemon(args):
    ctx = daemon.DaemonContext(
        working_directory=args.working_directory,
        pidfile=lockfile.LockFile(args.pidfile),  # daemon.pidfile.PIDLockFile(PID_PATH)
        stdout=open_io_redirect_file(args.stdout),
        stderr=open_io_redirect_file(args.stderr),
    )
    if args.command == "status":
        sys, exit(1 if ctx.is_open else 0)
    elif args.command == "stop":
        ctx.close()
    elif args.command == "start":
        with ctx:
            do_shit()
    else:
        raise Exception("Unexpected daemon command {!r}".format(args.command))


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='The NIF->NLF KA Daemon\n')

    subparsers = parser.add_subparsers(help='Use {subcommand} -h for each subcommand\'s optional arguments details',
                                       dest='command')

    subparsers.add_parser('status', help='Show status of KA daemon process')
    subparsers.add_parser('stop', help='Stop the KA daemon process')
    subparsers.add_parser('start', help='Start the KA daemon process')

    args = parser.parse_args()

    # print(args)

    ka_daemon(args)


if __name__ == "__main__":
    main()
