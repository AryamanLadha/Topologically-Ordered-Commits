import os,sys, zlib
#Each commit in the directed acycylic graph will be an object of the following Class:
class CommitNode:
    def __init__(self, commit_hash):
        """
        :type commit_hash: str
        """
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()

#discover the .git repository, moving upwards through the filesystem. 
#Return the path to the directory that contains the .git repository
def discover():
    path = os.getcwd()
    isValid = False
    while(path!= ''):
        git_path = path + '/.git'
        isValid = os.path.isdir(git_path)
        if(isValid):
            break
        path = '/'.join(path.split('/')[:-1])
        
    if(not isValid):
        sys.stderr.write("Not inside a Git repository")
        exit()
    else:
        return path

#Get all the branch commits in a dictionary. 
#Here, rootDir is the directory that contains the .git directory
#Return a dictionary (branch_list) that maps branch names to commit hashes
def get_branches(rootDir):
    rootDir = rootDir + '/.git/refs/heads'
    branch_list = {}
    for dirName, subdirList, fileList in os.walk(rootDir):
        for fname in fileList:
            file_path = dirName+'/'+ fname
            branch_name = file_path[file_path.rfind("/heads")+7:]
            f = open(file_path, 'r')
            for lines in f.readlines():
                branch_list[branch_name] = (lines.rstrip())
            f.close()
    return branch_list             

#Build the commit graph (A directed acycylic graph or dag)
#The graph returned is a dictionary that maps commit hashes to commit nodes
def build_dag(branches):
    path = discover()
    dag = {}
    stack = []
    #Perform a depth first traversal using a stack to generate commit nodes
    #with ids and parents for each node
    for commit_id in branches.values():
        stack.append(commit_id)
        while(len(stack)):
            commit_id = stack.pop()
            commit = CommitNode(commit_id)
            directory = commit_id[0:2]
            file = commit_id[2:]
            full_path = path + "/.git/objects/" + directory + '/' + file
            raw_bytes = open(full_path, "rb").read()
            data = zlib.decompress(raw_bytes).decode("utf-8").split("\n")
            for line in data:
                if line.startswith("parent"):
                    parent_commit_id = line[7:]
                    commit.parents.add(parent_commit_id.rstrip())
                    stack.append(parent_commit_id)
            dag[commit_id] = commit

    #For each commit node(c) in the dag, find it's parents. for each parent, add c as a child.
    for commit in dag.values():
        parents = commit.parents
        for parent_id in parents:
            dag[parent_id].children.add(commit.commit_hash)

     #Now that the dag is formed, we can add the commit with no parents to the root.
    for commit in dag.values():
        if(len(commit.parents) == 0):
            root = commit
    
    return dag, root

#Perform a topoogical sort, using Kahn's Algorithm
def topological_sort(dag, root):
    sorted_elements = []
    #S = set()
    S = []
    #S.add(root)
    S.append(root)
    while(len(S)):
        commit = S.pop()
        sorted_elements.append(commit.commit_hash)
        #for all of this commit's children, remove the edge from the graph
        #(removing the parent child relationship)
        #if the child has no other parents, insert it into S
        for child_id in commit.children.copy():
            dag[child_id].parents.remove(commit.commit_hash)
            dag[commit.commit_hash].children.remove(child_id)
            if(len(dag[child_id].parents) == 0):
                #S.add(dag[child_id]) 
                S.append(dag[child_id])        
    return sorted_elements
    #sorted_elements is a list of strings representing commit hashes.

#Return all branch names corresponding to this commit hash, sorted lexigraphically
def getBranchNames(id): 
    branches = get_branches(discover())
    branch_names = []
    for name, commit in branches.items():
        if (commit == id):
            #This hash corresponds to a branch head
            branch_names.append(name)
    branch_names.sort()
    return branch_names

#Compute the sticky end string for a particular commit_id and graph
def compute_sticky_end(commit_id, dag):
    parents = dag[commit_id].parents
    sticky_end = " "
    #TODO: remove this later
    x = []
    for id in parents:
        #x.append(id[0:2])
        x.append(id)
    #Till here
    sticky_end += (" ").join(x)
    sticky_end+= "="
    sticky_end+="\n"
    return sticky_end

#See if you want a sticky end for a particular commit_id
def want_sticky_end(commit_id, list, dag):
     #If this is the last element in the list, I don't want to check for sticky ends
    want_sticky_end = False
    if( len(list) -1 == list.index(commit_id)):
        pass
    else:
        next_commit_id = list[list.index(commit_id)+1]
        if (not next_commit_id in dag[commit_id].parents):
            want_sticky_end = True
    return want_sticky_end

#See if you want a sticky start for a commit_id based on the previous string printed
def want_sticky_start(previous_string):
    return previous_string.endswith("\n")

#Compute the sricky start for a particular commit_id and graph
def compute_sticky_start(commit_id, dag):
    sticky_start = "="
    x = []
    for child_id in dag[commit_id].children:
        #x.append(child_id[0:2])
        x.append(child_id)
    sticky_start+= (" ").join(x)
    sticky_start+= "\n"
    return sticky_start

           
#The function that prints out the final result
def topo_order_commits():
    path = discover()
    branches = get_branches(path)
    graph, r = build_dag(branches)
    list = topological_sort(graph, r) #This destroys dag, so we need to rebuild it.
    dag, root = build_dag(branches)
    #Reverse the resulting list, we want branches to come first
    list.reverse()
    previous_string = ""
    #For every commit_id, print out it's corresponding message
    for commit_id in list:
        string = ""
        #TODO:  remove the [0:2]
        #End of TODO
        if(want_sticky_start(previous_string)):
            string = compute_sticky_start(commit_id, dag)


        #string += commit_id[0:2]
        string += commit_id
        
        branch_names_for_commit = getBranchNames(commit_id)
        if (not want_sticky_end(commit_id, list, dag)):
            for name in branch_names_for_commit:
                string = string + " branch-" + name + " "
    
        
        if(want_sticky_end(commit_id, list, dag)):
            string+=compute_sticky_end(commit_id, dag)
    

        print(string)
        previous_string = string


    #To verify my implementation did not invoke any other system calls, I used the following 
    #shell commands:
    # strace python3 topp_ordered_commits.py 2>strace_output.txt
    # cat strace_output.txt | grep "git" 1> git_occurences.txt
    # I then examined git_occurences.txt to see the context in which "git" occured
    # I found that it only occured in file paths  passed as argument to open and getcwd, hence
    # confirming that no git commands were invoked in any way.
if __name__ == '__main__':
    topo_order_commits()
