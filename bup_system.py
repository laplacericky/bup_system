#!/usr/bin/env python3
import argparse,sys
import subprocess,os
import datetime
from zoneinfo import ZoneInfo
import shutil
from pathlib import Path

date_format = '%Y-%m-%d-%H%M%S'
HK_timezone = ZoneInfo('Asia/Hong_Kong')
def path_cannot_exist(p):
    assert not p.exists(), f'{p} exists'


def get_version():
    version = datetime.datetime(960, 2, 4, tzinfo = HK_timezone)
    r = subprocess.run(['bup', 'ls'], check = True, stdout = subprocess.PIPE, text = True)
    targets = r.stdout.split()

    for t in targets:
        r = subprocess.run(['bup', 'ls', '-l', t], check = True, stdout = subprocess.PIPE, text = True)
        d = datetime.datetime.strptime(r.stdout.splitlines()[-1].split()[-1], date_format).replace(tzinfo=HK_timezone)
        version = max(d, version)
    return version

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices = ['backup','ls','restore','ds','init', 'bundle', 'unbundle', 'update', 'version'] )
    parser.add_argument('target', nargs='?')
    parser.add_argument('--version', default = 'latest')
    args = parser.parse_args()

    workdir = Path('workdir')
    assert workdir.is_dir()


    with open('./params/public/bup_targets.txt') as f:
        valid_targets = f.read().splitlines()

    base_dir = Path.cwd()
    proj_name = base_dir.name
    print(f'project name: {proj_name}')
    relative_bup_dir = Path(f'.{proj_name}_bup')
    bup_dir = base_dir / relative_bup_dir
    os.environ['BUP_DIR'] = str(bup_dir)


    if args.mode == 'init':
        path_cannot_exist(bup_dir)
        subprocess.run(['bup', 'init'], check = True)
    elif args.mode == 'unbundle':
        path_cannot_exist(bup_dir)
        assert args.target is not None
        target_path = Path(args.target)
        prefix, suffix = target_path.stem, target_path.suffix
        assert '_'.join(prefix.split('_')[:-1]) == proj_name
        assert suffix == '.tar'
        subprocess.run(['tar', 'xf', target_path, f'--one-top-level={relative_bup_dir}', '--strip-components=1'], check = True)
        print('unbundle success')

    else:
        assert bup_dir.is_dir(), 'bup dir does not exist, run init to initialize or unbundle to import one'
        if args.mode == 'ds':
            subprocess.run(['du', '-sh', bup_dir], check = True)
        elif args.mode == 'version':
            ver = get_version()
            print(f'version date: {ver.strftime(date_format)}')
        elif args.mode == 'bundle':
            ver = get_version()
            bundle_name = Path(f'{proj_name}_{ver.strftime(date_format)}.tar')
            bundle_path = workdir / bundle_name
            path_cannot_exist(bundle_path)
            subprocess.run(['tar', 'cf', bundle_path, relative_bup_dir], check = True)
            print(f'bundled to {bundle_path}')
        elif args.mode == 'update':
            assert args.target is not None
            target_path = Path(args.target)
            prefix, suffix = target_path.stem, target_path.suffix
            assert '_'.join(prefix.split('_')[:-1]) == proj_name
            assert suffix == '.tar'
            ver = get_version()
            bundle_ver = datetime.datetime.strptime(prefix.split('_')[-1], date_format).replace(tzinfo=HK_timezone)
            print(f'local version date: {ver.strftime(date_format)}')
            print(f'bundle version date: {bundle_ver.strftime(date_format)}')
            assert bundle_ver > ver, 'not a newer version'
            shutil.rmtree(bup_dir)
            subprocess.run(['tar', 'xf', target_path, f'--one-top-level={relative_bup_dir}', '--strip-components=1'], check = True)
            print('update success')

        else:
            assert args.target in valid_targets
            target_path = Path(args.target)
            folder_name = args.target

            if args.mode == 'backup':
                folder_real_path = target_path.resolve(strict = True)
                folder_real_dir = folder_real_path.parent
                subprocess.run(['bup', 'index', f'{folder_real_path}'], check = True)
                subprocess.run(['bup', 'save', '-9', '-n', f'local-{folder_name}',
                                f'--strip-path={folder_real_dir}', f'{folder_real_path}'], check = True)

            elif args.mode == 'ls':
                subprocess.run(['bup', 'ls', '-l', f'local-{folder_name}'], check = True)

            elif args.mode == 'restore':
                path_cannot_exist(workdir / folder_name)
                subprocess.run(['bup', 'restore', '-C', workdir, f'local-{folder_name}/{args.version}/{folder_name}'], check = True)



if __name__ == '__main__':
    assert sys.version_info[0] >= 3 and sys.version_info[1] >= 11
    main()
