""" The fileserver module is used to connect to a file server and perform operations such as downloading and uploading files. """
from ftplib import FTP
from io import BytesIO
from datetime import datetime
from time import sleep
import logging

class FileServer:
    """A class to connect to a file server and perform operations such as downloading and uploading files."""
    MAX_RETRIES = 5
    RETRY_INTERVAL = 5  # Seconds

    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize and connect to the file server."""
        self.ftp = None
        self.CONNECTED_TO_FTP = self.connect_to_server(host, username, password)

    def connect_to_server(self, host: str, username: str, password: str) -> bool:
        """Connect to the file server with retries."""

        for attempt in range(self.MAX_RETRIES):
            try:
                self.ftp = FTP(host, username, password, timeout=5)
                return True
            except Exception as e:
                if attempt > 1:
                    logging.warning("Could not connect to fileserver: %s, attempt %s/%s failed.", str(e), attempt+1, self.MAX_RETRIES)
                else:
                    logging.info("Could not connect to fileserver: %s, attempt %s/%s failed.", str(e), attempt+1, self.MAX_RETRIES)
                sleep(self.RETRY_INTERVAL) # Wait and try again

        logging.error("Failed to connect to the file server after maximum retries.")
        return False

    def connected(self) -> bool:
        """Check if the file server is connected"""
        return self.CONNECTED_TO_FTP

    def change_directory(self, directory: str, create: bool = False) -> None:
        """Change the current directory on the file server"""
        try:
            directory_list = self.list_files()

            if create and directory not in directory_list:
                self.ftp.mkd(directory)

            self.ftp.cwd(directory)

        except Exception as e:
            logging.warning("Could not change directory on file server: %s", str(e))

    def download_file(self, filename: str, local_file_path: str = "") -> None:
        """Download a file from the file server and save it locally."""
        local_path = f"{local_file_path}{filename}"
        try:
            with open(local_path, 'wb') as local_file:
                self.ftp.retrbinary(f"RETR {filename}", local_file.write)
            logging.info("Successfully downloaded %s to %s", filename, local_path)
        except Exception as e:
            logging.error("Failed to download file: %s", str(e))

    def upload_file(self, filename: str, local_file_path: str = "") -> None:
        """Upload a file to the file server."""
        local_path = f"{local_file_path}{filename}"
        try:
            with open(local_path, 'rb') as local_file:
                self.ftp.storbinary(f"STOR {filename}", local_file)
            logging.info("Successfully uploaded %s", local_file)
        except Exception as e:
            logging.error("Failed to upload file: %s", str(e))

    def append_file(self, filename: str, local_file_path: str = "") -> None:
        """Append a file to the file server."""
        local_path = f"{local_file_path}{filename}"
        try:
            with open(local_path, 'rb') as local_file:
                self.append_file_from_bytes(filename, BytesIO(local_file.read()))
        except Exception as e:
            logging.error("Failed to append file: %s", str(e))

    def append_file_from_bytes(self, filename: str, file_data: BytesIO) -> None:
        """Append a file to the file server."""
        try:
            self.ftp.storbinary(f"APPE {filename}", file_data)
            logging.info("Successfully appended data to %s", filename)
        except Exception as e:
            logging.error("Failed to append data: %s", str(e))

    def get_file_as_bytes(self, filename: str) -> BytesIO:
        """Retrieve a file from the file server as a BytesIO object."""
        file_data = BytesIO()
        try:
            self.ftp.retrbinary(f"RETR {filename}", file_data.write)
            return file_data
        except Exception as e:
            logging.error(f"Failed to retrieve file: {e}")
            return BytesIO()

    def list_files(self) -> list:
        """List files in the current or specified directory"""
        try:
            return self.ftp.nlst()
        except Exception as e:
            logging.error("Failed to list files: %s", str(e))
            return []

    def get_file_last_modified_date(self, filename: str) -> datetime:
        """Get the last modification date of a file on the file server."""
        try:
            response = self.ftp.sendcmd(f"MDTM {filename}")
            return datetime.strptime(response[4:], '%Y%m%d%H%M%S') # Convert to datetime
        except Exception as e:
            logging.error("Failed to get file last modified date: %s", str(e))
            return datetime.now()

    def quit(self) -> None:
        """Close the FTP connection."""
        try:
            self.ftp.quit()
            logging.info("File server connection closed.")
        except Exception as e:
            logging.error("Failed to close file server connection: %s", str(e))
