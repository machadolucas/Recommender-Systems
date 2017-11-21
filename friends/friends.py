import pandas as pd
import networkx as nx
import sys

# Get filename from command line.
filename = sys.argv[1]

# If is not a saved graph file, load data from file and save as graph.pickle.
# In that way, we avoid processing the file every time into a Graph (since it is static).
# In a real world situation, instead of a file, there would be a noSQL graph database.
if not filename.endswith('.pickle'):

    df = pd.read_csv(filename, sep='\t', header=None)
    df.columns = ['u1', 'u2', 'timestamp']

    print('Creating graph from data...\n',
          'This could take a few minutes (around 6) depending on your computer... Grab a coffee! :)')
    G = nx.Graph()
    for i in range(df.index.size):
        u1 = df.iloc[i].u1
        u2 = df.iloc[i].u2
        G.add_edge(u1, u2)

    nx.write_gpickle(G, 'graph.pickle')
    print('Data loaded and graph file saved as graph.pickle')
    print('Re-run this program with graph.pickle as argument, followed by the user id to get recommendations.')
    print('Example: python friends.py graph.pickle 20341')

else:
    # Gets the user_id passed as second command line parameter, and reads the processed graph from file.
    user_id = int(sys.argv[2])
    try:
        G = nx.read_gpickle(filename)

        # Get all friends for user_id
        friends = list(nx.all_neighbors(G, user_id))

        # Create a set of all friends of friends of user_id that may be suggested, filtering direct friends.
        all_friends_of_friends = set()
        for friend in friends:
            all_friends_of_friends.update(
                set([second_degree for second_degree in list(nx.all_neighbors(G, friend)) if
                     second_degree != user_id & second_degree not in friends]))

        # Creates a list corresponding to all_friends_of_friends, with the count of friends in common with user_id.
        suggestions_weight = []
        for possibility in all_friends_of_friends:
            suggestions_weight = suggestions_weight + [len(list(nx.common_neighbors(G, user_id, possibility)))]

        # Creates a sorted recommendation DataFrame with the recommended friends and count of friends in common (score)
        dat = {'score': suggestions_weight, 'suggestion': list(all_friends_of_friends)}
        recommendation_table = pd.DataFrame(data=dat).sort_values(['score', 'suggestion'], ascending=[False, True])

        # Get first 4 recommendations and print results
        recommendation = recommendation_table.head(4)
        print('\nThe recommended friendships, in order, are:')
        print(*recommendation.suggestion.values, sep=", ")
        print('\nOut of curiosity, their scores were respectively:')
        print(*recommendation.score.values, sep=", ")

    except FileNotFoundError:
        print("File graph.pickle not found! Run first 'python friends.py facebook-links.txt'")
