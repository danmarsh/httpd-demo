"""ebserver.py provides a simple socket server that responds to limited GET requests."""

__author__ = "Dan Marsh"

import socket
import os
import urllib

class Server(object):
	"""Class to listen for HTTP requests and return dir listings"""
	def __init__(self, host, port, root_path):
		self.host = host
		self.port = port
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.root_path = root_path
		
	def listen(self):
		"""Listen for incoming requests, process and respond."""
		
		self.socket.bind((self.host, self.port))
		self.socket.listen(1)
		print "Listening..."
		while 1:
			# loop for new connection
			self.connection, self.address = self.socket.accept()
			header_data = None
			received_data = ""
			while 1:
				# loop for request data
				data = self.connection.recv(1024)
				received_data += data
				if "\n\n" in received_data or "\r\n\r\n" in received_data:
					# hit the end of the request header,
					# skip to the processing since we only care about the header
					header_data = received_data
					break
				if not data:
					break
			if header_data:
				request = Request()
				request.processHeaders( header_data )
				response = self.getResponse( request )
				self.connection.send( response.getHTTPString( ) )
			self.connection.close()
			self.connection = None
	
	def getResponse( self, request ):
		"""Returns a Response for a Request object"""
		
		# attempts to clean up the path, may be insecure
		absolute_root_path = os.path.abspath(self.root_path)
		response = Response( absolute_path = os.path.join( absolute_root_path, "./" + request.path ) )
		response.absolute_path = os.path.normpath( response.absolute_path )
		
		# make sure we are still inside the root path and that the file exists
		if response.absolute_path.startswith( absolute_root_path ) and os.path.exists( response.absolute_path ):
			if os.path.isfile( response.absolute_path ):
				# read file and return with header
				response.code = 200
				response.payload = "<h1>file contents for %s</h1>" % response.absolute_path
				with open(response.absolute_path, 'r') as f:
					response.payload = f.read()
			else:
				# generate dir listing
				response.code = 200
				response.payload = "<h1>dir listing for %s</h1>" % response.absolute_path
				response.payload += "<div><a href=\"..\">..</a></div>"
				for file_name in os.listdir( response.absolute_path ):
					if not os.path.isfile( os.path.join( response.absolute_path, file_name) ):
						# add a trailing slash for dirs
						file_name += "/"
					response.payload += "<div><a href=\"%s\">%s</a></div>" % (urllib.quote(file_name), file_name)
		else:
			# can't find the file, return 404
			response.code = 404
			response.payload = "<h1>error 404: invalid path %s</h1>" % response.absolute_path
		
		return response
	
class Request(object):
	"""HTTP Client Request"""
	def __init__(self, path=None):
		self.path = path
	
	def processHeaders(self, header_data):
		"""Extracts the path from  GET request headers."""
		# extract the GET path and ignore everything else
		
		for line in header_data.splitlines():
			if line[:4] == "GET ":
				parts = line.split(" ")
				self.path = parts[1]

class Response(object):
	"""HTTP Server Response"""
	def __init__(self, absolute_path = None, header_dict = None, code = 200, payload = "" ):
		self.absolute_path = absolute_path
		self.header_dict = header_dict
		self.code = code
		self.payload = payload
		
	def getHTTPString( self ):
		"""Returns the HTTP formated response"""
		if self.code == 404:
			code_string = "Not Found"
		else:
			code_string = "OK"
		
		# hardcoded HTTP header and payload
		return "HTTP/1.1 %d %s\r\nContent-Length: %d\r\nContent-Type: text/html\r\n\r\n%s" %  ( self.code, code_string, len(self.payload), self.payload )

		
if __name__ == "__main__":
	server = Server( "127.0.0.1", 8000, "." )
	server.listen()
	
	