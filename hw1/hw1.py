import socket, select
import sqlite3
import sys
host = '127.0.0.1'
port = 8787

#server socket set up
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port))
server_socket.listen(15)
server_socket.setblocking(0)
#connect to db
con2db = sqlite3.connect('hw1.db')
c = con2db.cursor()
'''
c.execute("""CREATE TABLE USERS (
                uid INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                password TEXT NOT NULL
            )""")
'''
inputs = [server_socket]
status = {}
while True:
    readable, output, err = select.select(inputs, [], [], 2)

    for skt in readable:
        if skt is server_socket:
            conn, addr = server_socket.accept()
            conn.setblocking(0)
            conn.send('********************************\n** Welcome to the BBS server. **\n********************************\n'.encode('utf-8'))
            conn.send('% '.encode('utf-8'))
            inputs.append(conn)
            print('New connection.')
            #print('connected by' + str(addr))
            status[conn] = '0'
        else:
            msg = skt.recv(1024).decode('utf-8').strip()
            if msg is not "":
                cmd = msg.split()

                if cmd[0] == 'exit':
                    if len(cmd) == 1:
                        status.pop(skt)
                        inputs.remove(skt)
                        skt.close()
                        continue
                    else:
                        skt.send('Usage: exit\n'.encode('utf-8'))
                elif cmd[0] == 'register':
                    if len(cmd) == 4:
                        check_for_user = 0
                        row = c.execute('SELECT username FROM USERS')
                        for r in row:
                            if r[0] == cmd[1]:
                                skt.send('Username is already used.\n'.encode('utf-8'))
                                check_for_user = 1
                                break
                            
                        if check_for_user == 0:
                            c.execute('INSERT INTO USERS (username, email, password) VALUES (?, ?, ?)', (cmd[1], cmd[2], cmd[3]))
                            skt.send('Register successfully.\n'.encode('utf-8'))
                    else:
                        skt.send('Usage: register <username> <email> <password>\n'.encode('utf-8'))
                elif cmd[0] == 'login':
                    if len(cmd) == 3:
                        if status[skt] == '0':#has not logined
                            check_for_login = 0
                            row = c.execute('SELECT username, password FROM USERS')
                            for r in row:
                                if r[0] == cmd[1] and r[1] == cmd[2]:
                                    check_for_login = 1
                                    skt.send('Welcome, {}.\n'.format(cmd[1]).encode('utf-8'))
                                    status[skt] = cmd[1]
                                    break
                            if check_for_login == 0:    
                                skt.send('Login failed.\n'.encode('utf-8')) 
                        else:
                            skt.send('Please logout first.\n'.encode('utf-8'))
                    else:
                        skt.send('Usage: login <username> <password>\n'.encode('utf-8'))
                elif cmd[0] == 'logout':
                    if len(cmd) == 1:
                        if status[skt] == '0':
                            skt.send('Please login first.\n'.encode('utf-8'))
                        else:
                            skt.send('Bye, {}.\n'.format(status[skt]).encode('utf-8'))
                            status[skt] = '0'
                    else:
                        skt.send('Usage: logout\n'.encode('utf-8'))
                elif cmd[0] == 'whoami':
                    if len(cmd) == 1:
                        if status[skt] == '0':
                            skt.send('Please login first.\n'.encode('utf-8'))
                        else:
                            skt.send('{}\n'.format(status[skt]).encode('utf-8'))
                    else:
                        skt.send('Usage: whoami\n'.encode('utf-8'))
                else:
                    print(msg)
                    skt.send("Unknowm command\n".encode('utf-8'))
                
                con2db.commit()
                skt.send('% '.encode('utf-8')) 
        
    
            

            
                
            
    
        
   
        
    


