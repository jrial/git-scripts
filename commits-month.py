#!/usr/bin/env python

from git import *
import sys
import getopt
from configobj import ConfigObj
from datetime import datetime
from os.path import expanduser

config = ConfigObj('%s/.config/gitscripts.conf' % expanduser('~'))
if not config.get('all'):
    config = {'all': {}}

integration_branches = config['all'].get('integration_branches', [])
onhold_branches = config['all'].get('onhold_branches', [])

# These are overridable on the commandline
repo_path = '.'
since = datetime.now().strftime('%Y-%m-01')
author = config['all'].get('author', '')
no_pause = config['all'].get('pause', False) and not config['all'].as_bool('pause')

helpmsg = "%s [--repo=<repo_path>] [--since=<start_date>] [--author='<author>'] [--np|--no-pause] [-h|--help]" % sys.argv[0]

try:
    opts, args = getopt.getopt(sys.argv[1:], 'h', ["repo=","since=","author=","np"])
except getopt.GetoptError:
    print helpmsg
    sys.exit(2)
for opt, arg in opts:
    if opt in ['-h', '--help']:
        print helpmsg
    if opt == '--repo':
        repo_path = arg
    if opt == '--since':
        since = arg
    if opt == '--author':
        author = arg
    if opt in ['--np', '--no-pause']:
        no_pause = True


repo = Repo(repo_path)

out_dict = {}
for branch in repo.branches:
    if not branch.name in integration_branches:
        commits = repo.iter_commits(rev=branch, since=since, author=author)
        for commit in commits:
            commit_datetime = datetime.fromtimestamp(commit.committed_date)
            commit_date = commit_datetime.strftime('%Y-%m-%d')
            commit_time = commit_datetime.strftime('%H-%M-%S')
            commit_date_and_hash = '%s - %s' % (commit.committed_date, commit.hexsha)
            commit_message = commit.message.split('\n')[0]
            out_dict.setdefault(commit_date ,{})
            out_dict[commit_date].setdefault(commit_date_and_hash, {'message': '%s - %s' % (commit_time, commit_message), 'branches': []})
            out_dict[commit_date][commit_date_and_hash]['branches'].append(branch.name)

for date in sorted(out_dict.keys()):
    print '[%s]' % date
    for entry in sorted(out_dict[date].keys()):
        print '    [%s]' % ', '.join(out_dict[date][entry]['branches'])
        print '        %s' % out_dict[date][entry]['message']
    print ''
    if not no_pause:
        cont = raw_input("Press Enter to continue...")
        if cont == 'q':
            sys.exit()
