#!/usr/bin/env python3
import argparse,sys
import subprocess,os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices = ['backup','ls','restore','ds','init'] )
    parser.add_argument('target', nargs='?')
    parser.add_argument('--version', default = 'latest')
    args = parser.parse_args()

    with open('./params/bup_targets.txt') as f:
        valid_targets = f.read().splitlines()

    base_dir = os.getcwd()
    proj_name = os.path.basename(base_dir)
    print(f'project name: {proj_name}')
    os.environ['BUP_DIR'] = f'{base_dir}/.bup'

    if args.mode == 'init':
        assert not os.path.exists(f'{base_dir}/.bup')
        subprocess.run(['bup', 'init'], check = True)
    else:
        assert os.path.isdir(f'{base_dir}/.bup')
        if args.mode == 'ds':
            subprocess.run(['du', '-sh', f'{base_dir}/.bup'], check = True)
        else:
            assert args.target in valid_targets
            folder_real_path = os.path.realpath(args.target)
            folder_real_dir = os.path.dirname(folder_real_path)
            folder_name = args.target
            if args.mode == 'backup':
                subprocess.run(['bup', 'index', f'{folder_real_path}'], check = True)
                subprocess.run(['bup', 'save', '-9', '-n', f'local-{folder_name}',
                                f'--strip-path={folder_real_dir}', f'{folder_real_path}'], check = True)

            elif args.mode == 'ls':
                subprocess.run(['bup', 'ls', '-l', f'local-{folder_name}'], check = True)

            elif args.mode == 'restore':
                assert os.path.isdir('workdir')
                subprocess.run(['bup', 'restore', '-C', './workdir', f'local-{folder_name}/{args.version}/{folder_name}'], check = True)



if __name__ == '__main__':
    assert sys.version_info[0] >= 3 and sys.version_info[1] >= 11
    main()
