#!/usr/bin/env python

from git import *
import sys
import getopt
from configobj import ConfigObj
from os.path import expanduser

config = ConfigObj('%s/.config/gitscripts.conf' % expanduser('~'))
if not config.get('all'):
    config = {'all': {}}

colors = {'+': '\033[32m', '-': '\033[31m', '@': '\033[36m'}
reset_color = '\033[0m'

integration_branches = config['all'].get('integration_branches', [])
onhold_branches = config['all'].get('onhold_branches', [])
# These are overridable on the commandline
repo_path = '.'
show_diff = config['all'].get('detail', False)
pause = config['all'].get('pause', False)
limit_branches = []

helpmsg = "%s [--repo=<repo_path>] [--branches='<branch1>[, <branch2>...]'] [--detail|-d] [-p|--pause] [-h|--help]" % sys.argv[0]

try:
    opts, args = getopt.getopt(sys.argv[1:], 'hdp', ["repo=","branches=","detail","pause"])
except getopt.GetoptError:
    print helpmsg
    sys.exit(2)
for opt, arg in opts:
    if opt in ['-h', '--help']:
        print helpmsg
    if opt == '--repo':
        repo_path = arg
    if opt == '--branches':
        limit_branches = [x.strip() for x in arg.split(',')]
    if opt in ['--detail', '-d']:
        show_diff = True
    if opt in ['--pause', '-p']:
        pause = True


repo = Repo(repo_path)

out_dict = {}
master_shas = set()
for master_commit in repo.iter_commits(rev=repo.branches.master):
    master_shas.add(master_commit.hexsha)

for branch in repo.branches:
     # Including onhold because they won't go into the release.
    if not limit_branches and branch.name in integration_branches + onhold_branches \
            or limit_branches and not branch.name in limit_branches:
        continue
    commits = repo.iter_commits(rev=branch)
    for commit in commits:
        if commit.hexsha in master_shas:
            continue
        commit_message = commit.summary
        commit_files = commit.stats.files.keys()
        for commit_file in commit_files:
            if '/security/' in commit_file and 'Merge' not in commit_message:
                out_dict.setdefault(branch.name, {})
                out_dict[branch.name].setdefault(commit_file, [])
                out_dict[branch.name][commit_file].append(commit.hexsha)

for branch in sorted(out_dict.keys()):
    print '[%s]' % branch
    for filename in sorted(out_dict[branch].keys()):
        if not show_diff:
            print '  * %s' % filename
        else:
            print
            last_commit = repo.commit(out_dict[branch][filename][0])
            first_commit_log = repo.iter_commits(rev=repo.commit(out_dict[branch][filename][-1]))
            first_commit_log.next()
            first_commit = first_commit_log.next()
            diffidx = first_commit.diff(last_commit, paths=[filename], create_patch=True)
            for diff in diffidx:
                if diff.renamed:
                    import pdb; pdb.set_trace()
                if diff.a_blob and filename == diff.a_blob.path \
                        or diff.b_blob and filename == diff.b_blob.path \
                        or diff.renamed and filename in [diff.rename_from, diff.rename_to]:
                    # This thing is weird; it's a 3-tuple representing the patch, but the boundaries are in strange places...
                    patch = ''.join(diff.diff.partition(filename))
                    for line in patch.split('\n'):
                        color = colors.get(line[0], reset_color) if line else reset_color
                        print color + '  ' + line
            if pause:
                cont = raw_input("Press Enter to continue...")
                print
                if cont == 'q':
                    sys.exit()
    print
