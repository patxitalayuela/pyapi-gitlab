# -*- coding: utf-8 -*-
"""
pyapi-gitlab, a gitlab python wrapper for the gitlab API
by Itxaka Serrano Garcia <itxakaserrano@gmail.com>
"""

import requests
import json
from . import exceptions


class Gitlab(object):
    """
    Gitlab class
    """
    def __init__(self, host, token="", verify_ssl=True):
        """
        on init we setup the token used for all the api calls and all the urls
        :param host: host of gitlab
        :param token: token
        """
        if token != "":
            self.token = token
            self.headers = {"PRIVATE-TOKEN": self.token}
        if not host:
            raise ValueError("host argument may not be empty")
        if host[-1] == '/':
            self.host = host[:-1]
        else:
            self.host = host
        if self.host[:7] == 'http://' or self.host[:8] == 'https://':
            pass
        else:
            self.host = 'https://' + self.host

        self.api_url = self.host + "/api/v3"
        self.projects_url = self.api_url + "/projects"
        self.users_url = self.api_url + "/users"
        self.keys_url = self.api_url + "/user/keys"
        self.groups_url = self.api_url + "/groups"
        self.search_url = self.api_url + "/projects/search"
        self.hook_url = self.api_url + "/hooks"
        self.verify_ssl = verify_ssl

    def login(self, email=None, password=None, user=None):
        """
        Logs the user in and setups the header with the private token
        :param user: gitlab user
        :param password: gitlab password
        :return: True if login successfull
        """
        if user != None:
            data = {"login": user, "password": password}
        elif email != None:
            data = {"email": email, "password": password}
        else:
            raise ValueError('Neither username nor email provided to login')

        request = requests.post("{}/api/v3/session".format(self.host), data=data,
                                verify=self.verify_ssl,
                                headers={"connection": "close"})
        if request.status_code == 201:
            self.token = json.loads(request.content.decode("utf-8"))['private_token']
            self.headers = {"PRIVATE-TOKEN": self.token,
                            "connection": "close"}
            return True
        else:
            msg = json.loads(request.content.decode("utf-8"))['message']
            raise exceptions.HttpError(msg)

    def setsudo(self, user=None):
        """
        Set the subsequent API calls to the user provided
        :param user: User id or username to change to, None to return to the logged user
        :return: Nothing
        """
        if user is None:
            try:
                self.headers.pop("SUDO")
            except KeyError:
                pass
        else:
            self.headers["SUDO"] = user

    def getusers(self, search=None, page=1, per_page=20):
        """
        Return a user list
        :param search: Optional search query
        :param page: Which page to return (default is 1)
        :param per_page: Number of items to return per page (default is 20)
        return: returs a dictionary of the users, false if there is an error
        """
        data = {'page': page, 'per_page': per_page}
        if search:
            data['search'] = search
        request = requests.get(self.users_url, params=data,
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getuser(self, user_id):
        """
        Get info for a user identified by id
        :param user_id: id of the user
        :return: False if not found, a dictionary if found
        """
        request = requests.get("{}/{}".format(self.users_url, user_id),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def createuser(self, name, username, password, email, **kwargs):
        """
        Create a user
        :param name: Obligatory
        :param username: Obligatory
        :param password: Obligatory
        :param email: Obligatory
        :param kwargs: Any param the the Gitlab API supports
        :return: True if the user was created,false if it wasn't(already exists)
        """
        data = {"name": name, "username": username, "password": password, "email": email}

        if kwargs:
            data.update(kwargs)

        request = requests.post(self.users_url, headers=self.headers, data=data,
                                verify=self.verify_ssl)
        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        elif request.status_code == 404:
            return False

    def deleteuser(self, user_id):
        """
        Deletes an user by ID
        :param user_id: id of the user to delete
        :return: True if it deleted, False if it couldn't. False could happen
        for several reasons, but there isn't a
        good way of differenting them
        """
        request = requests.delete("{}/{}".format(self.users_url, user_id),
                                  headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:

            return False

    def currentuser(self):
        """
        Returns the current user parameters. The current user is linked
        to the secret token
        :return: a list with the current user properties
        """
        request = requests.get("{}/api/v3/user".format(self.host),
                               headers=self.headers, verify=self.verify_ssl)
        return json.loads(request.content.decode("utf-8"))

    def edituser(self, user_id, **kwargs):
        """
        Edits an user data. Unfortunately we have to check ALL the params,
        as they can't be empty or the user will get all their data empty,
        so we only send the filled params
        :param user_id: id of the user to change
        :param kwargs: Any param the the Gitlab API supports
        :return: Dict of the user
        """
        data = {}

        if kwargs:
            data.update(kwargs)

        request = requests.put("{}/{}".format(self.users_url, user_id),
                               headers=self.headers, data=data,
                               verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getsshkeys(self, page=1, per_page=20):
        """
        Gets all the ssh keys for the current user
        :return: a dictionary with the lists
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get(self.keys_url, headers=self.headers, params=data,
                               verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def getsshkey(self, key_id):
        """
        Get a single ssh key identified by key_id
        :param key_id: the id of the key
        :return: the key itself
        """
        request = requests.get("{}/{}".format(self.keys_url, key_id),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def addsshkey(self, title, key):
        """
        Add a new ssh key for the current user
        :param title: title of the new key
        :param key: the key itself
        :return: true if added, false if it didn't add it
        (it could be because the name or key already exists)
        """
        data = {"title": title, "key": key}
        request = requests.post(self.keys_url, headers=self.headers, data=data,
                                verify=self.verify_ssl)
        if request.status_code == 201:
            return True
        else:

            return False

    def addsshkeyuser(self, user_id, title, key):
        """
        Add a new ssh key for the user identified by id
        :param user_id: id of the user to add the key to
        :param title: title of the new key
        :param key: the key itself
        :return: true if added, false if it didn't add it
        (it could be because the name or key already exists)
        """
        data = {"title": title, "key": key}

        request = requests.post("{}/{}/keys".format(self.users_url, user_id),
                                headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return True
        else:

            return False

    def deletesshkey(self, key_id):
        """
        Deletes an sshkey for the current user identified by id
        :param key_id: the id of the key
        :return: False if it didn't delete it, True if it was deleted
        """
        request = requests.delete("{}/{}".format(self.keys_url, key_id),
                                  headers=self.headers, verify=self.verify_ssl)
        if request.content == b"null":
            return False
        else:
            return True

    def getprojects(self, page=1, per_page=20):
        """
        Returns a dictionary of all the projects
        :param page: Which page to return (default is 1)
        :param per_page: Number of items to return per page (default is 20)
        :return: list with the repo name, description, last activity,
         web url, ssh url, owner and if its public
        """
        data = {'page': page, 'per_page': per_page}

        request = requests.get(self.projects_url, params=data,
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getprojectsall(self, page=1, per_page=20):
        """
        Returns a dictionary of all the projects for admins only
        :param page: Which page to return (default is 1)
        :param per_page: Number of items to return per page (default is 20)
        :return: list with the repo name, description, last activity,
         web url, ssh url, owner and if its public
        """
        data = {'page': page, 'per_page': per_page}

        request = requests.get("{}/all".format(self.projects_url), params=data,
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getprojectsowned(self, page=1, per_page=20):
        """
        Returns a dictionary of all the projects for the current user
        :param page: Which page to return (default is 1)
        :param per_page: Number of items to return per page (default is 20)
        :return: list with the repo name, description, last activity,
         web url, ssh url, owner and if its public
        """
        data = {'page': page, 'per_page': per_page}

        request = requests.get("{}/owned".format(self.projects_url), params=data,
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getproject(self, project_id):
        """
        Get info for a project identified by id
        :param project_id: id of the project
        :return: False if not found, a dictionary if found
        """
        request = requests.get("{}/{}".format(self.projects_url, project_id),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def getprojectevents(self, project_id, page=1, per_page=20):
        """
        Get the project identified by id, events(commits)
        :param project_id: id of the project
        :param page: Which page to return (default is 1)
        :param per_page: Number of items to return per page (default is 20)
        :return: False if no project with that id, a dictionary
         with the events if found
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/events".format(self.projects_url, project_id), params=data, headers=self.headers,
                               verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def createproject(self, name, **kwargs):
        """
        Creates a new project owned by the authenticated user.
        :param name: new project name
        :param path: custom repository name for new project. By default generated based on name
        :param namespace_id: namespace for the new project (defaults to user)
        :param description: short project description
        :param issues_enabled:
        :param merge_requests_enabled:
        :param wiki_enabled:
        :param snippets_enabled:
        :param public: if true same as setting visibility_level = 20
        :param visibility_level:
        :param sudo:
        :param import_url:
        :return:
        """
        data = {"name": name}

        if kwargs:
            data.update(kwargs)

        request = requests.post(self.projects_url, headers=self.headers,
                                data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        elif request.status_code == 403:
            if "Your own projects limit is 0" in request.text:
                print(request.text)
                return False
        else:

            return False

    def deleteproject(self, project_id):
        """
        Delete a project
        :param project_id: project id
        :return: always true
        """
        request = requests.delete("{}/{}".format(self.projects_url, project_id),
                                  headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True

    def createprojectuser(self, user_id, name, **kwargs):
        """

        :param user_id: user_id of owner
        :param name: new project name
        :param description: short project description
        :param default_branch: 'master' by default
        :param issues_enabled:
        :param merge_requests_enabled:
        :param wiki_enabled:
        :param snippets_enabled:
        :param public: if true same as setting visibility_level = 20
        :param visibility_level:
        :param import_url:
        :param sudo:
        :return:
        """
        data = {"name": name}

        if kwargs:
            data.update(kwargs)

        request = requests.post("{}/user/{}".format(self.projects_url, user_id),
                                headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return True
        else:

            return False

    def getprojectmembers(self, project_id, query=None, page=1, per_page=20):
        """
        lists the members of a given project id
        :param project_id: the project id
        :param query: Optional search query
        :param page: Which page to return (default is 1)
        :param per_page: Number of items to return per page (default is 20)
        :return: the projects memebers, false if there is an error
        """
        data = {'page': page, 'per_page': per_page}
        if query:
            data['query'] = query
        request = requests.get("{}/{}/members".format(self.projects_url, project_id),
                               params=data, headers=self.headers,
                               verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def addprojectmember(self, project_id, user_id, access_level):
        # check the access level and put into a number
        """
        adds a project member to a project
        :param project_id: project id
        :param user_id: user id
        :param access_level: access level, see gitlab help to know more
        :return: True if success
        """
        if access_level.lower() == "master":
            access_level = 40
        elif access_level.lower() == "developer":
            access_level = 30
        elif access_level.lower() == "reporter":
            access_level = 20
        else:
            access_level = 10
        data = {"id": project_id, "user_id": user_id, "access_level": access_level}

        request = requests.post("{}/{}/members".format(self.projects_url, project_id),
                                headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return True
        else:
            return False

    def editprojectmember(self, project_id, user_id, access_level):
        """
        edit a project member
        :param project_id: project id
        :param user_id: user id
        :param access_level: access level
        :return: True if success
        """
        if access_level.lower() == "master":
            access_level = 40
        elif access_level.lower() == "developer":
            access_level = 30
        elif access_level.lower() == "reporter":
            access_level = 20
        else:
            access_level = 10
        data = {"id": project_id, "user_id": user_id,
                "access_level": access_level}

        request = requests.put("{}/{}/members/{}".format(self.projects_url, project_id, user_id),
                               headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:

            return False

    def deleteprojectmember(self, project_id, user_id):
        """
        Delete a project member
        :param project_id: project id
        :param user_id: user id
        :return: always true
        """
        request = requests.delete("{}/{}/members/{}".format(self.projects_url, project_id, user_id),
                                  headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True  # It always returns true

    def getprojecthooks(self, project_id, page=1, per_page=20):
        """
        get all the hooks from a project
        :param project_id: project id
        :return: the hooks
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/hooks".format(self.projects_url, project_id), params=data,
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getprojecthook(self, project_id, hook_id):
        """
        get a particular hook from a project
        :param project_id: project id
        :param hook_id: hook id
        :return: the hook
        """
        request = requests.get("{}/{}/hooks/{}".format(self.projects_url, project_id, hook_id),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def addprojecthook(self, project_id, url):
        """
        add a hook to a project
        :param project_id: project id
        :param url: url of the hook
        :return: True if success
        """
        data = {"id": project_id, "url": url}
        request = requests.post("{}/{}/hooks".format(self.projects_url, project_id),
                                headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return True
        else:
            return False

    def editprojecthook(self, project_id, hook_id, url):
        """
        edit an existing hook from a project
        :param project_id: project id
        :param hook_id: hook id
        :param url: the new url
        :param sudo: do the request as another user
        :return: True if success
        """
        data = {"id": project_id, "hook_id": hook_id, "url": url}

        request = requests.put("{}/{}/hooks/{}".format(self.projects_url, project_id, hook_id),
                               headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:
            return False

    def deleteprojecthook(self, project_id, hook_id):
        """
        delete a project hook
        :param project_id: project id
        :param hook_id: hook id
        :return: True if success
        """
        request = requests.delete("{}/{}/hooks/{}".format(self.projects_url, project_id, hook_id),
                                  headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:
            return False

    def getsystemhooks(self, page=1, per_page=20):
        """
        Get all system hooks
        :return: list of hooks
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get(self.hook_url, params=data, headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def addsystemhook(self, url):
        """
        add a hook to a project
        :param url: url of the hook
        :return: True if success
        """
        data = {"url": url}
        request = requests.post(self.hook_url, headers=self.headers,
                                data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return True
        else:
            return False

    def testsystemhook(self, hook_id):
        """
        Test a system hook
        :param hook_id: hook id
        :return: list of hooks
        """
        data = {"id": hook_id}
        request = requests.get(self.hook_url, data=data,
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def deletesystemhook(self, hook_id):
        """
        delete a project hook
        :param hook_id: hook id
        :return: True if success
        """
        data = {"id": hook_id}
        request = requests.delete("{}/{}".format(self.hook_url, hook_id), data=data,
                                  headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:
            return False

    def getbranches(self, project_id, page=1, per_page=20):
        """
        list all the branches from a project
        :param project_id: project id
        :return: the branches
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/repository/branches".format(self.projects_url, project_id), params=data,
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getbranch(self, project_id, branch):
        """
        list one branch from a project
        :param project_id: project id
        :param branch: branch id
        :return: the branch
        """
        request = requests.get("{}/{}/repository/branches/{}".format(self.projects_url, project_id, branch),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def createbranch(self, project_id, branch, ref):
        """
        Create branch from commit SHA or existing branch
        :param project_id:  The ID of a project
        :param branch: The name of the branch
        :param ref: Create branch from commit SHA or existing branch
        :return: True if success, False if not
        """
        data = {"id": project_id, "branch_name": branch, "ref": ref}

        request = requests.post("{}/{}/repository/branches".format(self.projects_url, project_id),
                                headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def deletebranch(self, project_id, branch):
        """
        Delete branch by name
        :param project_id:  The ID of a project
        :param branch: The name of the branch
        :return: True if success, False if not
        """

        request = requests.delete("{}/{}/repository/branches/{}".format(self.projects_url, project_id, branch),
                                  headers=self.headers, verify=self.verify_ssl)

        if request.status_code == 200:
            return True
        else:
            return False

    def protectbranch(self, project_id, branch):
        """
        protect a branch from changes
        :param project_id: project id
        :param branch: branch id
        :return: True if success
        """
        request = requests.put("{}/{}/repository/branches/{}/protect".format(self.projects_url, project_id, branch),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:
            return False

    def unprotectbranch(self, project_id, branch):
        """
        stop protecting a branch
        :param project_id: project id
        :param branch: branch id
        :return: true if success
        """
        request = requests.put("{}/{}/repository/branches/{}/unprotect".format(self.projects_url, project_id, branch),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:

            return False

    def createforkrelation(self, project_id, from_project_id):
        """
        create a fork relation. This DO NOT create a fork but only adds
        the relation between 2 repositories
        :param project_id: project id
        :param from_project_id: from id
        :return: true if success
        """
        data = {"id": project_id, "forked_from_id": from_project_id}
        request = requests.post("{}/{}/fork/{}".format(self.projects_url, project_id, from_project_id),
                                headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return True
        else:

            return False

    def removeforkrelation(self, project_id):
        """
        remove an existing fork relation. this DO NOT remove the fork,
        only the relation between them
        :param project_id: project id
        :return: true if success
        """
        request = requests.delete("{}/{}/fork".format(self.projects_url, project_id),
                                  headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:

            return False

    def createfork(self, project_id):
        """
        Forks a project into the user namespace of the authenticated user.
        :param project_id: Project ID to fork
        :return: True if succeed
        """

        request = requests.post("{}/fork/{}".format(self.projects_url, project_id))

        if request.status_code == 200:
            return True
        else:
            return False

    def getissues(self, page=1, per_page=20):
        """
        Return a global list of issues for your user.
        :param page: Which page to return (default is 1)
        :param per_page: Number of items to return per page (default is 20)
        """
        data = {'page': page, 'per_page': per_page}

        request = requests.get("{}/api/v3/issues".format(self.host),
                               params=data, headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def getprojectissues(self, project_id, page=1, per_page=20):
        """
        Return a list of issues for project id_.
        :param project_id: The id for the project.
        :param page: Which page to return (default is 1)
        :param per_page: Number of items to return per page (default is 20)
        """
        data = {'page': page, 'per_page': per_page}

        request = requests.get("{}/{}/issues".format(self.projects_url, project_id),
                               params=data, headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def getprojectissue(self, project_id, issue_id):
        """
        get an specific issue id from a project
        :param project_id: project id
        :param issue_id: issue id
        :return: the issue
        """
        request = requests.get("{}/{}/issues/{}".format(self.projects_url, project_id, issue_id),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def createissue(self, project_id, title, **kwargs):
        """
        create a new issue
        :param project_id: project id
        :param title: title of the issue
        :return: dict with the issue created
        """
        data = {"id": id, "title": title}
        if kwargs:
            data.update(kwargs)
        request = requests.post("{}/{}/issues".format(self.projects_url, project_id),
                                headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def editissue(self, project_id, issue_id, **kwargs):
        """
        edit an existing issue data
        :param project_id: project id
        :param issue_id: issue id
        :return: true if success
        """
        data = {"id": project_id, "issue_id": issue_id}
        if kwargs:
            data.update(kwargs)
        request = requests.put("{}/{}/issues/{}".format(self.projects_url, project_id, issue_id),
                               headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getmilestones(self, project_id, page=1, per_page=20):
        """
        get the milestones for a project
        :param project_id: project id
        :return: the milestones
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/milestones".format(self.projects_url, project_id), params=data,
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def getmilestone(self, project_id, milestone_id):
        """
        get an specific milestone
        :param project_id: project id
        :param milestone_id: milestone id
        :return: the milestone
        """
        request = requests.get("{}/{}/milestones/{}".format(self.projects_url, project_id, milestone_id),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def createmilestone(self, project_id, title, **kwargs):
        """
        create a new milestone
        :param project_id: project id
        :param title: title
        :param description: description
        :param due_date: due date
        :param sudo: do the request as another user
        :return: true if success
        """
        data = {"id": project_id, "title": title}

        if kwargs:
            data.update(kwargs)

        request = requests.post("{}/{}/milestones".format(self.projects_url, project_id),
                                headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def editmilestone(self, project_id, milestone_id, **kwargs):
        """
        edit an existing milestone
        :param project_id: project id
        :param milestone_id: milestone id
        :param title: title
        :param description: description
        :param due_date: due date
        :param state_event: state
        :param sudo: do the request as another user
        :return: true if success
        """
        data = {"id": project_id, "milestone_id": milestone_id}
        if kwargs:
            data.update(kwargs)
        request = requests.put("{}/{}/milestones/{}".format(self.projects_url, project_id, milestone_id),
                               headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def getdeploykeys(self, project_id, page=1, per_page=20):
        """
        Get a list of a project's deploy keys.
        :param project_id: project id
        :return: the keys in a dictionary if success, false if not
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/keys".format(self.projects_url, project_id), params=data,
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def getdeploykey(self, project_id, key_id):
        """
        Get a single key.
        :param project_id: project id
        :param key_id: key id
        :return: the key in a dict if success, false if not
        """
        request = requests.get("{}/{}/keys/{}".format(self.projects_url, project_id, key_id),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def adddeploykey(self, project_id, title, key):
        """
        Creates a new deploy key for a project.
        If deploy key already exists in another project - it will be joined
        to project but only if original one was is accessible by same user
        :param project_id: project id
        :param title: title of the key
        :param key: the key itself
        :return: true if sucess, false if not
        """
        data = {"id": project_id, "title": title, "key": key}

        request = requests.post("{}/{}/keys".format(self.projects_url, project_id),
                                headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return True
        else:

            return False

    def deletedeploykey(self, project_id, key_id):
        """
        Delete a deploy key from a project
        :param project_id: project id
        :param key_id: key id to delete
        :return: true if success, false if not
        """
        request = requests.delete("{}/{}/keys/{}".format(self.projects_url, project_id, key_id),
                                  headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:

            return False

    def creategroup(self, name, path):
        """
        Creates a new group
        :param name: The name of the group
        :param path: The path for the group
        """
        request = requests.post(self.groups_url,
                                data={'name': name, 'path': path},
                                headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:
            msg = json.loads(request.content.decode("utf-8"))['message']
            return exceptions.HttpError(msg)

    def getgroups(self, group_id=None, page=1, per_page=20):
        """
        Retrieve group information
        :param group_id: Specify a group. Otherwise, all groups are returned
        :param page: Which page to return (default is 1)
        :param per_page: Number of items to return per page (default is 20)
        """
        data = {'page': page, 'per_page': per_page}

        request = requests.get("{}/{}".format(self.groups_url,
                                              group_id if group_id else ""),
                               params=data, headers=self.headers,
                               verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def moveproject(self, group_id, project_id):
        """
        Move a given project into a given group
        :param group_id: ID of the destination group
        :param project_id: ID of the project to be moved
        """
        request = requests.post("{}/{}/projects/{}".format(self.groups_url,
                                                              group_id,
                                                              project_id),
                                headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def getmergerequests(self, project_id, page=1, per_page=20, state=None):
        """
        Get all the merge requests for a project.
        :param project_id: ID of the project to retrieve merge requests for
        :param page: If pagination is set, which page to return
        :param state: Passes merge request state to filter them by it
        :param per_page: Number of merge requests to return per page
        """
        data = {'page': page, 'per_page': per_page, 'state': state}

        request = requests.get('{}/{}/merge_requests'.format(self.projects_url, project_id),
                               params=data, headers=self.headers, verify=self.verify_ssl)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def getmergerequest(self, project_id, mergerequest_id):
        """
        Get information about a specific merge request.
        :type project_id: int
        :param project_id: ID of the project
        :param mergerequest_id: ID of the merge request
        """
        request = requests.get('{}/{}/merge_request/{}'.format(self.projects_url, project_id, mergerequest_id),
                               headers=self.headers, verify=self.verify_ssl)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def getmergerequestcomments(self, project_id, mergerequest_id, page=1, per_page=20):
        """
        Get comments of a merge request.
        :type project_id: int
        :param project_id: ID of the project
        :param mergerequest_id: ID of the merge request
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get('{}/{}/merge_request/{}/comments'.format(self.projects_url, project_id, mergerequest_id),
                               params=data, headers=self.headers, verify=self.verify_ssl)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def createmergerequest(self, project_id, sourcebranch, targetbranch,
                           title, target_project_id=None, assignee_id=None):
        """
        Create a new merge request.
        :param project_id: ID of the project originating the merge request
        :param sourcebranch: name of the branch to merge from
        :param targetbranch: name of the branch to merge to
        :param title: Title of the merge request
        :param assignee_id: Assignee user ID
        """
        data = {'source_branch': sourcebranch,
                'target_branch': targetbranch,
                'title': title,
                'assignee_id': assignee_id,
                'target_project_id': target_project_id}

        request = requests.post('{}/{}/merge_requests'.format(self.projects_url, project_id),
                                data=data, headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:

            return False

    def updatemergerequest(self, project_id, mergerequest_id, **kwargs):
        """
        Update an existing merge request.
        :param project_id: ID of the project originating the merge request
        :param mergerequest_id: ID of the merge request to update
        :param sourcebranch: name of the branch to merge from
        :param targetbranch: name of the branch to merge to
        :param title: Title of the merge request
        :param assignee_id: Assignee user ID
        :param closed: MR status.  True = closed
        """
        data = {}

        if kwargs:
            data.update(kwargs)

        request = requests.put('{}/{}/merge_request/{}'.format(self.projects_url, project_id, mergerequest_id),
                               data=data, headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:

            return False

    def acceptmergerequest(self, project_id, mergerequest_id, merge_commit_message=None):
        """
        Update an existing merge request.
        :param project_id: ID of the project originating the merge request
        :param mergerequest_id: ID of the merge request to accept
        :param merge_commit_message: Custom merge commit message
        """

        data = {'merge_commit_message': merge_commit_message}

        request = requests.put('{}/{}/merge_request/{}/merge'.format(self.projects_url, project_id, mergerequest_id),
                               data=data, headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:
            return False

    def addcommenttomergerequest(self, project_id, mergerequest_id, note):
        """
        Add a comment to a merge request.
        :param project_id: ID of the project originating the merge request
        :param mergerequest_id: ID of the merge request to comment on
        :param note: Text of comment
        """
        request = requests.post('{}/{}/merge_request/{}/comments'.format(self.projects_url, project_id, mergerequest_id),
                                data={'note': note}, headers=self.headers, verify=self.verify_ssl)

        if request.status_code == 201:
            return True
        else:

            return False

    def getsnippets(self, project_id, page=1, per_page=20):
        """
        Get all the snippets of the project identified by project_id
        @param project_id: project id to get the snippets from
        @return: list of dictionaries
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/snippets".format(self.projects_url, project_id), params=data,
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getsnippet(self, project_id, snippet_id):
        """
        Get one snippet from a project
        @param project_id: project id to get the snippet from
        @param snippet_id: snippet id
        @return: dictionary
        """
        request = requests.get("{}/{}/snippets/{}".format(self.projects_url, project_id, snippet_id),
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return json.loads(request.content.decode('utf-8'))
        else:
            return False

    def createsnippet(self, project_id, title, file_name, code, lifetime=""):
        """
        Creates an snippet
        @param project_id: project id to create the snippet under
        @param title: title of the snippet
        @param file_name: filename for the snippet
        @param code: content of the snippet
        @param lifetime: expiration date
        @return: True if correct, false if failed
        """
        data = {"id": project_id, "title": title, "file_name": file_name, "code": code}
        if lifetime != "":
            data["lifetime"] = lifetime
        request = requests.post("{}/{}/snippets".format(self.projects_url, project_id),
                                data=data, verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getsnippetcontent(self, project_id, snippet_id):
        """
        Get raw content of a given snippet
        :param project_id: project_id for the snippet
        :param snippet_id: snippet id
        :return: the content of the snippet
        """
        request = requests.get("{}/{}/snippets/{}/raw".format(self.projects_url, project_id, snippet_id),
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return request.content.decode("utf-8")
        else:
            return False

    def deletesnippet(self, project_id, snippet_id):
        """
        Deletes a given snippet
        :param project_id:
        :param snippet_id:
        :return:
        """
        request = requests.delete("{}/{}/snippets/{}".format(self.projects_url, project_id, snippet_id),
                                  headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:
            return False

    def getrepositories(self, project_id, page=1, per_page=20):
        """
        Gets all repositories for a project id
        :param project_id:
        :return:
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/repository/branches".format(self.projects_url, project_id), params=data,
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getrepositorybranch(self, project_id, branch):
        """
        Get a single project repository branch.
        :param project_id:
        :param branch:
        :return:
        """
        request = requests.get("{}/{}/repository/branches/{}".format(self.projects_url, project_id, branch),
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        elif request.status_code == 404:
            if json.loads(request.content.decode("utf-8"))['message'] == "404 Branch does not exist Not Found":
                # In the future we should raise an exception here
                return False
        else:
            return False

    def protectrepositorybranch(self, project_id, branch):
        """
        Protects a single project repository branch. This is an idempotent function,
        protecting an already protected repository branch still returns a 200 OK status code.
        :param project_id:
        :param branch:
        :return:
        """
        request = requests.put("{}/{}/repository/branches/{}/protect".format(self.projects_url, project_id, branch),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def unprotectrepositorybranch(self, project_id, branch):
        """
        Unprotects a single project repository branch. This is an idempotent function,
        unprotecting an already unprotected repository branch still returns a 200 OK status code.
        :param project_id:
        :param branch:
        :return:
        """
        request = requests.put("{}/{}/repository/branches/{}/unprotect".format(self.projects_url, project_id, branch),
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return

    def getrepositorytags(self, project_id, page=1, per_page=20):
        """
        Get a list of repository tags from a project, sorted by name in reverse alphabetical order.
        :param project_id:
        :return:
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/repository/tags".format(self.projects_url, project_id), params=data,
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def createrepositorytag(self, project_id, tag_name, ref, message=None):
        """
        Creates new tag in the repository that points to the supplied ref.
        :param project_id:
        :param tag_name:
        :param ref:
        :param message:
        :return:
        """

        data = {"id": project_id, "tag_name": tag_name, "ref": ref, "message": message}
        request = requests.post("{}/{}/repository/tags".format(self.projects_url, project_id), data=data,
                                verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getrepositorycommits(self, project_id, ref_name=None, page=1, per_page=20):
        """
        Get a list of repository commits in a project.
        :param project_id: The ID of a project
        :param ref_name: The name of a repository branch or tag or if not given the default branch
        :return:
        """
        data = {'page': page, 'per_page': per_page}
        if ref_name is not None:
            data.update({"ref_name": ref_name})
        request = requests.get("{}/{}/repository/commits".format(self.projects_url, project_id),
                               verify=self.verify_ssl, params=data, headers=self.headers)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getrepositorycommit(self, project_id, sha1):
        """
        Get a specific commit identified by the commit hash or name of a branch or tag.
        :param project_id: The ID of a project
        :param sha1: The commit hash or name of a repository branch or tag
        :return:
        """
        request = requests.get("{}/{}/repository/commits/{}".format(self.projects_url, project_id, sha1),
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getrepositorycommitdiff(self, project_id, sha1):
        """
        Get the diff of a commit in a project.
        :param project_id: The ID of a project
        :param sha1: The name of a repository branch or tag or if not given the default branch
        :return:
        """
        request = requests.get("{}/{}/repository/commits/{}/diff".format(self.projects_url, project_id, sha1),
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getrepositorytree(self, project_id, **kwargs):
        """
        Get a list of repository files and directories in a project.
        :param project_id: The ID of a project
        :param path: The path inside repository. Used to get contend of subdirectories
        :param ref_name: The name of a repository branch or tag or if not given the default branch
        :return:
        """
        data = {}
        if kwargs:
            data.update(kwargs)

        request = requests.get("{}/{}/repository/tree".format(self.projects_url, project_id), params=data,
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getrawfile(self, project_id, sha1, filepath):
        """
        Get the raw file contents for a file by commit SHA and path.
        :param project_id: The ID of a project
        :param sha1: The commit or branch name
        :param filepath: The path the file
        :return:
        """
        data = {"filepath": filepath}
        request = requests.get("{}/{}/repository/blobs/{}".format(self.projects_url, project_id, sha1),
                               params=data, verify=self.verify_ssl,
                               headers=self.headers)
        if request.status_code == 200:
            return request.content.decode("utf-8")
        else:
            return False

    def getrawblob(self, project_id, sha1):
        """
        Get the raw file contents for a blob by blob SHA.
        :param project_id: The ID of a project
        :param sha1:
        :return:
        """
        request = requests.get("{}/{}/repository/raw_blobs/{}".format(self.projects_url, project_id, sha1),
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return request.content.decode("utf-8")
        else:
            return False

    def getcontributors(self, project_id, page=1, per_page=20):
        """
        Get repository contributors list
        :param project_id: The ID of a project
        :return:
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/repository/contributors".format(self.projects_url, project_id), params=data,
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def compare_branches_tags_commits(self, project_id, from_id, to_id):
        """
        Compare branches, tags or commits
        :param project_id: The ID of a project
        :param from_id: the commit sha or branch name
        :param to_id: the commit sha or branch name
        return commit list and diff between two branches tags or commits provided by name
        hash value
        """
        data = {"from": from_id, "to": to_id}
        request = requests.get("{}/{}/repository/compare".format(self.projects_url, project_id),
                               params=data, verify=self.verify_ssl,
                               headers=self.headers)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def searchproject(self, search, page=1, per_page=20):
        """
        Search for projects by name which are accessible to the authenticated user.
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}".format(self.search_url, search), params=data,
                               verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getfilearchive(self, project_id, filepath=""):
        """
        Get an archive of the repository
        """
        request = requests.get("{}/{}/repository/archive".format(self.projects_url, project_id),
                               verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 200:
            if filepath == "":
                filepath = request.headers['content-disposition'].split(";")[1].split("=")[1].strip('"')
            with open(filepath, "wb") as filesave:
                filesave.write(request.content)
                # TODO: Catch oserror exceptions as no permissions and such
                # TODO: change the filepath to a path and keep always the filename?
            return True
        else:
            msg = json.loads(request.content.decode("utf-8"))['message']
            raise exceptions.HttpError(msg)

    def deletegroup(self, group_id):
        """
        Deletes an group by ID
        :param group_id: id of the group to delete
        :return: True if it deleted, False if it couldn't. False could happen
        for several reasons, but there isn't a
        good way of differentiating them
        """
        request = requests.delete("{}/{}".format(self.groups_url, group_id),
                                  headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:
            return False

    def getgroupmembers(self, group_id, page=1, per_page=20):
        """
        lists the members of a given group id
        :param group_id: the group id
        :param page: which page to return (default is 1)
        :param per_page: number of items to return per page (default is 20)
        :return: the group's members
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/members".format(self.groups_url, group_id), params=data,
                               headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def addgroupmember(self, group_id, user_id, access_level):
        """
        # check the access level and put into a number

        adds a project member to a project
        :param user_id: user id
        :param access_level: access level, see gitlab help to know more
        :return: True if success
        """
        if not isinstance(access_level, int):
            if access_level.lower() == "owner":
                access_level = 50
            elif access_level.lower() == "master":
                access_level = 40
            elif access_level.lower() == "developer":
                access_level = 30
            elif access_level.lower() == "reporter":
                access_level = 20
            elif access_level.lower() == "guest":
                access_level = 10
            else:
                return False

        data = {"id": group_id, "user_id": user_id, "access_level": access_level}

        request = requests.post("{}/{}/members".format(self.groups_url, group_id),
                                headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 201:
            return True
        else:
            return False

    def deletegroupmember(self, group_id, user_id):
        """
        Delete a group member
        :param group_id: group id to remove the member from
        :param user_id: user id
        :return: always true
        """
        request = requests.delete("{}/{}/members/{}".format(self.groups_url, group_id, user_id),
                                  headers=self.headers, verify=self.verify_ssl)
        if request.status_code == 200:
            return True  # It always returns true

    def getissuewallnotes(self, project_id, issue_id, page=1, per_page=20):
        """
        get the notes from the wall of a issue
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/issues/{}/notes".format(self.projects_url, project_id, issue_id),  params=data,
                               verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getissuewallnote(self, project_id, issue_id, note_id):
        """
        get one note from the wall of the issue
        """
        request = requests.get("{}/{}/issues/{}/notes/{}".format(self.projects_url, project_id, issue_id, note_id),
                               verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def createissuewallnote(self, project_id, issue_id, content):
        """
        create a new note
        """
        data = {"body": content}
        request = requests.post("{}/{}/issues/{}/notes".format(self.projects_url, project_id, issue_id),
                                verify=self.verify_ssl, headers=self.headers, data=data)

        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getsnippetwallnotes(self, project_id, snippet_id, page=1, per_page=20):
        """
        get the notes from the wall of a snippet
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/snippets/{}/notes".format(self.projects_url, project_id, snippet_id),
                               params=data, verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getsnippetwallnote(self, project_id, snippet_id, note_id):
        """
        get one note from the wall of the snippet
        """
        request = requests.get("{}/{}/snippets/{}/notes/{}".format(self.projects_url, project_id, snippet_id, note_id),
                               verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def createsnippetewallnote(self, project_id, snippet_id, content):
        """
        create a new note
        """
        data = {"body": content}
        request = requests.post("{}/{}/snippets/{}/notes".format(self.projects_url, project_id, snippet_id),
                                verify=self.verify_ssl, headers=self.headers, data=data)

        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getmergerequestwallnotes(self, project_id, merge_request_id, page=1, per_page=20):
        """
        get the notes from the wall of a merge request
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/merge_requests/{}/notes".format(self.projects_url, project_id, merge_request_id),
                               params=data, verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def getmergerequestwallnote(self, project_id, merge_request_id, note_id):
        """
        get one note from the wall of the merge request
        """
        request = requests.get("{}/{}/merge_requests/{}/notes/{}".format(self.projects_url, project_id,
                                                                         merge_request_id, note_id),
                               verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def createmergerequestewallnote(self, project_id, merge_request_id, content):
        """
        create a new note
        """
        data = {"body": content}
        request = requests.post("{}/{}/merge_requests/{}/notes".format(self.projects_url, project_id, merge_request_id),
                                verify=self.verify_ssl, headers=self.headers, data=data)

        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def createfile(self, project_id, file_path, branch_name, content, commit_message):
        """
        Creates a new file in the repository
        :param project_id: project id
        :param file_path: Full path to new file. Ex. lib/class.rb
        :param branch_name: The name of branch
        :param content: File content
        :param commit_message: Commit message
        :return: true if success, false if not
        """
        data = {"file_path": file_path, "branch_name": branch_name,
                "content": content, "commit_message": commit_message}
        request = requests.post("{}/{}/repository/files".format(self.projects_url, project_id),
                                verify=self.verify_ssl, headers=self.headers, data=data)
        if request.status_code == 201:
            return True
        else:
            return False

    def updatefile(self, project_id, file_path, branch_name, content, commit_message):
        """
        Updates an existing file in the repository
        :param project_id: project id
        :param file_path: Full path to new file. Ex. lib/class.rb
        :param branch_name: The name of branch
        :param content: File content
        :param commit_message: Commit message
        :return: true if success, false if not
        """
        data = {"file_path": file_path, "branch_name": branch_name,
                "content": content, "commit_message": commit_message}
        request = requests.put("{}/{}/repository/files".format(self.projects_url, project_id),
                               headers=self.headers, data=data, verify=self.verify_ssl)

        if request.status_code == 200:
            return True
        else:
            return False

    def getfile(self, project_id, file_path, ref):
        """
        Allows you to receive information about file in repository like name, size, content.
        Note that file content is Base64 encoded.
        :param project_id: project_id
        :param file_path: Full path to file. Ex. lib/class.rb
        :param ref: The name of branch, tag or commit
        :return:
        """
        data = {"file_path": file_path, "ref": ref}
        request = requests.get("{}/{}/repository/files".format(self.projects_url, project_id),
                               headers=self.headers, data=data, verify=self.verify_ssl)
        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def deletefile(self, project_id, file_path, branch_name, commit_message):
        """
        Deletes existing file in the repository
        :param project_id: project id
        :param file_path: Full path to new file. Ex. lib/class.rb
        :param branch_name: The name of branch
        :param commit_message: Commit message
        :return: true if success, false if not
        """
        data = {"file_path": file_path, "branch_name": branch_name,
                "commit_message": commit_message}
        request = requests.delete("{}/{}/repository/files".format(self.projects_url, project_id),
                                  headers=self.headers, data=data,
                                  verify=self.verify_ssl)
        if request.status_code == 200:
            return True
        else:
            return False

    def setgitlabciservice(self, project_id, token, project_url):
        """
        Set GitLab CI service for project
        :param project_id: project id
        :param token: CI project token
        :param project_url: CI project url
        :return: true if success, false if not
        """
        data = {"token": token, "project_url": project_url}
        request = requests.put("{}/{}/services/gitlab-ci".format(self.projects_url, project_id),
                               verify=self.verify_ssl, headers=self.headers, data=data)

        if request.status_code == 200:
            return True
        else:
            return False

    def deletegitlabciservice(self, project_id, token, project_url):
        """
        Delete GitLab CI service settings
        :return: true if success, false if not
        """
        request = requests.delete("{}/{}/services/gitlab-ci".format(self.projects_url,project_id),
                                  headers=self.headers, verify=self.verify_ssl)

        if request.status_code == 200:
            return True
        else:
            return False

    def getlabels(self, project_id, page=1, per_page=20):
        """
        Get all labels for given project.
        :param project_id: The ID of a project
        :return: list of the labels
        """
        data = {'page': page, 'per_page': per_page}
        request = requests.get("{}/{}/labels".format(self.projects_url, project_id), params=data,
                               verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def createlabel(self, project_id, name, color):
        """
        Creates a new label for given repository with given name and color.
        :param project_id: The ID of a project
        :param name: The name of the label
        :param color: Color of the label given in 6-digit hex notation with leading '#' sign (e.g. #FFAABB)
        :return:
        """

        data = {"name": name, "color": color}
        request = requests.post("{}/{}/labels".format(self.projects_url, project_id), data=data,
                                verify=self.verify_ssl, headers=self.headers)
        if request.status_code == 201:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False

    def deletelabel(self, project_id, name):
        """
        Deletes a label given by its name.
        :param project_id: The ID of a project
        :param name: The name of the label
        :return: True if succeed
        """
        data = {"name": name}

        request = requests.delete("{}/{}/labels".format(self.projects_url, project_id), data=data,
                                  verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 200:
            return True
        else:
            return False

    def editlabel(self, project_id, name, new_name=None, color=None):
        """
        Updates an existing label with new name or now color. At least one parameter is required, to update the label.
        :param project_id: The ID of a project
        :param name: The name of the label
        :return: True if succeed
        """
        data = {"name": name, "new_name": new_name, "color": color}

        request = requests.put("{}/{}/labels".format(self.projects_url, project_id), data=data,
                               verify=self.verify_ssl, headers=self.headers)

        if request.status_code == 200:
            return json.loads(request.content.decode("utf-8"))
        else:
            return False
