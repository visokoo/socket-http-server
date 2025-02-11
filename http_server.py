import socket
import sys
import traceback
import os
import mimetypes
import logging


def init_logging():
    """ Setting up the logger
        Logging to a file called http_server.log with anything INFO and above
    """
    logger = logging.getLogger(__name__)
    log_format = (
        "%(asctime)s %(filename)s:%(lineno)-3d %(levelname)s %(message)s")
    log_file = 'http_server.log'
    formatter = logging.Formatter(log_format)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)

    return logger


LOGGER = init_logging()


def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->

        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """
    return b"\r\n".join([
        b"HTTP/1.1 200 OK",
        b"Content-Type: " + mimetype,
        b"",
        body,
    ])


def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""
    return b"\r\n".join([
        b"HTTP/1.1 405 Method Not Allowed",
        b"",
        b"You can't do that on this server!"
    ])


def response_not_found():
    """Returns a 404 Not Found response"""
    return b"\r\n".join([
        b"HTTP/1.1 404 Page Not Found",
        b"",
        b"Sorry, the page that you're requesting does not exist."
    ])


def parse_request(request):
    """
    Given the content of an HTTP request, returns the path of that request.

    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.
    """
    method, path, version = request.split("\r\n")[0].split(" ")
    print(method, path, version)
    if method != "GET":
        raise NotImplementedError
    return path


def response_path(path):
    """
    This method should return appropriate content and a mime type.

    If the requested path is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the path is a file, it should return the contents of that file
    and its correct mimetype.

    If the path does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        response_path('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        response_path('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        response_path('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        response_path('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """
    directory = os.path.dirname(os.path.abspath(__file__)) + "/webroot"
    full_path = directory + path
    LOGGER.info("Path: %s", path)
    LOGGER.info("Full path: %s", full_path)
    if not os.path.exists(full_path):
        LOGGER.info("Path: %s not found in dir: %s", path, directory)
        raise NameError

    if os.path.isdir(full_path):
        mime_type = b"text/plain"
        content = "\r\n".join(os.listdir(full_path)).encode("utf-8")
    else:
        mime_type = mimetypes.guess_type(full_path)[0].encode("utf-8")
        content = ""
        LOGGER.info("mime-type: %s", mime_type)
        with open(full_path, "rb") as file:
            content = file.read()

    return content, mime_type


def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)

                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')

                    if '\r\n\r\n' in request:
                        break

                print("Request received:\n{}\n\n".format(request))

                try:
                    path = parse_request(request)
                    content, mimetype = response_path(path)

                    response = response_ok(
                        body=content,
                        mimetype=mimetype
                    )
                except NotImplementedError:
                    response = response_method_not_allowed()
                except NameError:
                    response = response_not_found()

                conn.sendall(response)
            except:
                traceback.print_exc()
            finally:
                conn.close()

    except KeyboardInterrupt:
        sock.close()
        return
    except:
        traceback.print_exc()


if __name__ == '__main__':
    server()
    sys.exit(0)
