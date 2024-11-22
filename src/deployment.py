import logging
import os
from pathlib import Path
import subprocess

from Utilities_Python import misc

CONFIG_FILE = os.path.join(Path(__file__).parents[1], 'config.json')


class Project:
    """ A class structure for a project and its related methods """
    def __init__(self, name: str, properties: dict):
        self.name = name
        self.directory = properties['directory']
        self.branch = properties['branch']
        self.language = properties['language']
        self.publish_dir = properties['publishLocation']
        self.do_build = self._do_build()
        self.project_extension = self._project_extension()
        self.deploy_file = 'deploy.txt'

    def _do_build(self) -> bool:
        """ Determine if the project language supports builds """
        do_build = True
        match self.language.upper():
            case 'PYTHON':
                do_build = False
            case 'VB':
                do_build = True
            case 'C#':
                do_build = True
            case _:
                do_build = False

        if do_build:
            if not os.path.exists(self.publish_dir):
                logging.warning(F"Project '{self.name}' has an invalid publish directory '{self.publish_dir}'")
                do_build = False

        return do_build

    def _project_extension(self) -> str:
        """ Returns the Visual Studio project extension for the language """
        match self.language:
            case 'Python':
                return 'pyproj'
            case 'VB':
                return 'vbproj'
            case 'C#':
                return 'csproj'
            case _:
                raise NotImplementedError(f'Project language {self.language} not supported')

    def _pull(self) -> bool:
        """ Pull the specified Git branch """
        try:
            os.chdir(self.directory)
            _ = subprocess.run(f'git pull origin {self.branch}', check=True, shell=True, text=True)
            return True
        except Exception as e:
            logging.error(f'Git pull failed: {type(e).__name__}')
            return False

    def _build(self) -> bool:
        """ Build a project, currently only supports .NET """
        try:
            os.chdir(self.directory)
            _ = subprocess.run('dotnet build -c Release', check=True, shell=True, text=True)
            return True
        except Exception as e:
            logging.error(f'Build failed: {type(e).__name__}')
            return False

    def _publish(self) -> bool:
        """ Publish a project, currently only supports .NET """
        try:
            os.chdir(self.directory)
            _ = subprocess.run(
                f'dotnet publish {self.name}.{self.project_extension} -c Release --no-build -o "{self.publish_dir}"',
                check=True,
                shell=True,
                text=True
            )
            return True
        except Exception as e:
            logging.error(f'Publish failed: {type(e).__name__}')
            return False

    def deploy_application(self):
        """ Perform an application deployment """
        # if the trigger file exists, proceed with deployment
        deployment_file = os.path.join(self.directory, self.deploy_file)
        if os.path.exists(deployment_file):
            logging.info(f"Deploying application '{self.name}'")
            deployed = False
            if self._pull():
                if not self.do_build:
                    deployed = True
                else:
                    if self._build():
                        if self._publish():
                            deployed = True

            # remove the deployment trigger file
            os.remove(deployment_file)

            if deployed:
                logging.info(f"Project '{self.name}' deployment succeeded")
            else:
                logging.warning(f"Project '{self.name}' deployment failed")


def main():
    script_name = Path(__file__).stem
    _ = misc.initiate_logging(script_name, CONFIG_FILE)

    projects = misc.get_config('projects', CONFIG_FILE)
    for p in projects:
        project = Project(p, projects[p])
        project.deploy_application()


if __name__ == '__main__':
    main()
