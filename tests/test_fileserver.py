import os
from pathlib import Path
from sys import path
from ftplib import error_perm
from unittest.mock import MagicMock

import pytest

path.append(str(Path(__file__).resolve().parents[1]))
from fileserver import FileServer


@pytest.fixture
def fileserver(mocker):
    """Return a FileServer instance with a mocked FTP client."""
    ftp = MagicMock()
    mocker.patch("fileserver.FTP", return_value=ftp)
    server = FileServer("ftp.example.com", "user", "password")
    return server, ftp


def test_upload_file_succeeds_when_size_check_is_unsupported(tmp_path, fileserver):
    """A missing SIZE command should not turn a successful upload into a failure."""
    server, ftp = fileserver
    local_file = tmp_path / "image.jpg"
    local_file.write_bytes(b"test-image-bytes")

    ftp.storbinary.return_value = "226 Transfer complete"
    ftp.size.side_effect = error_perm("550 SIZE not allowed")

    server.upload_file(local_file.name, f"{tmp_path}{os.sep}", delete_after_upload=True)

    ftp.storbinary.assert_called_once()
    ftp.size.assert_called_once_with(local_file.name)
    assert not local_file.exists()


def test_upload_file_fails_when_verified_size_differs(tmp_path, fileserver):
    """A real size mismatch should keep the local file in place."""
    server, ftp = fileserver
    local_file = tmp_path / "image.jpg"
    local_file.write_bytes(b"test-image-bytes")

    ftp.storbinary.return_value = "226 Transfer complete"
    ftp.size.return_value = 1

    server.upload_file(local_file.name, f"{tmp_path}{os.sep}", delete_after_upload=True)

    ftp.storbinary.assert_called_once()
    ftp.size.assert_called_once_with(local_file.name)
    assert local_file.exists()
