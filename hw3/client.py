import socket, select
import sqlite3
import sys
import re
from datetime import date
import time
import boto3

host = sys.argv[1]
port = int(sys.argv[2])

#client socket set up
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
check = client_socket.connect_ex((host, port))
s3 = boto3.resource('s3')

current_client = ""
def set_client(client_name):
    global current_client
    current_client = client_name

# def get_client():
#     global current_client
#     # current_client = current_client
#     print(current_client)
#     return current_client

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
                cmd = input('% ').strip()
                msg = cmd
                cmd = cmd.split()
                if cmd == "":
                    continue
                elif cmd[0] == 'exit':
                    client_socket.send(msg.encode('utf-8'))
                    # time.sleep(1)
                    client_socket.close()
                    sys.exit()
                else:
                    # client_socket.send(cmd.encode('utf-8'))
                    # client_socket.setblocking(True)
                    # msg = client_socket.recv(4096).decode('utf-8').strip('\n')
                    if cmd[0] == 'register':
                        client_socket.send(msg.encode('utf-8'))
                        # client_socket.setblocking(True)
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        if server_response == 'Register successfully.':
                            s3_response = s3.create_bucket(Bucket = '0613457' + cmd[1])
                        print(server_response)

                    elif cmd[0] == 'login':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        if server_response == 'Welcome, {}.'.format(cmd[1]):
                            target_bucket = s3.Bucket('0613457' + cmd[1])
                            set_client(cmd[1])
                        
                        print(server_response)

                    elif cmd[0] == 'logout' or cmd[0] == 'whoami' or cmd[0] == 'create-board':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        print(server_response)
                    
                    elif cmd[0] == 'create-post':
                        post = re.split(r'create-post | --title | --content ', msg)
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')

                        if server_response.split('post_id:')[0] == 'Create post successfully.':
                            #create and write post content to file
                            post_id = server_response.split('post_id:')[1]
                            content_file = open("./tmp/{}_content.txt".format(post_id), "w")
                            content_file.write(post[3])
                            content_file.close()
                            #create post_comment file
                            comment_file = open("./tmp/{}_comment.txt".format(post_id), "w")
                            comment_file.close()
                            #upload post object to current_client's bucket
                            target_bucket = s3.Bucket('0613457' + current_client)
                            target_bucket.upload_file('./tmp/{}_content.txt'.format(post_id), '{}_content.txt'.format(post_id) )
                            target_bucket.upload_file('./tmp/{}_comment.txt'.format(post_id), '{}_comment.txt'.format(post_id) )
                            print('Create post successfully.')
                        else:
                            print(server_response)
        
                    elif cmd[0] == 'list-board':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        # if server_response is not "":
                        print(server_response)
                        client_socket.setblocking(False)
                        try:
                            while True:
                                time.sleep(1)
                                server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                                print(server_response)
                        except:
                            client_socket.setblocking(True)
                            
                    elif cmd[0] == 'list-post':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        print(server_response)
                        client_socket.setblocking(False)
                        try:
                            while True:
                                time.sleep(1)
                                server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                                print(server_response)
                        except:
                            client_socket.setblocking(True)

                    elif cmd[0] == 'read':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        if server_response != 'Post does not exist.' and server_response != 'Usage: read <post-id>':
                            #print post metadata
                            post_metadata = server_response.split('--')[0]
                            print(post_metadata + '--')
                            #get matched id post object
                            target_bucket = s3.Bucket('0613457' + server_response.split('--')[1])
                            #get post content
                            content_object = target_bucket.Object('{}_content.txt'.format(cmd[1]))
                            comment_object = target_bucket.Object('{}_comment.txt'.format(cmd[1]))
                            raw_content = content_object.get()['Body'].read().decode('utf-8')
                            raw_comment = comment_object.get()['Body'].read().decode('utf-8')
                            
                            # handle content
                            content = raw_content.strip('\n').split('<br>')
                            for s in content:
                                print('   ' + s)  
                            print('   --')
                            
                            # handle comment
                            count = 0
                            comment = raw_comment.split('\n')
                            if len(comment) != 1 and comment[0] != '':
                                for c in comment:
                                    if count < (len(comment) - 2):
                                        print('   ' + c)
                                    else:
                                        print('   ' + c)
                                        break
                                    count = count + 1
                        else:
                            print(server_response)        
                    elif cmd[0] == 'update-post':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        # if server_response.split('author:')[0] == 'Update successfully.':
                        if server_response == 'Update successfully.':
                            if re.search('title', msg) == None:
                                u_post = re.split(r'update-post | --content ', msg)
                                
                                content_file = open("./tmp/{}_content.txt".format(u_post[1]), "w")
                                content_file.write(u_post[2])
                                content_file.close()

                                target_bucket = s3.Bucket('0613457' + current_client)
                                target_bucket.upload_file('./tmp/{}_content.txt'.format(u_post[1]), '{}_content.txt'.format(u_post[1]) )
                        
                        print(server_response)

                    elif cmd[0] == 'delete-post':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        if server_response == 'Delete successfully.':
                            target_bucket = s3.Bucket('0613457' + current_client)
                            content_object = target_bucket.Object('{}_content.txt'.format(cmd[1]))
                            comment_object = target_bucket.Object('{}_comment.txt'.format(cmd[1]))
                            content_object.delete()
                            comment_object.delete()
                        
                        print(server_response)

                    elif cmd[0] == 'comment':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        if server_response.split('author:')[0] == 'Comment successfully.':
                            cmt = msg.split(' ', 2)
                            post_id = cmt[1]
                            ##
                            target_bucket = s3.Bucket('0613457' + server_response.split('author:')[1])
                            comment_object = target_bucket.Object('{}_comment.txt'.format(post_id))
                            comment = comment_object.get()['Body'].read().decode('utf-8')
                            
                            comment_file = open("./tmp/{}_comment.txt".format(post_id), "w")
                            comment_file.write(comment + current_client + ': ' + cmt[2] + '\n')
                            comment_file.close()

                            target_bucket.upload_file('./tmp/{}_comment.txt'.format(post_id), '{}_comment.txt'.format(post_id))
                            ##
                            print('Comment successfully.')
                        else:
                            print(server_response)
                    elif cmd[0] == 'mail-to':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        if server_response.split('mail_id:')[0] == 'Sent successfully.':
                            mail_id = server_response.split('mail_id:')[1]
                            mail = re.split(r'mail-to | --subject | --content ', msg)
                            
                            target_bucket = s3.Bucket('0613457' + mail[1])
                            mail_file = open("./tmp/mail_{}.txt".format(mail_id), "w")
                            mail_content = []
                            mail_content.append('   Subject   :{}\n'.format(mail[2]))
                            mail_content.append('   From      :{}\n'.format(current_client))
                            mail_content.append('   Date      :{}\n'.format(str(date.today())))
                            mail_content.append('   --\n')
                            for s in mail[3].split('<br>'):
                                mail_content.append('   {}\n'.format(s))
                            
                            mail_file.writelines(mail_content)
                            mail_file.close()

                            target_bucket.upload_file('./tmp/mail_{}.txt'.format(mail_id), 'mail_{}.txt'.format(mail_id))
                            print('Sent successfully.')
                        else:
                            print(server_response)
                    elif cmd[0] == 'list-mail':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        print(server_response)
                        client_socket.setblocking(False)
                        try:
                            while True:
                                time.sleep(1)
                                server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                                print(server_response)
                        except:
                            client_socket.setblocking(True)

                    elif cmd[0] == 'retr-mail' or cmd[0] == 'delete-mail':
                        client_socket.send(msg.encode('utf-8'))
                        server_response = client_socket.recv(4096).decode('utf-8').strip('\n')
                        if server_response == 'Success':
                            target_bucket = s3.Bucket('0613457' + current_client)
                            mail_count = 0
                            check_for_mail = 0
                            for obj in target_bucket.objects.filter(Prefix = 'mail'):
                                mail_count = mail_count + 1
                                if int(cmd[1]) == mail_count:
                                    check_for_mail = 1
                                    if cmd[0] == 'retr-mail':
                                        print(obj.get()['Body'].read().decode('utf-8').strip('\n'))
                                    else:
                                        obj.delete()
                                        print('Mail deleted.')
                                    break
                            if check_for_mail == 0:
                                print('No such mail.')
                        else:
                            print(server_response)
                    
                    else:
                        print('Unknowm command')
                    #break
        # except Exception:
        #     print('disconnected\n')
        #     sys.exit()
    
   






