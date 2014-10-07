# -*- coding: utf-8 -*-
#
#
#  TheVirtualBrain-Scientific Package. This package holds all simulators, and 
# analysers necessary to run brain-simulations. You can use it stand alone or
# in conjunction with TheVirtualBrain-Framework Package. See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General 
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
Basic TVB Settings are defined here, some are grouped by they
category of usage (e.g. cluster related, web related, etc).

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
"""

import os
import sys
from subprocess import Popen, PIPE
from tvb.basic.config import stored
from tvb.basic.config.environment import Environment
from tvb.basic.config.utils import EnhancedDictionary, LibraryModulesFinder



class VersionSettings(object):
    """
    Gather settings related to various version numbers of TVB application
    """

    # Current release number
    BASE_VERSION = "1.2.3"

    # Current DB version. Increment this and create a new xxx_update_db.py migrate script
    DB_STRUCTURE_VERSION = 12

    # This is the version of the data stored in H5 and XML files
    # and should be used by next versions to know how to import
    # data in TVB format, in case data structure changes.
    # Value should be updated every time data structure is changed.
    DATA_VERSION = 2
    DATA_VERSION_ATTRIBUTE = "Data_version"

    # This is the version of the tvb project.
    # It should be updated every time the project structure changes
    # Should this be sync-ed with data version changes?
    PROJECT_VERSION = 1


    def __init__(self, manager, bin_folder):

        # Used for reading the version file from it
        self.BIN_FOLDER = bin_folder

        # Concatenate BASE_VERSION with svn revision number
        self.CURRENT_VERSION = self.BASE_VERSION + '-' + str(self.SVN_VERSION)

        # The version up until we done the upgrade properly for the file data storage.
        self.DATA_CHECKED_TO_VERSION = manager.get_attribute(stored.KEY_LAST_CHECKED_FILE_VERSION, 1, int)

        # The version up until we done the upgrade properly for the file data storage.
        self.CODE_CHECKED_TO_VERSION = manager.get_attribute(stored.KEY_LAST_CHECKED_CODE_VERSION, -1, int)


    @property
    def SVN_VERSION(self):
        """Current SVN version in the package running now."""
        svn_variable = 'SVN_REVISION'
        if svn_variable in os.environ:
            return os.environ[svn_variable]

        try:
            with open(os.path.join(self.BIN_FOLDER, 'tvb.version'), 'r') as version_file:
                return self._parse_svn_version(version_file.read())
        except Exception:
            pass

        try:
            _proc = Popen(["svnversion", "."], stdout=PIPE)
            return self._parse_svn_version(_proc.communicate()[0])
        except Exception:
            pass

        try:
            proc = Popen(['git', 'rev-parse', 'HEAD'], stdout=PIPE)
            return proc.stdout.read().strip()
        except Exception:
            pass

        raise ValueError('cannot determine svn version')


    @staticmethod
    def _parse_svn_version(version_string):
        if ':' in version_string:
            version_string = version_string.split(':')[1]

        number = ''.join([ch for ch in version_string if ch.isdigit()])
        return int(number)



class ClusterSettings(object):
    """
    Cluster related settings.
    """

    SCHEDULE_COMMAND = 'oarsub -p "host>\'n02\' AND host>\'n02\'" -l walltime=%s -q tvb ' \
                       '-S "/home/tvbadmin/clusterLauncher %s %s"'
    STOP_COMMAND = 'oardel %s'

    #Specify if the current process is executing an operation (via clusterLauncher)
    IN_OPERATION_EXECUTION_PROCESS = False

    _CACHED_IS_RUNNING_ON_CLUSTER = None
    _CACHED_NODE_NAME = None


    def __init__(self, manager):
        self.IS_DEPLOY = manager.get_attribute(stored.KEY_CLUSTER, False, eval)


    @property
    def IS_RUNNING_ON_CLUSTER_NODE(self):
        """
        Returns True if current execution happens on cluster node.
        Even when IS_DEPLOY is True, this call will return False for the web machine.
        """
        if self._CACHED_IS_RUNNING_ON_CLUSTER is None:
            self._CACHED_IS_RUNNING_ON_CLUSTER = self.CLUSTER_NODE_NAME is not None

        return self._CACHED_IS_RUNNING_ON_CLUSTER


    @property
    def CLUSTER_NODE_NAME(self):
        """
        :return the name of the cluster on which TVB code is executed.
            If code is executed on a normal machine (not cluster node) returns None
        """
        # Check if the name wasn't computed before.
        if self._CACHED_NODE_NAME is None:
            # Read env variable which contains path the the file containing node name
            env_oar_nodefile = os.getenv('OAR_NODEFILE')
            if env_oar_nodefile is not None and len(env_oar_nodefile) > 0:
                # Read node name from file
                with open(env_oar_nodefile, 'r') as f:
                    node_name = f.read()

                if node_name is not None and len(node_name.strip()) > 0:
                    self._CACHED_NODE_NAME = node_name.strip()
                    return self._CACHED_NODE_NAME
        else:
            return self._CACHED_NODE_NAME

        return None



class WebSettings(object):
    """
    Web related specifications
    """

    ENABLED = False
    LOCALHOST = "127.0.0.1"
    RENDER_HTML = True
    VISUALIZERS_ROOT = "tvb.interfaces.web.templates.genshi.visualizers"
    VISUALIZERS_URL_PREFIX = "/flow/read_datatype_attribute/"
    MPLH5_Server_Thread = None  # This is going to be set at init-time, by MPLH5 backend


    def __init__(self, manager, enabled):

        self.ENABLED = enabled
        self.admin = WebAdminSettings(manager)

        self.CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if enabled:
            try:
                import tvb.interfaces
                self.CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(tvb.interfaces.__file__)))
            except ImportError:
                pass
        else:
            self.VISUALIZERS_URL_PREFIX = ""

        self.SERVER_PORT = manager.get_attribute(stored.KEY_PORT, 8080, int)
        self.MPLH5_SERVER_PORT = manager.get_attribute(stored.KEY_PORT_MPLH5, 9000, int)

        # Compute reference towards the current web application, valid FROM localhost
        server_IP = manager.get_attribute(stored.KEY_IP, self.LOCALHOST)
        self.BASE_LOCAL_URL = "http://%s:%s/" % (server_IP, str(self.SERVER_PORT))

        # Compute PUBLIC reference towards the current web application, valid FROM outside
        self.BASE_URL = manager.get_attribute(stored.KEY_URL_WEB, self.BASE_LOCAL_URL)

        # URL for accessing the Matplotlib HTML5 backend
        default = "ws://%s:%s/" % (server_IP, str(self.MPLH5_SERVER_PORT))
        self.MPLH5_SERVER_URL = manager.get_attribute(stored.KEY_URL_MPLH5, default)

        # URL for reading current available version information.
        default = "http://www.thevirtualbrain.org/tvb/zwei/action/serialize-version?version=1&type=json"
        self.URL_TVB_VERSION = manager.get_attribute(stored.KEY_URL_VERSION, default)

        self.TEMPLATE_ROOT = os.path.join(self.CURRENT_DIR, 'interfaces', 'web', 'templates', 'genshi')
        self.CHERRYPY_CONFIGURATION = {'global': {'server.socket_host': '0.0.0.0',
                                                  'server.socket_port': self.SERVER_PORT,
                                                  'server.thread_pool': 20,
                                                  'engine.autoreload_on': False,
                                                  'server.max_request_body_size': 1932735283  # 1.8 GB
                                                  },
                                       '/': {'tools.encode.on': True,
                                             'tools.encode.encoding': 'utf-8',
                                             'tools.decode.on': True,
                                             'tools.gzip.on': True,
                                             'tools.sessions.on': True,
                                             'tools.sessions.storage_type': 'ram',
                                             'tools.sessions.timeout': 6000,  # 100 hours
                                             'response.timeout': 1000000,
                                             'tools.sessions.locking': 'explicit',
                                             'tools.upload.on': True,    # Tool to check upload content size
                                             'tools.cleanup.on': True    # Tool to clean up files on disk
                                             },
                                       '/static': {'tools.staticdir.root': self.CURRENT_DIR,
                                                   'tools.staticdir.on': True,
                                                   'tools.staticdir.dir': os.path.join('interfaces', 'web', 'static')
                                                   },
                                       '/statichelp': {'tools.staticdir.root': self.CURRENT_DIR,
                                                       'tools.staticdir.on': True,
                                                       'tools.staticdir.dir': os.path.join('interfaces', 'web',
                                                                                           'static', 'help')
                                                       },
                                       '/static_view': {'tools.staticdir.root': self.CURRENT_DIR,
                                                        'tools.staticdir.on': True,
                                                        'tools.staticdir.dir': os.path.join('interfaces', 'web',
                                                                                            'templates', 'genshi',
                                                                                            'visualizers'),
                                                        },
                                       '/schema': {'tools.staticdir.root': self.CURRENT_DIR,
                                                   'tools.staticdir.on': True,
                                                   'tools.staticdir.dir': os.path.join('core', 'schema'),
                                                   },
                                       }



class WebAdminSettings(object):
    """
    Setting related to the default users of web-tvb
    """

    SYSTEM_USER_NAME = 'TVB system'
    DEFAULT_ADMIN_EMAIL = 'jira.tvb@gmail.com'
    ADMINISTRATOR_BLANK_PWD = 'pass'


    def __init__(self, manager):
        # Give name for the Admin user, first created.
        self.ADMINISTRATOR_NAME = manager.get_attribute(stored.KEY_ADMIN_NAME, 'admin')

        # Admin's password used when creating first user (default is MD5 for 'pass')
        self.ADMINISTRATOR_PASSWORD = manager.get_attribute(stored.KEY_ADMIN_PWD, '1a1dc91c907325c69271ddf0c944bc72')

        # Admin's email used when creating first user
        self.ADMINISTRATOR_EMAIL = manager.get_attribute(stored.KEY_ADMIN_EMAIL, self.DEFAULT_ADMIN_EMAIL)



class DBSettings(object):

    # Overwrite number of connections to the DB.
    # Otherwise might reach PostgreSQL limit when launching multiple concurrent operations.
    # MAX_CONNECTION default value will be used for WEB
    # When launched on cluster, the MAX_ASYNC_CONNECTIONS overwrites MAX_ONNECTIONS value
    MAX_CONNECTIONS = 20
    MAX_ASYNC_CONNECTIONS = 2

    # Nested transactions are not supported by all databases and not really necessary in TVB so far so
    # we don't support them yet. However when running tests we can use them to out advantage to rollback
    # any database changes between tests.
    ALLOW_NESTED_TRANSACTIONS = False

    def __init__(self, manager, default_storage, current_storage):

        # A dictionary with accepted db's and their default URLS
        default_pg = 'postgresql+psycopg2://postgres:root@127.0.0.1:5432/tvb?user=postgres&password=postgres'
        default_lite = 'sqlite:///' + os.path.join(default_storage, 'tvb-database.db')
        self.ACEEPTED_DBS = {'postgres': manager.get_attribute(stored.KEY_DB_URL, default_pg),
                             'sqlite': manager.get_attribute(stored.KEY_DB_URL, default_lite)}

        # Currently selected database (must be a key in ACCEPTED_DBS)
        self.SELECTED_DB = manager.get_attribute(stored.KEY_SELECTED_DB, 'sqlite')

        # Used DB url: IP,PORT. The DB  needs to be created in advance.
        default_lite = 'sqlite:///' + os.path.join(current_storage, "tvb-database.db")
        self.DB_URL = manager.get_attribute(stored.KEY_DB_URL, default_lite)

        # Upgrade/Downgrade repository
        self.DB_VERSIONING_REPO = os.path.join(current_storage, 'db_repo')




class BaseSettingsProfile(object):

    TVB_CONFIG_FILE = os.path.expanduser(os.path.join("~", '.tvb.configuration'))

    DEFAULT_STORAGE = os.path.expanduser(os.path.join('~', 'TVB' + os.sep))
    FIRST_RUN_STORAGE = os.path.expanduser(os.path.join('~', '.tvb-temp'))

    LOGGER_CONFIG_FILE_NAME = "logger_config.conf"

    # Access rights for TVB generated files/folders.
    ACCESS_MODE_TVB_FILES = 0744

    ## Number used for estimation of TVB used storage space
    MAGIC_NUMBER = 9


    def __init__(self, web_enabled=True):

        self.manager = stored.SettingsManager(self.TVB_CONFIG_FILE)

        ## Actual storage of all TVB related files
        self.TVB_STORAGE = self.manager.get_attribute(stored.KEY_STORAGE, self.FIRST_RUN_STORAGE, unicode)
        self.TVB_LOG_FOLDER = os.path.join(self.TVB_STORAGE, "logs")
        self.TVB_TEMP_FOLDER = os.path.join(self.TVB_STORAGE, "TEMP")
        self.TVB_PATH = self.manager.get_attribute(stored.KEY_TVB_PATH, '')
        self.EXTERNALS_FOLDER_PARENT = os.path.dirname(self.BIN_FOLDER)

        self.env = Environment()
        self.cluster = ClusterSettings(self.manager)
        self.web = WebSettings(self.manager, web_enabled)
        self.db = DBSettings(self.manager, self.DEFAULT_STORAGE, self.TVB_STORAGE)
        self.version = VersionSettings(self.manager, self.BIN_FOLDER)

        #The path to the matlab executable (if existent). Otherwise just return an empty string.
        value = self.manager.get_attribute(stored.KEY_MATLAB_EXECUTABLE, '', str) or ''
        if value == 'None':
            value = ''
        self.MATLAB_EXECUTABLE = value

        # Maximum number of vertices acceptable o be part of a surface at import time.
        self.MAX_SURFACE_VERTICES_NUMBER = self.manager.get_attribute(stored.KEY_MAX_NR_SURFACE_VERTEX, 300000, int)
        # Max number of ops that can be scheduled from UI in a PSE. To be correlated with the oarsub limitations
        self.MAX_RANGE_NUMBER = self.manager.get_attribute(stored.KEY_MAX_RANGE_NR, 2000, int)
        # Max number of threads in the pool of ops running in parallel. TO be correlated with CPU cores
        self.MAX_THREADS_NUMBER = self.manager.get_attribute(stored.KEY_MAX_THREAD_NR, 4, int)
        #The maximum disk space that can be used by one single user, in KB.
        self.MAX_DISK_SPACE = self.manager.get_attribute(stored.KEY_MAX_DISK_SPACE_USR, 5 * 1024 * 1024, int)

        ## Configure Traits
        self.TRAITS_CONFIGURATION = EnhancedDictionary()
        self.TRAITS_CONFIGURATION.interface_method_name = 'interface'
        self.TRAITS_CONFIGURATION.use_storage = True


    @property
    def BIN_FOLDER(self):
        """
        Return path towards tvb_bin location. It will be used in some environment for determining the starting point
        """
        try:
            import tvb_bin
            return os.path.dirname(os.path.abspath(tvb_bin.__file__))
        except ImportError:
            return "."


    @property
    def PYTHON_EXE_NAME(self):
        """
        Returns the name of the python executable depending on the specific OS
        """
        if self.env.is_windows():
            return 'python.exe'
        else:
            return 'python'


    @property
    def PYTHON_PATH(self):
        """
        Get Python path, based on current environment.
        """
        exe_name = self.PYTHON_EXE_NAME
        if self.env.is_development():
            python_path = 'python'
        elif self.env.is_windows_deployment() or self.env.is_linux_deployment():
            python_path = os.path.join(os.path.dirname(self.BIN_FOLDER), 'exe', exe_name)
        elif self.env.is_mac_deployment():
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(self.BIN_FOLDER))))
            python_path = os.path.join(root_dir, 'MacOS', exe_name)
        else:
            python_path = 'python'

        try:
            # check if file actually exists
            os.stat(python_path)
            return python_path
        except:
            # otherwise best guess is the current interpreter!
            return sys.executable


    def prepare_for_operation_mode(self):
        """
        Overwrite PostgreSQL number of connections when executed in the context of a node.
        """
        self.db.MAX_CONNECTIONS = self.db.MAX_ASYNC_CONNECTIONS
        self.cluster.IN_OPERATION_EXECUTION_PROCESS = True


    def initialize_profile(self):
        """
        Make sure tvb folders are created.
        """
        if not os.path.exists(self.TVB_LOG_FOLDER):
            os.makedirs(self.TVB_LOG_FOLDER)

        if not os.path.exists(self.TVB_TEMP_FOLDER):
            os.makedirs(self.TVB_TEMP_FOLDER)

        if not os.path.exists(self.TVB_STORAGE):
            os.makedirs(self.TVB_STORAGE)



class LibrarySettingsProfile(BaseSettingsProfile):
    """
    Profile used when scientifical library is used without storage and without web UI.
    """

    TVB_STORAGE = os.path.expanduser(os.path.join("~", "TVB" + os.sep))
    LOGGER_CONFIG_FILE_NAME = "library_logger.conf"


    def __init__(self):

        super(LibrarySettingsProfile, self).__init__(False)

        ## Configure Traits
        self.TRAITS_CONFIGURATION = EnhancedDictionary()
        self.TRAITS_CONFIGURATION.interface_method_name = 'interface'
        self.TRAITS_CONFIGURATION.use_storage = False


    def initialize_profile(self):
        """
        Make sure some warning are thrown when trying to import from framework.
        """
        super(LibrarySettingsProfile, self).initialize_profile()
        sys.meta_path.append(LibraryModulesFinder())


class TestLibrarySettingsProfile(LibrarySettingsProfile):
    """
    Profile for library unit-tests.
    """

    LOGGER_CONFIG_FILE_NAME = "library_logger_test.conf"