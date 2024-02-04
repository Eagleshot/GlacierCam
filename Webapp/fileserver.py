# ftp_operations.py
from ftplib import FTP
from io import BytesIO
from datetime import datetime
from pytz import timezone

class fileServer:
    def __init__(self, host, username, password):
        self.ftp = FTP(host, username, password)

    def change_directory(self, directory):
        '''Change the current directory on the file server'''
        self.ftp.cwd(directory)

    # @st.cache_data(show_spinner=False, ttl=1)
    def download_file(self, filename: str) -> None:
        '''Download a file from the file server and save it to the disk.'''
        with open(filename, 'wb') as local_file:
            self.ftp.retrbinary(f"RETR {filename}", local_file.write)

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
        '''Get the last modification date of a file on the fileserver.'''
        last_modified = self.ftp.sendcmd(f"MDTM {filename}")
        last_modified = datetime.strptime(last_modified[4:], '%Y%m%d%H%M%S') # Convert to datetime
        last_modified = timezone.localize(last_modified) # Convert date to local timezone

        return last_modified

    def close(self):
        '''Close the FTP connection'''
        self.ftp.quit()
