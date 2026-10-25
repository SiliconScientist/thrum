"""Run with python3 -m thrum from the project directory."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
from .storage import Store, default_path, private_path
from .portability import backup, import_data, write_export


def unique_object(pairs):
    data={}
    for key,value in pairs:
        if key in data: raise ValueError('Duplicate JSON keys are not allowed.')
        data[key]=value
    return data


def main(argv=None):
    parser=argparse.ArgumentParser(description='Thrum — private, local relationship management.')
    parser.add_argument('--db',type=Path,default=default_path(),help='Database outside any Git checkout (default: ~/.local/share/thrum/people.sqlite)')
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('init',help='Initialize a private database or apply numbered migrations')
    commands.add_parser('demo',help='Load fictional examples into an empty database')
    serve=commands.add_parser('serve',help='Open the local browser dashboard')
    serve.add_argument('--port',type=int,default=8765)
    commands.add_parser('check',help='Check database and foreign-key integrity')
    for command in ('export','import','backup'):
        p=commands.add_parser(command);p.add_argument('file',type=Path)
    args=parser.parse_args(argv)
    if args.command=='serve' and not 1<=args.port<=65535: parser.error('Port must be between 1 and 65535.')
    try:
        if args.command in ('serve','export','backup','check') and not args.db.expanduser().exists():
            raise ValueError('Database not found. Run init first.')
        payload=None
        if args.command=='import':
            source=private_path(args.file)
            with source.open('rb') as stream:
                raw=stream.read(16*1024*1024+1)
            if len(raw)>16*1024*1024: raise ValueError('Import exceeds the 16 MiB limit.')
            payload=json.loads(raw.decode('utf-8'),object_pairs_hook=unique_object)
        if args.command=='serve':
            from .web import create_server
            server=create_server(args.db,args.port)
            print(f'Thrum is running at http://127.0.0.1:{server.server_port}/ — Ctrl-C to stop.',flush=True)
            try: server.serve_forever()
            except KeyboardInterrupt: pass
            finally: server.server_close()
            return 0
        with closing(Store(args.db)) as store:
            if args.command=='demo':
                from .demo import seed
                seed(store)
            elif args.command=='export': write_export(store,args.file)
            elif args.command=='import': import_data(store,payload)
            elif args.command=='backup': backup(store,args.file)
            elif args.command=='check':
                if store.con.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or store.con.execute('PRAGMA foreign_key_check').fetchall():
                    raise ValueError('Database integrity check failed.')
        print({'init':'Database ready.','demo':'Fictional examples loaded.','export':'Export saved.','import':'Import complete.','backup':'Backup saved.','check':'Database integrity OK.'}[args.command])
        return 0
    except FileExistsError:
        print('Destination already exists. Choose a new filename.',file=sys.stderr)
    except json.JSONDecodeError:
        print('Invalid JSON import.',file=sys.stderr)
    except (OSError,sqlite3.Error,UnicodeError,RecursionError):
        print('Operation failed. Check file availability, private permissions, and database integrity.',file=sys.stderr)
    except ValueError as error:
        # Application validation messages never interpolate contact values or paths.
        print(str(error),file=sys.stderr)
    return 1


if __name__=='__main__':
    sys.exit(main())
