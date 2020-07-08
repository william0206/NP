import socket, select
import sqlite3
import sys
import re
from datetime import date
host = '127.0.0.1'
port = 8787

#server socket set up
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host, port)) 
server_socket.listen(15) #set maximum connections
server_socket.setblocking(0) #set nonblocking
#connect to db
con2db = sqlite3.connect('hw.db') #if not exist, create file hw1.db
# con2db2 = sqlite3.connect('hw2_board.db')
# con2db3 = sqlite3.connect('hw2_post.db')
# con2db4 = sqlite3.connect('hw2_post_article.db')
# con2db5 = sqlite3.connect('hw2_post_comment.db')
c = con2db.cursor()
# c2 = con2db2.cursor()
# c3 = con2db3.cursor()
# c4 = con2db4.cursor()
# c5 = con2db4.cursor() # Todo: merge into one db!!! & show comments 

# c.execute("""CREATE TABLE USERS (
#                 uid INTEGER PRIMARY KEY AUTOINCREMENT,
#                 username TEXT NOT NULL UNIQUE,
#                 email TEXT NOT NULL,
#                 password TEXT NOT NULL
#             )""")

# c.execute("""CREATE TABLE BOARD (
#                 Idx INTEGER PRIMARY KEY AUTOINCREMENT,
#                 Name TEXT NOT NULL UNIQUE,
#                 Moderator TEXT NOT NULL
#             )""")

# c.execute("""CREATE TABLE POST (
#                 ID INTEGER PRIMARY KEY AUTOINCREMENT,
#                 Title TEXT NOT NULL UNIQUE,
#                 Author TEXT NOT NULL,
#                 Date TEXT NOT NULL,
#                 Board TEXT NOT NULL
#             )""")

# c.execute("""CREATE TABLE ARTICLE (
#                 post_id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 article TEXT
#             )""")

# c.execute("""CREATE TABLE COMMENT (
#                 post_id INTEGER NOT NULL,
#                 user TEXT NOT NULL,
#                 comment TEXT
#             )""")

inputs = [server_socket] #the file descripter to keeo track of 
status = {} #dict structure {skt, '0'/'username'} to record the login status, not login-->"0"; login-->"username"
while True:
    #monitor the file descipters in inputs, and set the blocking time to 2sec, if there're requests, it'll be put into readable
    readable, output, err = select.select(inputs, [], [], 2)
    #do corresponding action for different file descripter(socket) in readable 
    for skt in readable:
        if skt is server_socket:
            conn, addr = server_socket.accept()
            conn.setblocking(0) #set conn socket to nonblocking
            conn.send('********************************\n** Welcome to the BBS server. **\n********************************\n'.encode('utf-8'))
            conn.send('% '.encode('utf-8'))
            inputs.append(conn) #add the newly created conn socket to inputs list, so select.select can keep track of it 
            print('New connection.')
            #print('connected by' + str(addr))
            status[conn] = '0' #add the new conn to dict status, and initialize to '0'
        else: #if it's not the server socket, then it must be the conn socket for recv & send
            msg = skt.recv(1024).decode('utf-8').strip()
            
            #process different recv msg(command from users)
            if msg is not "": #not "" means it's not sending nothing
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
                        check_for_user = 0 #a flag to check weather the useranme has already been used
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
                        if status[skt] == '0': #has not logined
                            check_for_login = 0 #a flag to check weather the user is successfully login 
                            row = c.execute('SELECT username, password FROM USERS')
                            for r in row:
                                if r[0] == cmd[1] and r[1] == cmd[2]: #the username & password are both correct
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
                elif cmd[0] == 'create-board':
                    if len(cmd) == 2:
                        if status[skt] != '0':
                            data = c.execute('SELECT Name FROM BOARD WHERE Name = ?',(cmd[1],)).fetchall()

                            if not data:
                                c.execute('INSERT INTO BOARD (Name, Moderator) VALUES (?, ?)', (cmd[1], status[skt]))
                                skt.send('Create board successfully.\n'.encode('utf-8'))
                            else:
                                skt.send('Board already exist.\n'.encode('utf-8'))
                        else:
                            skt.send('Please login first.\n'.encode('utf-8'))
                    else:
                        skt.send('Usage: create-board <name>\n'.encode('utf-8'))
                elif cmd[0] == 'create-post':
                    check_for_post = re.fullmatch(r'create-post .+ --title .+ --content .+', msg)
                    if check_for_post != None:
                        if status[skt] != '0':
                            post = re.split(r'create-post | --title | --content ', msg)

                            #check_for_board = 0
                            data = c.execute('SELECT Name FROM BOARD WHERE Name = ?',(post[1],)).fetchall()
                            if not data:
                                skt.send('Board does not exist.\n'.encode('utf-8'))
                            else: #board do exist
                                today = str(date.today())    
                                c.execute('INSERT INTO POST (Title, Author, Date, Board) VALUES (?, ?, ?, ?)', (post[2], status[skt], today, post[1]))
                                #handle article
                                c.execute('INSERT INTO ARTICLE (article) VALUES (?)', (post[3], ))
                                
                                skt.send('Create post successfully.\n'.encode('utf-8'))
                        else:
                            skt.send('Please login first.\n'.encode('utf-8'))
                    else:
                        skt.send('Usage: create-post <board-name> --title <title> --content <content>\n'.encode('utf-8'))
                elif cmd[0] == 'list-board':
                    # if status[skt] != '0':
                        if len(cmd) == 1:
                            skt.send('   Index       Name          Moderator     \n'.encode('utf-8'))
                            row = c.execute('SELECT * FROM BOARD')
                            for r in row:
                                skt.send('   {:<12}{:<14}{:<14}\n'.format(r[0], r[1], r[2]).encode('utf-8'))
                        else:
                            key = cmd[1][2::] #key for board name

                            skt.send('   Index       Name          Moderator     \n'.encode('utf-8'))
                            row = c.execute('SELECT * FROM BOARD')
                            for r in row:
                                if re.search(str(key), r[1]) != None:
                                    skt.send('   {:<12}{:<14}{:<14}\n'.format(r[0], r[1], r[2]).encode('utf-8'))   
                    # else:
                    #     skt.send('Please login first.\n'.encode('utf-8'))
                elif cmd[0] == 'list-post': 
                    if len(cmd) == 2 or len(cmd) == 3:
                        # if status[skt] != '0':
                            check_for_board = c.execute('SELECT Name FROM BOARD WHERE Name = ?', (cmd[1], )).fetchone()
                            if not check_for_board:
                                skt.send('Board does not exist.\n'.encode('utf-8'))
                            else:
                                skt.send('   ID       Ttile            Author       Date   \n'.encode('utf-8'))
                                row = c.execute('SELECT * FROM POST WHERE Board = ?', (cmd[1], )).fetchall()
                                if len(cmd) == 3:
                                    key = cmd[2][2::] #key for post title
                                for r in row:
                                    if len(cmd) == 3:
                                        if re.search(str(key), r[1]) != None:
                                            skt.send('   {:<9}{:<17}{:<13}{:<7}\n'.format(r[0], r[1], r[2], r[3].split('-')[1] + '/' + r[3].split('-')[2]).encode('utf-8'))
                                    else:
                                        skt.send('   {:<9}{:<17}{:<13}{:<7}\n'.format(r[0], r[1], r[2], r[3].split('-')[1] + '/' + r[3].split('-')[2]).encode('utf-8'))
                        # else:
                        #     skt.send('Please login first.\n'.encode('utf-8'))
                    else:
                        skt.send('Usage: list-post <board-name> ##<key>\n'.encode('utf-8'))
                elif cmd[0] == 'read':
                    if len(cmd) == 2:
                        # if status[skt] != '0':
                            data = c.execute('SELECT * FROM POST WHERE ID = ?', (int(cmd[1]), )).fetchone()
                            if not data:
                                skt.send('Post does not exist.\n'.encode('utf-8'))
                            else:
                                skt.send('   Author   :{}\n   Title    :{}\n   Date     :{}\n   --\n'.format(data[2], data[1], data[3]).encode('utf-8'))
                                    
                                article_raw = c.execute('SELECT * FROM ARTICLE WHERE post_id=?', (int(data[0]),)).fetchone()
                                article = article_raw[1].split('<br>')                                    
                                for p in article:
                                    skt.send(('   ' + p + '\n').encode('utf-8'))
                                skt.send('   --\n'.encode('utf-8'))
                                #handle comment
                                cmts = c.execute('SELECT * FROM COMMENT WHERE post_id = ?', (int(data[0]),)).fetchall()
                                for cmt in cmts:
                                    skt.send(('   ' + cmt[1] + ': ' + cmt[2] + '\n').encode('utf-8'))
                        # else:
                        #     skt.send('Please login first.\n'.encode('utf-8'))
                    else:
                        skt.send('Usage: read <post-id>\n'.encode('utf-8'))
                elif cmd[0] == 'update-post':
                    check_format = re.fullmatch(r'update-post [0-9]+ --title .+|update-post [0-9]+ --content .+', msg) 
                    if check_format != None: #correct cmd format
                        if status[skt] != '0':

                            if re.search('title', msg) != None:
                                u_post = re.split(r'update-post | --title ', msg)
                                post_data = c.execute('SELECT * FROM POST WHERE ID = ?', (u_post[1],)).fetchone()
                                
                                if not post_data:
                                    skt.send('Post does not exist.\n'.encode('utf-8'))
                                else:
                                    if post_data[2] == status[skt]:
                                        c.execute('UPDATE POST SET Title = ? WHERE ID = ?', (u_post[2], u_post[1]))
                                        skt.send('Update successfully.\n'.encode('utf-8'))
                                    else:
                                        skt.send('Not the post owner.\n'.encode('utf-8'))
                            else:
                                u_post = re.split(r'update-post | --content ', msg)
                                post_data = c.execute('SELECT * FROM POST WHERE ID = ?', (u_post[1],)).fetchone()
                                if not post_data:
                                    skt.send('Post does not exist.\n'.encode('utf-8'))
                                else:
                                    if post_data[2] == status[skt]:
                                        c.execute('UPDATE ARTICLE SET article = ? WHERE post_id = ?', (u_post[2], u_post[1]))
                                        skt.send('Update successfully.\n'.encode('utf-8'))
                                    else:
                                        skt.send('Not the post owner.\n'.encode('utf-8'))
                        else:
                            skt.send('Please login first.\n'.encode('utf-8'))
                    else:
                        skt.send('Usage: update-post <post-id> --title/content <new>\n'.encode('utf-8'))
                elif cmd[0] == 'delete-post':
                    if len(cmd) == 2:
                        if status[skt] != '0':
                            post_data = c.execute('SELECT * FROM POST WHERE ID = ?', (int(cmd[1]), )).fetchone()
                            if not post_data:
                                skt.send('Post does not exist.\n'.encode('utf-8'))
                            else:
                                if post_data[2] == status[skt]:
                                    c.execute('DELETE FROM POST WHERE ID = ?', (int(cmd[1]), ))
                                    c.execute('DELETE FROM ARTICLE WHERE post_id = ?', (int(cmd[1]), ))
                                    c.execute('DELETE FROM COMMENT WHERE post_id = ?', (int(cmd[1]), ))
                                    skt.send('Delete successfully.\n'.encode('utf-8'))
                                else:
                                    skt.send('Not the post owner.\n'.encode('utf-8'))
                        else:
                            skt.send('Please login first.\n'.encode('utf-8'))
                    else:
                        skt.send('Usage: delete-post <post-id>\n'.encode('utf-8'))
                elif cmd[0] == 'comment':
                    check_format = re.fullmatch(r'comment [0-9]+ .+', msg)
                    if check_format != None:
                        if status[skt] != '0':
                            cmt = msg.split(' ', 2)
                            post_data = c.execute('SELECT ID FROM POST WHERE ID = ?', (cmt[1], )).fetchone()
                            if not post_data:
                                skt.send('Post does not exist.\n'.encode('utf-8'))
                            else:
                                c.execute('INSERT INTO COMMENT (post_id, user, comment) VALUES (?, ?, ?)', (int(cmt[1]),status[skt], cmt[2]))
                                skt.send('Comment successfully.\n'.encode('utf-8'))
                        else:
                            skt.send('Please login first.\n'.encode('utf-8'))
                    else:
                        skt.send('Usage: comment <post-id> <comment>\n'.encode('utf-8'))        
                else:
                    print(msg)
                    skt.send("Unknowm command\n".encode('utf-8'))
                
                #must commit so that chamges made will be updated to the db
                con2db.commit()  
                # con2db2.commit()
                # con2db3.commit()
                # con2db4.commit()
                # con2db5.commit()
                skt.send('% '.encode('utf-8')) 
        
    
            

            
                
            
    
        
   
        
    


