import socket, select
import sqlite3
import sys
import re
from datetime import date
import time
import threading

host = sys.argv[1]
port = int(sys.argv[2])

#client socket set up
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
check = client_socket.connect_ex((host, port))

def get_sub_msg(flag):
    while True:
        if flag() == True:
            break
        try:
            client_socket.setblocking(False)
            sub_msg = client_socket.recv(4096).decode('utf-8').strip('\n')
            print(sub_msg, end = "")
        except:
            client_socket.setblocking(True)

while not check:
    while True:
        try:
            while True:
                msg = client_socket.recv(4096).decode('utf-8').strip('\n')
                print(msg)
                client_socket.setblocking(False)
                # time.sleep(1)
        except IOError:
            client_socket.setblocking(True)
            while True:
                print('% ', end = "")
                stop_flag = False
                t = threading.Thread(target = get_sub_msg, args =(lambda : stop_flag, )) 
                t.start()
                #
                cmd = input().strip()
                #
                stop_flag = True
                t.join()

                msg = cmd
                cmd = cmd.split()
                if not cmd:
                    continue
                elif cmd[0] == 'exit':
                    client_socket.send(msg.encode('utf-8'))
                    # time.sleep(1)
                    client_socket.close()
                    sys.exit()
                else:
                    client_socket.send(msg.encode('utf-8'))
                    server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                    print(server_response)
                    client_socket.setblocking(False)
                    try:
                        while True:
                            time.sleep(0.5)
                            server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                            print(server_response)
                    except:
                        client_socket.setblocking(True)   
    
   






