""" The fileserver module is used to connect to a file server and perform operations such as downloading and uploading files. """
from ftplib import FTP
from io import BytesIO
from datetime import datetime
from time import sleep
from os import remove
import logging

class FileServer:
    """A class to connect to a file server and perform operations such as downloading and uploading files."""
    
    def __init__(self, host: str, username: str, password: str) -> None:
        """Initialize and connect to the file server."""
        self.MAX_RETRIES = 5
        self.RETRY_INTERVAL = 5  # Seconds

        self.ftp = None
        self.connected_to_server = self.connect_to_server(host, username, password)

    def connect_to_server(self, host: str, username: str, password: str) -> bool:
        """Connect to the file server with retries."""

        for attempt in range(self.MAX_RETRIES):
            try:
                self.ftp = FTP(host, username, password, timeout=10)
                logging.info("Connected to file server.")
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
        return self.connected_to_server

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

    def upload_file(self, filename: str, local_file_path: str = "", delete_after_upload = False) -> None:
        """Upload a file to the file server."""
        local_path = f"{local_file_path}{filename}"
        try:
            with open(local_path, 'rb') as local_file:
                self.ftp.storbinary(f"STOR {filename}", local_file)
            logging.info("Successfully uploaded %s", local_file)

            if delete_after_upload:
                logging.info("Deleting local file: %s", local_path)
                remove(local_path)
        except Exception as e:
            logging.error("Failed to upload file: %s", str(e))

    def append_file(self, filename: str, local_file_path: str = "", delete_after_upload = False) -> None:
        """Append a file to the file server."""
        local_path = f"{local_file_path}{filename}"
        try:
            with open(local_path, 'rb') as local_file:
                self.append_file_from_bytes(filename, BytesIO(local_file.read()))

            if delete_after_upload:
                logging.info("Deleting local file: %s", local_path)
                remove(local_path)
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
            logging.error("Failed to retrieve file: %s", str(e))
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
        """Close the file server connection."""
        try:
            self.ftp.quit()
            logging.info("File server connection closed.")
        except Exception as e:
            logging.error("Failed to close file server connection: %s", str(e))


if __name__ == "__main__":

    HOST = "444024-1.web.fhgr.ch"
    USERNAME = "444024_1_1"
    PASSWORD = "e5tlZOhT=EoB"

    logging.basicConfig(level=logging.INFO)
    file_server = FileServer(HOST, USERNAME, PASSWORD)

    print(f"Connected to file server: {file_server.connected()}")

    file_server.change_directory("private")


    import yaml
    import random

    generated_data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'next_startup_time': datetime.now().timestamp() + random.randint(60, 3600),  # Random future timestamp
        'battery_voltage': round(random.uniform(3.0, 4.2), 2),  # Example voltage range
        'internal_voltage': round(random.uniform(1.0, 1.5), 2),
        'internal_current': round(random.uniform(0.0, 5.0), 2),
        'temperature': round(random.uniform(-20, 40), 1),  # Example temperature range
        'signal_quality': random.randint(0, 100),
        'latitude': round(random.uniform(-90, 90), 6),
        'longitude': round(random.uniform(-180, 180), 6),
        'height': round(random.uniform(0, 10000), 2)  # Example height in meters
    }

    # Append the new data to the YAML file in the file server with append_file_from_bytes
    byte_stream = BytesIO()
    yaml.safe_dump([generated_data], stream=byte_stream,  default_flow_style=False, encoding='utf-8')
    byte_stream.seek(0)  # Set the position to the beginning of the BytesIO object
    
    file_server.append_file_from_bytes("data.yaml", byte_stream)

    #     file_server.download_file("example.txt", "local/")
    #     file_server.upload_file("example.txt", "local/")
    #     file_server.quit()
    # else:
    #     logging.error("Could not connect to file server.")

    file_server.quit()
