from trac.core import *
from trac.config import Option, BoolOption
from trac.util import shorten_line
from trac.versioncontrol import RepositoryManager
from trac.versioncontrol.web_ui.browser import BrowserModule
from trac.versioncontrol.web_ui.changeset import ChangesetModule
from trac.web.api import IRequestHandler, RequestDone
from trac.wiki import IWikiSyntaxProvider
try:
    from tracopt.versioncontrol.git.git_fs import GitConnector
except ImportError:
    from tracext.git.git_fs import GitConnector
from genshi.builder import tag
import simplejson
import re

class GithubPlugin(Component):
    implements(IRequestHandler)

    secret = Option('github', 'secret', '',
        """The shared secret passed by GitHub when a post-commit hook is dispatched.""")

    #################
    # IRequestHandler

    def match_request(self, request):
        should_handle = request.path_info.rstrip('/') == ('/github/%s' % self.secret) and request.method == 'POST'

        if should_handle:
            # This is hacky but it's the only way davglass found to let Trac post to this request without a valid
            # form_token
            request.form_token = None

        return should_handle

    def process_request(self, request):
        payload = request.args.get('payload')

        if not payload:
            raise Exception('Payload not found')

        payload = simplejson.loads(payload)

        repository_name = payload['repository']['name']
        repository = self.env.get_repository(repository_name)

        if not repository:
            raise Exception('Repository "%s" not found' % repository_name)

        # CachedRepository
        if repository.repos:
            repository.repos.git.repo.remote('update')
        # Normal repository
        else:
            repository.git.repo.remote('update')

        manager = RepositoryManager(self.env)

        revision_ids = [ commit['id'] for commit in payload['commits'] ]

        try:
            self.env.log.debug('Adding changesets: %s' % revision_ids)
            manager.notify('changeset_added', repository_name, revision_ids)
        except Exception as exception:
            self.env.log.error(exception)

        request.send_response(204)
        request.send_header('Content-Length', 0)
        request.write('')
        raise RequestDone

def _valid_github_request(request):
    return request.get_header('X-Requested-With') != 'XMLHttpRequest' and not request.args.get('format')

# Redirect requests to changesets for repositories that use GitHub
def _process_changeset_view(self, request):
    request.perm.require('CHANGESET_VIEW')

    new = request.args.get('new')
    new_path = request.args.get('new_path')
    old = request.args.get('old')
    repository_name = request.args.get('reponame')

    # -- support for the revision log ''View changes'' form,
    #    where we need to give the path and revision at the same time
    if old and '@' in old:
        old, old_path = old.split('@', 1)
    if new and '@' in new:
        new, new_path = new.split('@', 1)

    manager = RepositoryManager(self.env)

    if repository_name:
        repository = manager.get_repository(repository_name)
    else:
        repository_name, repository, new_path = manager.get_repository_by_path(new_path)

    repository_url = repository.params.get('url', '')

    if _valid_github_request(request) and re.match(r'^https?://(?:www\.)?github\.com/', repository_url):
        url = repository_url.rstrip('/') + '/'

        if old:
            url += 'compare/' + old + '...' + new
        else:
            url += 'commit/' + new

        request.redirect(url)
    else:
        return _old_process_changeset_view(self, request)

_old_process_changeset_view = ChangesetModule.process_request;
ChangesetModule.process_request = _process_changeset_view;

# Redirect requests to the browser for repositories that use GitHub
def _process_browser_view(self, request):
    request.perm.require('BROWSER_VIEW')

    preselected = request.args.get('preselected')
    if preselected and (preselected + '/').startswith(request.href.browser() + '/'):
        request.redirect(preselected)

    elif request.path_info.startswith('/browser') and _valid_github_request(request):
        path = request.args.get('path', '/')
        rev = request.args.get('rev', '')
        if rev.lower() in ('', 'head'):
            rev = 'master'

        manager = RepositoryManager(self.env)
        repository_name, repository, path = manager.get_repository_by_path(path)
        repository_url = repository.params.get('url', '')

        if re.match(r'^https?://(?:www\.)?github\.com/', repository_url):
            url = repository_url.rstrip('/') + '/blob/' + rev + '/' + path
            request.redirect(url)
        else:
            return _old_process_browser_view(self, request)

    else:
        return _old_process_browser_view(self, request)

_old_process_browser_view = BrowserModule.process_request;
BrowserModule.process_request = _process_browser_view;

# Fix the _format_sha_link method in the Git module to correctly search for the SHA in all repositories,
# not just the default repository
def _format_sha_link(self, formatter, original_sha, label):
    for repository in RepositoryManager(self.env).get_real_repositories():
        try:
            sha = repository.normalize_rev(original_sha) # in case it was abbreviated
            changeset = repository.get_changeset(sha)
            return tag.a(label, class_='changeset',
                         title=shorten_line(changeset.message),
                         href=formatter.href.changeset(sha, repository.reponame))
        except Exception, e:
            pass

    return tag.a(label, title='Changeset not found in any repository', class_='missing changeset', rel='nofollow')

GitConnector._format_sha_link = _format_sha_link;