import socket, sys, pickle
from datetime import datetime

# TODO: change BUFFER_SIZE in send_commands_to_server to the size of the message
# global BUFFER_SIZE
# BUFFER_SIZE= 1024

# ports are 43500 to 43999
class UDPClient:
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.socket_gen = None

	def print_log(self, msg):
		# Log time for a message
		log_T = datetime.now().strftime('%Y/%m/%d; %H:%M:%S')
		print(f'[{log_T}] {msg}')

	def create_socket(self):
		# Create socket
		try:
			self.socket_gen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.print_log('Socket creation successful!')
			self.print_log(f'Client hostname is: {socket.gethostname()} and ip address is: {socket.gethostbyname(socket.gethostname())}')
		except socket.error as msg:
			self.print_log(f'Socket creation failed. Error Code: {str(msg[0])} Message {msg[1]}')
			sys.exit()

	def send_commands_to_server(self):
		try:
			while 1:
				message = input('Enter command to send: ')
				self.print_log(f'Client sends {message} to server')
				try:
					# check if length of message to server is equal to the length of the message inputted
					if(self.socket_gen.sendto(message.encode('utf-8'), (self.host, self.port)) == len(message)):
						# Receive data from server (data, addr)
						response, server_addr = self.socket_gen.recvfrom(4096)
						de_pickle = pickle.loads(response)
						self.print_log(f'Server replied: {de_pickle}')
				except socket.error as message:
					self.print_log(f'Error Code: {str(message[0])} | Message {message[1]}')
					sys.exit()
		except KeyboardInterrupt:
			self.close_socket()

	def close_socket(self):
		# Close socket
		self.print_log('Closing the socket')
		self.socket_gen.close()
		self.print_log('Socked closed')

def main():
	# get port and server_ip from command line
	argv = sys.argv[0:]
	try:
		# check if the 2nd argument is an ip address
		if(argv[1].count('.') == 3):
			server_ip = argv[1] # get server IP
		else:
			print('Usage: python3 Client.py <ipaddress> <port>')
			sys.exit()
		# convert port number to int
		port = int(argv[2])
		print(f'Arguments passed: server IP {server_ip} port(s) {port}')
	except:
		print('Usage: python3 Client.py <ipaddress> <port>')
		sys.exit()

	udp_client = UDPClient(server_ip, port)
	udp_client.create_socket()
	udp_client.send_commands_to_server()

if __name__ == '__main__':
	main()
