import socket, sys, threading, time, random, uuid
ring_id_database = {}
big_database = []


BUFFER_SIZE = 4096
def create_socket():
    # Create socket
    try:
        socket_new = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print('Socket creation successful!')
        return socket_new
    except socket.error as msg:
        print('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
        sys.exit()

def bind_socket(socket_p, portnumber, host = ''):
    # Bind socket to local host and port
    try:
        if(socket_p.bind((host, portnumber)) == 0):
            print('Bind successful')
    except socket.error as msg:
        print('Bind failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
        sys.exit()

def run_UDPserver(socket_p, portnumber, buffersize):
    # Start the UDP server
    while 1:
        print('UDP Server is up and listening to port: ', portnumber)
        # receive data from client is in form (data, client_address)
        send_code = 'None'
        data, client_addr = socket_p.recvfrom(buffersize)
        decoded_data = data.decode('utf-8')
        decoded_split = decoded_data.split()
        # for register command
        if(decoded_split[0] == 'register'):
            print('REGISTER command selected')
            #print(f'strip is: {decoded_split}')
            # only enter
            if(len(decoded_split[1])>15):
                print('Username should be less than 15 characters long')
                send_code = 'FAILURE'
            else:
                check_duplicate_ports = False
                # duplicate port check
                print('before for loop', big_database)
                for i in range(len(big_database)):
                    if(decoded_split[1] in big_database[i]):
                        print('Duplicate username, cannot register')
                        send_code = 'FAILURE'
                    elif(send_code != 'FAILURE'):
                        for j in decoded_split[3:]:
                            if(j =='Free' or j=='InRing' or j == 'Leader'):#ignore state strings
                                check_duplicate_ports = False
                            elif(j in big_database[i]):
                                check_duplicate_ports = True # duplicate ports exist
                            else:
                                check_duplicate_ports = False
                    else:
                        print('Should not be in this case of register!!!')
                        send_code = 'FAILURE'
                # correct port range check
                port_range = False
                for i in decoded_split[3:]:
                    if(int(i)>=43500 and int(i)<=43999):
                        port_range = True # correct port range
                    else:
                        port_range = False
                # check for port range, duplicate ports and if ipaddress is provided in correct format and if send_code is FAILURE
                # if send code is FAILURE then that means either a username longer than 15 chars is used, duplicate username exists or goes in else statement for loop shouldn't go inside
                # if parameters are unique then append them to the big_database.
                if(decoded_split[2].count('.') != 3 or (port_range == False) or (check_duplicate_ports == True) or (send_code == 'FAILURE')):
                    print('Duplicate Username, Improper IP address or Improper port numbers. Please reinput')
                    print(decoded_split[2].count('.'), port_range, check_duplicate_ports, send_code)
                    send_code = 'FAILURE'
                    print('Failure', big_database)
                else:
                    decoded_split.append('Free')
                    big_database.append(list(decoded_split[1:]))
                    send_code = 'SUCCESS'
                    print('Success', big_database)

        # for deregister command
        elif(decoded_split[0] == 'deregister'):
            print('DEREGISTER command selected')
            print(f'strip is: {decoded_split}')
            for i in range(len(big_database)):
                # check if the username is already in database
                try:
                    if(decoded_split[1] in big_database[i]):
                        if('InRing' in big_database[i] or 'Leader' in big_database[i]):
                            print('Client has state InRing or is Leader, cannot deregister')
                            send_code =  'FAILURE'
                        else:
                            # deregister
                            try:
                                del big_database[i]
                                print('Client has been deregistered')
                                send_code = 'SUCCESS'
                                print(big_database)
                            except:
                                print('Deregistration failed even when client was not InRing/Leader')
                                send_code = 'FAILURE'
                except:
                    print('Deregistration failed. client name is not in registry')
                    print(big_database)
                    send_code = 'FAILURE'


        # for setup-ring command
        elif(decoded_split[0] == 'setup-ring'):
            print('SETUP-RING command')
            # will have setup-ring <n> <user-name> (n>=3)
            n = int(decoded_split[1])
            free_position = []
            #check if correct n value is being used
            if(n>=3 and n%2==1):
                print('n is', n, 'databaseis', big_database)
                user_name = decoded_split[2]
                free_counter = 0 # counts the number of free users in the database
                #check if user_name is registered and Free
                username_flag = False
                for i in range(len(big_database)):
                    if('Free' in big_database[i]):
                        # username is free
                        username_flag = True
                        free_counter += 1
                    elif(user_name in big_database[i]):
                        # username is in big database
                        username_flag = True
                    else:
                        username_flag = False

                # TODO: Could assign an upper limit on n?

                if(username_flag==True and (free_counter>=(n-1))):
                    # n is odd and >=3, username is free and registered and there's atleast n-1 free users in database
                    # only 1 user can request ring making and be in the database. combating duplicates with below variable
                    user_counter = False
                    for i in range(len(big_database)):
                        if(user_name in big_database[i] and user_counter == False):
                            user_requesting_setup = big_database[i]
                            user_requesting_pos = i
                            user_counter = True # user_requesting_setup has been recognized
                        if('Free' in big_database[i] and (user_name not in big_database[i])):
                            # finds positions of free users in the big database and appends it
                            free_position.append(i)
                    # g contains the random element positions to be selected in big database for random users
                    # if n is 3, 2 users will be randomly selected from big_database
                    # with user who requested setup-ring being the 3rd user
                    g = random.sample(free_position, (n-1))
                    # select random n-1 Free users to set their state to InRing
                    selected_users = [big_database[pos] for pos in g]
                    # append the user requesting setup to the n users list
                    selected_users.append(user_requesting_setup)
                    for i in range(len(selected_users)):
                        for j in range(len(selected_users[i])):
                            if(selected_users[i][j] == 'Free'):
                                selected_users[i][j] = 'InRing' # change state to InRing
                    # ring_id contains the ring id for the ring being made
                    ring_id = (uuid.uuid4().hex[:9])
                    send_code = 'SUCCESS'
                    # setting the ring_id in the database
                    # setdefault will not override and change information for a key if it has alreay been set
                    ring_id_database.setdefault(ring_id, selected_users)
                    # update states in big database:
                    # the states in big database should be automatically updated due to changing those specific elements and assigning them
                    # to selected users. Still printing the database to make sure!
                    print('big database is: ', big_database)
                    print
                    print('selected_users are: ', selected_users)
                    print
                    print('ringid database is: ', ring_id_database)
                else:
                    send_code = 'FAILURE'
                    print('Either username was not in database or there weren\'t enough free variables. Please type the command again')
            else:
                send_code = 'FAILURE'
                print('n is either < 3 or not odd')
        # for setup-complete
        elif('setup-complete' in decoded_split[0]):
            pass
        
        else:
            pass

        reply = 'Ok...' + data.decode('utf-8')
        socket_p.sendto(reply.encode('utf-8'), client_addr)
        print('Message[' + client_addr[0] + ':' + str(client_addr[1]) + '] - ' + data.decode('utf-8').strip())

def main(argv):
    try:
        if(len(argv)<3):
            PORT = int(argv[1])
    except:
        # print(str(sys.argv), len(sys.argv))
        print('Usage: python Server.py <port1> <port2> . . <portn>')
        sys.exit()

    socket_t = create_socket()
    bind_socket(socket_t, PORT)
    run_UDPserver(socket_t, PORT, BUFFER_SIZE)
    socket_t.close()

if __name__ == '__main__':
    main(sys.argv[0:])
