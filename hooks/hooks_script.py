#!/usr/bin/python

import sys
import os
import subprocess
from subprocess import Popen, PIPE
import time
import pexpect
import shutil, errno
from distutils.dir_util import copy_tree


git_cmd = "/usr/bin/git"
user_refact_msg = "user refactor (will be deleted)"
unpushed_commit_folder = "hooks/.tmp_refac/"
unpushed_commit_file_name = "unpushed_commit"

def main(argv):

	if "pull" in argv :
		pull_hook(argv)
	elif "push" in argv :
		push_hook(argv)
	elif "commit" in argv :
		commit_hook(argv)
	else :
		print("commande originale.")
		full_cmd = argv
		full_cmd.insert(0, git_cmd)
		execute_cmd(full_cmd)



def commit_hook(argv):	
	# Real commit
	full_cmd = argv
	full_cmd.insert(0, git_cmd)
	res = execute_cmd(full_cmd)
	
	post_commit()

	
def post_commit() :
	sha1 = ""
	branch_name = ""
	message = ""
	
	branch_name = execute_cmd( [ git_cmd, "rev-parse", "--abbrev-ref", "HEAD"], print_it=False ).strip()
	log_res = execute_cmd( [ git_cmd, "log",  "--pretty=oneline",  "-n",  "1" ], print_it=False )
	log_values = log_res.split(" ", 1)
	sha1 = log_values[0]
	message = log_values[1]
	
	update_unpushed_commit_file(sha1, branch_name, message)
	
	
def update_unpushed_commit_file(sha1, branch_name, message):
	path = get_root_directory() + "/" + unpushed_commit_folder
	
	if not os.path.exists(path):
		os.makedirs(path)
	
	write_file(path + unpushed_commit_file_name, sha1 + " " + branch_name + " " + message) 

def pull_hook(argv):
	#pre_pull 
	pre_pull()

	full_cmd = argv
	full_cmd.insert(0, git_cmd)
	#launch the real pull cmb given by the user
	res = execute_cmd(full_cmd)
		
	#post_pull 
	res = post_pull()

def pre_pull():
	nb_commit_to_check = 2
	last_commits = execute_cmd( [ git_cmd, "log",  "--pretty=oneline",  "-n",  str(nb_commit_to_check) ], print_it=False )
	last_commits = last_commits.splitlines()
	position_in_head = find_position_of_a_commit(last_commits, user_refact_msg)
	
	#On reset le commit
	#On reformat-serv
	#On refait le commit si il y en avait un 
	
	#if the commit was found
	if position_in_head :
		commit_message = None
		if position_in_head != 1 :
			commit_message = last_commits[0].split(" ", 1)[1]
		#reset to HEAD~N	
		git_reset_head(position_in_head)
		
		#we do the server refactor
		srv_refactor(str(commit_message))

def post_pull():
	user_refactor()
	

#find the positon of a commit in HEAD thank to his message
def find_position_of_a_commit(commit_list, commit_message):
	head = 1;
	for commit in commit_list :
		if commit_message in commit :
			return head
		else :
			head += 1
	return None
	
def push_hook(argv):
	print("push hook")
	
	#first, pre_push operations
	commit_msg = pre_push()

	#and we process to the server_refactoring
	srv_refactor(commit_msg)
	
	#we push it with the real push cmd given by the user
	full_cmd = argv
	full_cmd.insert(0, git_cmd)
	res = execute_cmd(full_cmd)
	
	
	if res != 0 :
		print("on verra")
	#then post_push operations
	post_push()

def pre_push():
	#get the two last commit sha1 and message
	two_last_commit = execute_cmd( [ git_cmd, "log",  "--pretty=oneline",  "-n",  "2" ], print_it=False)
	#get the messages of the commits
	first_commit_sha1_msg = two_last_commit.splitlines()[0].split(" ", 1)
	second_commit_sha1_msg = two_last_commit.splitlines()[1].split(" ", 1)
	
	#default param if the last commit is the user refactor commit
	commit_msg = None
	head = 1
	
	#if the first commit isn't the refactor user commit
	if user_refact_msg != first_commit_sha1_msg[1] :
		head += 1
		commit_msg = first_commit_sha1_msg[1]
	
	#then we reset the commit(s)
	git_reset_head(head)
	return commit_msg


def post_push():
	#we simply apply the user_refactor process
	user_refactor()
	

def srv_refactor(commit_msg=None):
	
	#TODO : le refactoring server
	#Du coup je fait un mock pour le moment
	os.system("python3 mock_refac_srv.py")
	
	#the rebased commit (if we have to)
	if commit_msg :
		git_add_all()
		git_simple_commit(commit_msg)
	
	
def user_refactor():
	#TODO : le user refactoring
	#Du coup je fait un mock pour le moment
	os.system("python3 mock_refac_usr.py")
	
	
	#adding all refactored files
	git_add_all()
	
	#then we commit it with our default message
	git_simple_commit(user_refact_msg)

	
def git_simple_commit(message):
	return execute_cmd([git_cmd, "commit", "-m", message ], print_it=False)

def git_reset_head(head):
	execute_cmd( [ git_cmd, "reset",  ("HEAD~" + str(head)) ], print_it=False)
	
def git_add_all():
	execute_cmd( [ git_cmd, "add", "--all"  ], print_it=False)
	
	
def array_to_string(argv):
	arg_string = ""
	for arg in argv :
		arg_string += arg + " "
	return arg_string
	
"""
will execute the cmd in the system.
the main cmd and each argument have to be in an element of the list
return the value of the command
"""
def execute_cmd(arg_list, print_it=True):
	#create the proc
	proc = subprocess.Popen(arg_list, stdout=subprocess.PIPE)
	#communicate with the proc and get the stdout value
	stdout_value = proc.communicate()[0].decode("utf-8")
	if print_it != False :
		print(stdout_value)
	if proc.returncode != 0 :
		return proc.returncode
	return stdout_value


def read_file(path):
	f = open(path, 'r')
	file_str = f.read()
	f.close()
	return file_str

#pathname include the complete path from the source repo
def copy_unpushed_commit_file(sha1, pathname, path_file_to_copy):
	
	#we read the file
	file_str = read_file(path_file_to_copy)
	#creation of the filename
	new_file_name = sha1 + "/" + pathname
	complete_copyfile_path = get_root_directory() + unpushed_commit_folder + new_file_name
	#write the file to the wanted path
	write_file(complete_copyfile_path, file_str, mode="w")
	
def write_file(path, data, mode="a+"):
	f = open(path, mode)
	f.write(data)
	f.close()

def recreate_unpushed_commits():
	#TODO : finir ca
	
	#unpushed_commit_info_list = parse_unpushed_commit_tmp()
	
	
	#test copy folder
	copyanything(get_root_directory() + unpushed_commit_folder + "shadir", get_root_directory())
	
	
	#for commit_hash in unpushed_commit_info_list:
	unpushed_commit_list = parse_unpushed_commit_tmp()
	
	for commit_hash in unpushed_commit_list:
		unpushed_commit = get_root_directory() + unpushed_commit_folder + commit_hash["sha1"]
		#copy all the file 
		copyanything(unpushed_commit, get_root_directory())
		#gerer les cas chiant PLUS TARD
		
		

def copyanything(src, dst):
    # copy subdirectory example
	fromDirectory = src
	toDirectory = dst

	copy_tree(fromDirectory, toDirectory)

		

#return a hash of information for all the unpushed commit
def parse_unpushed_commit_tmp():
	path = get_root_directory() + unpushed_commit_folder + unpushed_commit_file_name
	
	#array with the parsed info
	commit_info_list = []
	file_str_array = read_file(path).splitlines()
	
	for line in file_str_array:
		#split with the 2 first space char
		l_parse = line.split(" ", 2)
		commit_info_list.append({ "sha1" : l_parse[0], "branch" : l_parse[1], "message" : l_parse[2] })
	return commit_info_list
	

def delete_folder_with_files(path):
	shutil.rmtree(path)
	
def get_root_directory():
	root_dir = execute_cmd([ git_cmd, "rev-parse" ,"--show-toplevel" ], print_it=False).strip()
	return root_dir + "/"

if __name__ == "__main__":
   main(sys.argv[1:])
