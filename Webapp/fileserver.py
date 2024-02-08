# fileserver.py
from ftplib import FTP
from io import BytesIO
from datetime import datetime
from time import sleep
import logging
from pytz import timezone

class fileServer:
    def __init__(self, host: str, username: str, password: str) -> None:
        '''Connect to the file server'''

        MAX_RETRIES = 5
        self.CONNECTED_TO_FTP = False

        for i in range(MAX_RETRIES):
            try:
                self.ftp = FTP(host, timeout=5)
                self.ftp.login(user=username, passwd=password)
                self.CONNECTED_TO_FTP = True
                break
            except Exception as e:
                if i > 1:
                    logging.warning("Could not connect to FTP server: %s, attempt %s/%s failed - trying again in 5 seconds.", str(e), i+1, MAX_RETRIES)
                else:
                    logging.info("Could not connect to FTP server: %s, attempt %s/%s failed - trying again in 5 seconds.", str(e), i+1, MAX_RETRIES)

                sleep(5) # Wait 5 seconds and try again

    # TODO Create flag
    def change_directory(self, directory: str, create: bool = False):
        '''Change the current directory on the file server'''
        try:
            directory_list = self.list_files()

            if directory not in directory_list and create:
                self.ftp.mkd(directory)

            self.ftp.cwd(directory)

        except Exception as e:
            logging.warning("Could not change directory on FTP server: %s", str(e))


    # @st.cache_data(show_spinner=False, ttl=1)
    def download_file(self, filename: str) -> None:
        '''Download a file from the file server and save it to the disk.'''
        with open(filename, 'wb') as local_file:
            self.ftp.retrbinary(f"RETR {filename}", local_file.write)

    def upload_file(self, filename: str, directory: str = "") -> None:
        '''Upload a file to the file server.'''
        if directory:
            self.change_directory(directory)

        with open(filename, 'rb') as local_file:
            self.ftp.storbinary(f"STOR {filename}", local_file)

        if directory:
            self.change_directory("..")

    # @st.cache_data(show_spinner=False, ttl=3600)
    def get_image(self, filename: str) -> BytesIO: #TODO Make more general
        '''Get an file from the file server as a BytesIO object.'''
        image_data = BytesIO()
        self.ftp.cwd("save") # TODO Cleanup
        self.ftp.retrbinary(f"RETR {filename}", image_data.write)
        self.ftp.cwd("..") # TODO Cleanup

        return image_data

    def list_files(self, directory: str = "") -> list:
        '''List files in the current or specified directory'''
        if directory:
            self.change_directory(directory)
            files = self.ftp.nlst()
            self.change_directory("..")
            return files

        return self.ftp.nlst()

    def get_file_last_modified_date(self, filename: str, timezone: timezone) -> datetime:
        '''Get the last modification date of a file on the file server.'''
        last_modified = self.ftp.sendcmd(f"MDTM {filename}")
        last_modified = datetime.strptime(last_modified[4:], '%Y%m%d%H%M%S') # Convert to datetime
        last_modified = timezone.localize(last_modified) # Convert date to local timezone

        return last_modified

    def close(self) -> None:
        '''Close the file server connection'''
        self.ftp.quit()
