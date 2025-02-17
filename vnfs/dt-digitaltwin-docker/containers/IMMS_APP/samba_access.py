#!/bin/bash
#  Copyright (c) 2018 5GTANGO, Weidmüller, Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, 5GTANGO, Weidmüller, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.5gtango.eu).

# code from https://pysmb.readthedocs.io/en/latest/api/smb_SMBConnection.html
import os
import time
import datetime
import tempfile
from pathlib import Path
from smb.SMBConnection import SMBConnection
from smb.smb_structs import OperationFailure


class SambaAccess:
    def __init__(self, smb_host, smb_share="guest", local_dir=Path("../em63_share")):
        self.smb_host = smb_host
        self.smb_share = smb_share
        self.local_dir = local_dir

    def samba_connect(self):
        """Connect to Samba host. Block and retry forever if connection times out."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # username, password, my_name, remote_name seem to not matter when creating the connection; only the host IP
        conn = SMBConnection("guest", "", "", "")
        
        print("\nConnecting to SMB host {} at time {}".format(self.smb_host, timestamp), flush=True)
        try:
            conn.connect(self.smb_host, 139, timeout=10)
        except: 
            print("Connection timed out. Retry in 5s")
            time.sleep(5)
            return self.samba_connect()
 
        return conn 
        
    def print_filenames(self):
        """Print name of all files and directories in the Samba share."""
        conn = self.samba_connect()
        print("Listing files and dirs in Samba share:", flush=True)
        file_list = conn.listPath(self.smb_share, "")
        for f in file_list:
            print(f.filename, flush=True)
            
    def get_file(self, filename, return_content=False):
        """
        Retrieve and saves specified file from Samba share locally. 
        Return path to downloaded file (default). Or file contents (if return_content=True).
        """
        conn = self.samba_connect()
        file_path = os.path.join(self.local_dir, filename)
        print("Downloading {} from the Samba share to {}".format(filename, file_path), flush=True)
        file_obj = open(file_path, 'wb')
        file_attr, filesize = conn.retrieveFile(self.smb_share, filename, file_obj)
        file_obj.close()
        
        if return_content:
            with open(file_path, 'r') as f:
                return f.read()
        return file_path

    def save_file(self, filename, file_path, overwrite=True):
        """Save the local file at file_path to the Samba share with the specified name. Return the bytes written."""
        conn = self.samba_connect()
        uploaded_bytes = 0
        print("Saving local file {} to Samba share to {}".format(file_path, filename), flush=True)
        try:
            with open(file_path, 'rb') as f:
                uploaded_bytes = conn.storeFile(self.smb_share, filename, f)
        except OperationFailure:
            if overwrite:
                print("File exists already, overwriting...", flush=True)
                self.delete_file(filename)
                return self.save_file(filename, file_path)
            else:
                print("File exists already, NOT overwriting...", flush=True)
        return uploaded_bytes

    def write_file(self, filename, text):
        """Write the specified text to the file."""
        print("Writing to file {}: {}".format(filename, text), flush=True)
        with open(filename, 'w') as f:
            f.write(text)
        self.save_file(filename, filename, overwrite=True)
        
    def delete_file(self, filename):
        """Delete files in the Samba share matching the filename."""
        conn = self.samba_connect()
        print("Deleting files matching {} from the Samba share".format(filename), flush=True)
        try:
            conn.deleteFiles(self.smb_share, filename)
        except OperationFailure as of:
            print("Error deleting {}. Does the file exist?".format(filename))

    def exists_file(self, filename):
        """Return if the file exists in the Samba share"""
        conn = self.samba_connect()
        print("Checking if file {} exists".format(filename))
        exists = False
        try:
            attr = conn.getAttributes(self.smb_share, filename)
            exists = attr is not None
        finally:
            print("{} exists: {}".format(filename, exists))
            return exists

        
if __name__ == "__main__":
    # some code to test and experiment: specify floating IP of NS2 MDC
    smb = SambaAccess("172.31.13.160")
    # smb.print_filenames()
    # smb.exists_file('blablala')
    # smb.delete_file('remote_test.txt')
    # print(smb.save_file('remote_test.txt', 'test.txt'))
    # print(smb.save_file('remote_test.txt', 'test.txt'))
    smb.write_file('remote_test2.txt', 'works really well!')
    print(smb.get_file("remote_test2.txt", return_content=True))
    # smb.print_filenames()

