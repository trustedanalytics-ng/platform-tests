#
# Copyright (c) 2016 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""This module is responsible for preparing applications that will be later
pushed to TAP.

Basically you have to call the initializer with the path to the application:
p_a = PrepApp("path/to/applications")

After initialization you can update the manifest with required params:
manifest_path = p_a.update_manifest({"par1" : "val1", "par2" : "val2"})

If you don't provide a "name" in the parameters, then one will be generated for
you. You can retrieve it later:
name = p_a.app_name

Also, "instances" will be set to 1, if not provided:
instances = p_a.instances

If you want, you can also compress the app:
gzipped_file = p_a.package_app(context)

You have to pass the context, as the gzipped file will be later removed.
"""
import json
import os
import random
import tarfile

from modules import test_names

class PrepApp():
    """Prepares application, by packing in tar.gz format. It allows also
    to update manifest. After packing the application, it is added to the context
    so at the end of the test those gzipped applications can be removed from
    hard drive.
    """
    MANIFEST_NAME = "manifest.json"
    RUN_SH_NAME = "run.sh"
    def __init__(self, app_path=str):
        """Initializer

        Args:
            app_path: Directory containing the application
        """
        self.app_path = app_path
        self.tar_name = None
        self.app_name = None
        self.instances = 0

    def package_app(self, context) -> str:
        """Packages the application to the tar.gz format

        Args:
            context: When application is no longer needed, context
                    will run the cleanup method

        Returns:
            Path to the gzipped application
        """
        self.tar_name = os.path.join(self.app_path, str(random.random()) + ".tar.gz")
        tar_file = tarfile.open(self.tar_name, "w:gz")
        tar_file.add(self.app_path, arcname="")

        tar_file.close()

        context.test_objects.append(self)

        return self.tar_name

    def update_manifest(self, *, params: dict):
        """Updates the manifest with provided params. If the manifest file
        does not exist, it is created and filled with parameters provided.

        It also checks if the application name is provided. If not, it will be
        automatically generated.

        If instances aren't passed, they are set to 1

        Args:
            params: key->value that will update the manifest

        Returns:
            Path to the manifest file
        """
        # Include basic params
        if params.get("name", None) is None:
            params["name"] = test_names.generate_test_object_name(separator="")

        self.app_name = params["name"]

        if params.get("instances", None) is None:
            params["instances"] = 1

        self.instances = params["instances"]

        # Look for the manifest
        if os.path.isfile(self.app_path):
            manifest_dir = os.path.dirname(self.app_path)
        else:
            manifest_dir = self.app_path

        manifest_path = os.path.join(manifest_dir, self.MANIFEST_NAME)

        # Open the manifest and update it's params
        try:
            with open(manifest_path, 'r') as file:
                manifest = json.loads(file.read())
                for key, val in params.items():
                    manifest[key] = val
        except FileNotFoundError:
            # That is okay
            manifest = params

        # Save the manifest
        with open(manifest_path, 'w') as file:
            file.write(json.dumps(manifest))

        return manifest_path


    @classmethod
    def set_run_sh_access(cls, *, app_path):
        """Applies proper right to run.sh

        Args:
            app_path: Path to the application
        """

        if os.path.isfile(app_path):
            run_sh_dir = os.path.dirname(app_path)
        else:
            run_sh_dir = app_path

        run_sh_path = os.path.join(run_sh_dir, cls.RUN_SH_NAME)
        if os.path.isfile(run_sh_path):
            os.chmod(run_sh_path, 0o777)


    def cleanup(self):
        """Removes the previously compressed file"""
        if self.tar_name != None:
            print("Removing file: " + self.tar_name)
            os.remove(self.tar_name)
