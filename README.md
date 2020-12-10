# Topologically Ordered Commits

Given a git repository, the commits can be thought of as having the structure of a directed acyclic graph (DAG) with the commits being the vertices. In particular, one can create a directed edge from each child commit to each of its parent commits. Alternatively, one can create a directed edge from each parent to each of its children.

When called from within a .git repository, this script performs a topological sort on all the commits made, and prints their hashes out in reverse topological order. No git commands are invoked in the process.

