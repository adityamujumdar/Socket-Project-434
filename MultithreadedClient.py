# Aditya Mujumdar and Jendric Shawn Chan
# COmputer Netorking CSE 434 Fall 2020 Milestone 1

# Client application

import socket, sys, pickle, threading
from datetime import datetime

# TODO: change BUFFER_SIZE in server_communication to the size of the message
# global BUFFER_SIZE
# BUFFER_SIZE= 1024


# ports are 43500 to 43999
class UDPClient:
    def __init__(self, server_ip, destination_port):
        self.server_ip = ''
        # destination port is servers port its listening at
        self.destination_port = 43599
        # ss port is the source port where client is sending information from
        self.ss_port = None
        # port for peer communication
        self.pp_port_1 = None
        # port for peer communication
        self.pp_port_2 = None
        self.client_ip = None
        self.ring_id = 0
        self.clients = None
        self.ring_size = 0
        self.rc_ip = None # right clients IP
        self.rc_port = None # right client port
        self.compute_port = 0
        self.client_name = ''
        self.teardown_id = None
        self.teardown_name = None

        self.print_log('Creating Sockets...')
        # Create socket for pp_2 (right)
        try:
            self.socket_pp_2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socket_pp_2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error as msg:
            self.print_log('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
            sys.exit()

        # Create socket for pp_1 (left)
        try:
            self.socket_pp_1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socket_pp_1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except socket.error as msg:
            self.print_log('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
            sys.exit()

        # Create socket for ss (server)
        try:
            self.socket_ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socket_ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.print_log('Sockets created successfully!')
        except socket.error as msg:
            self.print_log('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
            sys.exit()


    def print_log(self, msg):
        # Log time for a message
        log_T = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        print(f'[{log_T}] {msg}')

    def setup_ring(self, depickled_data):
        # for register command
        if(type(depickled_data) is str and depickled_data == 'SUCCESS'):
            # SUCCESS from server at task
            self.print_log(f'SUCCESS')
        elif(type(depickled_data) is str and depickled_data == 'FAILURE'):
            # FAILURE from server at task
            self.print_log(f'FAILURE')
        elif(type(depickled_data) is tuple and depickled_data[0] == 'SUCCESS' and len(depickled_data) == 5):
            # start the O-ring setup
            print(f'Users in Ring from Ring Database: {depickled_data[3]}')
            self.ring_id, self.ring_size = depickled_data[1], depickled_data[2]
            index_pos = depickled_data[4]
            # sort the clients list according to user numbers
            #client_lst = tuple(sorted(depickled_data[3], key=lambda item: item[0]))
            # make a global list of clients to be used by other functions
            self.clients = depickled_data[3]
            client_lst = depickled_data[3]
            #right client information
            self.print_log(f'client_lst: {client_lst}')
            self.rc_ip = client_lst[index_pos][1]
            self.rc_port = int(client_lst[index_pos][3])
            index_pos+=1
            self.print_log('Sending o-ring-setup to right client...')
            self.manage_right_client(pickle.dumps(('o-ring-setup', client_lst, index_pos)))
        elif(type(depickled_data) is tuple and depickled_data[0] == 'o-ring-setup'):
            # setup of the ring.
            #client_lst = tuple(sorted(depickled_data[1], key=lambda item: item[0]))
            client_lst = depickled_data[1]
            index_pos = depickled_data[2]
            # client allocated leader
            if index_pos == 1:
                # self.print_log(f'client_lst before sending setup-complete: {client_lst}')
                # send the compute port (port of elected leader as setup-complete port variable)
                self.compute_port = (client_lst[0][2])
                self.client_name = client_lst[0][0]
                # self.print_log(f"TYPES are -> ring_id: {type(self.ring_id)}. client name: {type(self.client_name)}. compute port: {type(self.compute_port)}")
                self.print_log('Sending setup-complete to server')
                stpreply_msg = 'setup-complete ' + self.ring_id + ' ' + self.client_name + ' ' + self.compute_port
                self.socket_ss.sendto(stpreply_msg.encode('utf-8'), (self.server_ip, self.destination_port))
                resp, serv_add = self.socket_ss.recvfrom(4096)
                dpckl = pickle.loads(resp)
                self.print_log(f'Server response: {dpckl}')
                print('Enter command to send: ')
                self.server_communication()
            else:
                if index_pos == len(client_lst):
                    self.rc_ip = client_lst[0][1]
                    self.rc_port = int(client_lst[0][3])
                    index_pos = 1
                else:
                    self.rc_ip = client_lst[index_pos][1]
                    self.rc_port = int(client_lst[index_pos][3])
                    index_pos += 1

                self.manage_right_client(pickle.dumps(('o-ring-setup', client_lst, index_pos)))

        elif(type(depickled_data) is tuple and depickled_data[0] == 'FAILURE'  and len(depickled_data) == 5):
            # couldn't setup ring
            self.print_log(f'Code: FAILURE. User is already in a ring.')
        # hold for other methods and their implementation
        else:
            self.print_log(f'Inside else')

    def manage_left_client(self):
        while 1:
            response, address = self.socket_pp_1.recvfrom(4096)
            self.print_log(f'Message received from: {str(address)}')
            pd_response = pickle.loads(response)
            if(pd_response[0] == 'o-ring-setup' or pd_response[0] == 'setup-ring'):
                self.socket_pp_1.sendto(pickle.dumps('SUCCESS'), address)
                # Acknowledge is sent to right client who sent the message
                self.print_log(f'Acknowledgement sent to {str(address)}')
                # Back to Manage setup ring with the reply
                self.setup_ring(pd_response)

    def manage_right_client(self, message):
        pd_msg = pickle.loads(message)
        if(pd_msg[0] == 'o-ring-setup' or pd_msg[0] == 'setup-ring'):
            self.socket_pp_2.sendto(message, (self.rc_ip, self.rc_port))
            self.print_log(f'Message has been sent to {str((self.rc_port, self.rc_ip))}')

            reply, address = self.socket_pp_2.recvfrom(4096)
            self.print_log(f'Acknowledgment of {pickle.loads(reply)} from {str(address)} has been received')
            self.setup_ring(pickle.loads(reply))

    def teardown_left(self):
        while 1:
            response, address = self.socket_pp_1.recvfrom(4096)
            self.print_log(f'Message received from: {str(address)}')
            pd_response = pickle.loads(response)
            self.socket_pp_1.sendto(pickle.dumps('Teardown-Initialized'), address)
            self.print_log(f'Teardown has been initialized. This process will be closing it\'s socket')
            # Acknowledge is sent to right client who sent the message
            self.print_log(f'Acknowledgement sent to {str(address)}')
            self.teardown_ring(pd_response)
    
    def teardown_right(self, message):
        pd_msg = pickle.loads(message)
        self.socket_pp_2.sendto(message, (self.rc_ip, self.rc_port))
        self.print_log(f'Message from right client: {pickle.loads(message)}')
        self.print_log(f'Teardown message has been sent to {str((self.rc_port, self.rc_ip))}')
        reply, address = self.socket_pp_2.recvfrom(4096)
        self.print_log(f'Acknowledgment of {pickle.loads(reply)} from {str(address)} has been received')
        self.teardown_ring(pickle.loads(reply))

    def compute(self, depickled_data):
        self.print_log(f'From Server: {depickled_data}')


    def teardown_ring(self, depickled_data):
        if type(depickled_data) is list:
            teardown_index = 1
            # change type of list of tuples of tuple of tuples
            client_lst = tuple(depickled_data)
            client_lst = tuple(sorted(client_lst, key=lambda item: item[0]))
            self.rc_ip = client_lst[teardown_index][1]
            self.rc_port = int(client_lst[teardown_index][3])
            teardown_index+=1
            self.print_log('Sending \'teardown-ring\' to right client...')
            self.teardown_right(pickle.dumps(('teardown-ring', client_lst, teardown_index)))
        elif type(depickled_data) is tuple:
            teardown_index = depickled_data[2]
            client_lst = depickled_data[1]
            if teardown_index == 1:
                self.socket_pp_1.close()
                self.socket_pp_2.close()
                self.print_log('Sockets have been closed. Sending teardown-complete to server')
                tear_comp_msg = 'teardown-complete ' + self.teardown_id + ' ' + self.teardown_name
                self.socket_ss.sendto(tear_comp_msg.encode('utf-8'), (self.server_ip, self.destination_port))
                resp, serv_add = self.socket_ss.recvfrom(4096)
                dpckl = pickle.loads(resp)
                self.print_log(f'Server response: {dpckl}')
                self.print_log(f'Teardown of ring with ID {self.teardown_id} has been completed')
                print('Enter command to send: ')
                self.server_communication()
            else:
                if teardown_index == len(client_lst):
                    self.rc_ip = client_lst[0][1]
                    self.rc_port = int(client_lst[0][3])
                    teardown_index = 1
                else:
                    self.rc_ip = client_lst[teardown_index][1]
                    self.rc_port = int(client_lst[teardown_index][3])
                    teardown_index += 1

                self.teardown_right(pickle.dumps(('teardown-ring', client_lst, teardown_index)))
        elif type(depickled_data) is str and depickled_data == 'Teardown-Initialized':
            pass
        else:
            self.print_log(f'Something went wrong. Please try again')

    def server_communication(self):
        while 1:
            try:
                message = input('Enter command to send: ')
                self.print_log(f'Client sends {message} to server')
                decoded_split = message.split()
                # assign ports for binding. Supports only 3 ports right now
                if decoded_split[0] == 'register':
                    try:
                        port_list = []
                        for i in decoded_split[3:]:
                            if(int(i)<44000 and int(i)>43500):
                                port_list.append(i)
                        port_list = sorted(port_list)
                        if(decoded_split[2].count('.') == 3):
                            self.client_ip = decoded_split[2] # ip address of the client
                    except:
                        print('Error: Incorrect Port numbers/IP address. Please retype the command')
                    # ss_port is client port which is used to send packets to server socket 
                    # pp ports are used for peer processes. pp_1 is left, pp_2 is right
                    self.ss_port, self.pp_port_1, self.pp_port_2 = int(port_list[0]), int(port_list[1]), int(port_list[2])
                    # creates sockets and binds the correct ports to them
                    self.create_bind_sockets()
                elif decoded_split[0] == 'setup-ring':
                    self.compute_port = decoded_split[2]
                try:
                    # check if length of message to server is equal to the length of the message inputted
                    if(self.socket_ss.sendto(message.encode('utf-8'), (self.server_ip, self.destination_port)) == len(message)):
                        # Receive data from server (data, addr)
                        response, server_addr = self.socket_ss.recvfrom(4096)
                        # depickles the received response
                        de_pickle = pickle.loads(response)
                        self.print_log(f'Server response: {de_pickle}')
                        if(decoded_split[0] == 'setup-ring' and type(de_pickle) is tuple and de_pickle[0] == 'SUCCESS'):
                            self.setup_ring(de_pickle)

                        elif(decoded_split[0] == 'setup-ring' and type(de_pickle) is tuple and de_pickle[0] == 'FAILURE'):
                            self.print_log('Server returned code FAILURE for setup-ring.')

                        elif(decoded_split[0] == 'register' and type(de_pickle) is tuple and de_pickle == 'SUCCESS'):
                            self.print_log(f'{decoded_split[1]} has been registered with the server!')

                        elif(decoded_split[0] == 'register' and type(de_pickle) is tuple and de_pickle == 'FAILURE'):
                            self.print_log(f'{decoded_split[1]} couldn\'t be registered with the server. Please try again')

                        elif(decoded_split[0] == 'deregister' and type(de_pickle) is str and de_pickle == 'SUCCESS'):
                            self.print_log(f'{decoded_split[1]} has been deregistered')

                        elif(decoded_split[0] == 'deregister' and type(de_pickle) is str and de_pickle == 'FAILURE'):
                            self.print_log(f'{decoded_split[1]} couldn\'t be deregistered. Please try again')

                        elif(decoded_split[0] == 'teardown-ring' and type(de_pickle) is str and de_pickle == 'SUCCESS'):
                            self.teardown_id = decoded_split[1]
                            self.teardown_name = decoded_split[2]
                            lst_clients = list(self.clients)
                            self.teardown_ring(lst_clients)

                        elif(decoded_split[0] == 'teardown-ring' and type(de_pickle) is str and de_pickle == 'FAILURE'):
                            self.print_log('Client has to be leader of O-Ring')

                        elif(decoded_split[0] == 'compute' and type(de_pickle) is tuple and de_pickle[0] == 'SUCCESS'):
                            self.compute(de_pickle)

                        elif(decoded_split[0] == 'compute' and type(de_pickle) is tuple and de_pickle[0] == 'FAILURE'):
                            self.print_log('Compute command couldn\'t be selected')

                        else:
                            # self.print_log('Unexpected command was passed. Reinput')
                            pass
                except socket.error as message:
                    self.print_log(f'Error Code: {str(message[0])} | Message {message[1]}')
                    sys.exit()

            except KeyboardInterrupt:
                    self.close_socket()

    def create_bind_sockets(self):
        # bind socket to pp_port_2 (right)
        try:
            self.socket_pp_2.bind((self.client_ip, self.pp_port_2))
            self.print_log(f'Binded pp_2 to {self.client_ip}:{self.pp_port_2} successful')
        except socket.error as msg:
            self.print_log('Bind to pp_port_2 failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
            sys.exit()
        
        # Bind socket to pp_port_1 (left)
        try:
            self.socket_pp_1.bind((self.client_ip, self.pp_port_1))
            self.print_log(f'Binded pp_1 to {self.client_ip}:{self.pp_port_1} successful')
        except socket.error as msg:
            self.print_log('Bind to pp_port_1 failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
            sys.exit()
        
        # Bind socket to ss_port (server)
        try:
            self.socket_ss.bind((self.server_ip, self.ss_port))
            self.print_log(f'Binded ss to {self.server_ip}:{self.ss_port} successful')
        except socket.error as msg:
            self.print_log('Bind to ss_port failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
            sys.exit()

    def close_socket(self):
        # Close socket
        if(self.socket_ss is None or self.socket_pp_1 is None or self.socket_pp_2 is None):
            sys.exit()
        else:
            self.print_log('Closing the sockets')
            self.socket_ss.close()
            self.socket_pp_1.close()
            self.socket_pp_2.close()
            self.print_log('Sockets closed')
            sys.exit()

def main():
    # get port and server_ip from command line
    argv = sys.argv[0:]
    # check if the 2nd argument is an ip address
    if(argv[1].count('.') != 3):
        print('Usage: python3 Client.py <server ipaddress>')
        sys.exit()
    else:
        server_ip = argv[1] # get server IP
        print(f'Argument passed: server IP {server_ip}. Port is 43599 by default')

    udp_client = UDPClient(server_ip, 43599)
    udp_client.print_log('Making instances...')
    server_instance = threading.Thread(target=udp_client.server_communication)
    client_instance = threading.Thread(target=udp_client.manage_left_client)
    teardown_left_instance = threading.Thread(target=udp_client.teardown_left)

    try:
        udp_client.print_log('Server Instance up and running')
        udp_client.print_log('Client Instances up and running')
        server_instance.start()
        client_instance.start()
        teardown_left_instance.start()

    except KeyboardInterrupt:
        server_instance.join()
        client_instance.join()
        udp_client.close_socket()


if __name__ == '__main__':
    main()
