github-trac
===========

I have unofficially taken this project over. Forks of this project should happen here, not upstream. (Déjà vu!)

This Trac plugin is designed to accept a [GitHub Post-Receive hook](https://help.github.com/articles/post-receive-hooks).
It is designed to work with Trac 1.0 and later using the built-in Git and multi-repository support.

Installation
------------

1. `easy_install https://github.com/csnover/github-trac/archive/master.zip`
2. Enable the plugin in the admin interface (you may need to restart Trac and/or your Web server for it to appear)
3. Go to your GitHub repository’s Settings → Service Hooks page and choose “Trac”
4. Set URL to the URL to your Trac installation
5. Set Token to a randomly generated secret (just make one up!)
6. Add the following configuration to your trac.ini:

   ```ini
   [github]
   secret = <the random shared secret entered as the “Token” in your GitHub settings>

   # optional, defaults to "closed"
   closed_status = closed

   # optional, but recommended; ensures your Trac repos are in sync immediately
   # after a GH commit
   resync = True
   ```
7. Create local mirror clones of your GitHub repositories on the machine running Trac, in directories that are
   writable by the user that Trac runs as.
8. Add your Git repositories to Trac, following the recommendations below if you want your code browser/changeset
   viewer to redirect to GitHub as well.

**Important notes:**

1. When you clone your GitHub repositories for Trac, make sure that you use `git clone --mirror`. If you use
   `git clone --bare`, your Trac repository will *not* resync properly after a changeset.
2. The name given to your repository in Trac *must* match the name of the repository on GitHub if you want to
   perform auto-resync.

Code browser and changeset viewer
---------------------------------

The code browser portion of the plugin is designed to replace the code browser built into Trac with a
redirect to the GitHub source browser, if desired.

In order for this to work, when you add your Git repositories to Trac, *you must set the URL for the repository to its
URL at GitHub*. Once this is set, browsing to paths or viewing changesets will redirect to the appropriate GitHub page.

Commit message format
---------------------

The commit hook is designed to close or mark tickets that are attached to a commit message.

It searches commit messages for text in the form of:

```
command #1
command #1, #2
command #1 & #2
command #1 and #2
```

Instead of the short-hand syntax "#1", "ticket:1" can be used as well, which is handy for avoiding GitHub linking
to its own issue tracker:

```
command ticket:1
command ticket:1, ticket:2
command ticket:1 & ticket:2
command ticket:1 and ticket:2
```

You can combine multiple commands in one commit message as well. For example:

```
Fixes #1, #2. Refs #3.
```

[List of available commands](https://github.com/csnover/github-trac/blob/master/github/hook.py#L76-L87)