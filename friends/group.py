import pandas as pd
import networkx as nx
import sys

# Get filename from command line.
filename = sys.argv[1]


# Function to generate recommendations to a specific user.
def individual_recommendations(user_id):
    # Get all friends for user_id
    friends = list(nx.all_neighbors(G, user_id))

    # Create a set of all friends of friends of user_id that may be suggested, filtering direct friends.
    all_friends_of_friends = set()
    for friend in friends:
        all_friends_of_friends.update(
            set([second_degree for second_degree in list(nx.all_neighbors(G, friend)) if
                 second_degree != user_id and second_degree not in friends]))

    # Creates a list corresponding to all_friends_of_friends, with the count of friends in common with user_id.
    suggestions_weight = []
    for possibility in all_friends_of_friends:
        common_friends = list(nx.common_neighbors(G, user_id, possibility))
        score = 0
        # For each common friend, compute the weighted score based on number of friends.
        for common in common_friends:
            score += 1 / len(list(nx.all_neighbors(G, common)))
        suggestions_weight += [score]

    # Creates a sorted recommendation DataFrame with the recommended friends and count of friends in common (score)
    dat = {'score': suggestions_weight, 'suggestion': list(all_friends_of_friends)}
    return pd.DataFrame(data=dat).sort_values(['score', 'suggestion'], ascending=[False, True])


# Aggregates group recommendations based on individual user recommendations. Uses borda count method.
def aggregate_borda(user_recs):
    sum_points = {}
    for individual_rec in user_recs:
        suggestions = individual_rec.suggestion.values
        for index, sug in enumerate(suggestions):
            weight = individual_rec.suggestion.values.size - index
            if sug in sum_points:
                sum_points[sug] = sum_points[sug] + weight
            else:
                sum_points[sug] = weight

    dat = {'score': list(sum_points.values()), 'suggestion': list(sum_points.keys())}
    return pd.DataFrame(data=dat).sort_values(['score', 'suggestion'], ascending=[False, True])


# Aggregates group recommendations based on individual user recommendations. Uses average method.
def aggregate_average(user_recs):
    sum_score = {}
    for individual_rec in user_recs:
        suggestions = individual_rec.suggestion.values
        for index, sug in enumerate(suggestions):
            score = individual_rec.score.iloc[index]
            if sug in sum_score:
                sum_score[sug] = (sum_score[sug][0] + score, sum_score[sug][0] + 1)
            else:
                sum_score[sug] = (score, 1)
    for k, v in sum_score.items():
        sum_score[k] = v[0] / v[1]

    dat = {'score': list(sum_score.values()), 'suggestion': list(sum_score.keys())}
    return pd.DataFrame(data=dat).sort_values(['score', 'suggestion'], ascending=[False, True])


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
    print('Re-run this program with graph.pickle as argument, followed by method and user ids to get recommendations.')
    print('Example: python group.py graph.pickle borda 20341 33722 35571 25017')

else:

    # Reads the processed graph from file.
    try:
        G = nx.read_gpickle(filename)

        # Gets the method passed as second command line parameter, and the users passed as following parameters
        method = sys.argv[2]
        user_ids = [int(u) for u in sys.argv[3:]]

        # Gets first 4 recommendations for every user
        ind_recs = [individual_recommendations(user_id).head(4) for user_id in user_ids]

        recommendation = None
        if method == 'borda':
            recommendation = aggregate_borda(ind_recs).head(5)
        elif method == 'average':
            recommendation = aggregate_average(ind_recs).head(5)
        else:
            print("Supported methods are 'borda' and 'average'. Unrecognized: " + method)
            exit(1)

        print('\nUser group:')
        print(*user_ids, sep=", ")
        print('\nThe recommended friendships to the group, in order, are:')
        print(*recommendation.suggestion.values, sep=", ")
        print('\nOut of curiosity, their scores were respectively:')
        print(*recommendation.score.values, sep=", ")

    except FileNotFoundError:
        print("File graph.pickle not found! Run first 'python friends.py facebook-links.txt'")

# python group.py graph.pickle borda 20341 33722 35571 25017
# python group.py graph.pickle average 20341 33722 35571 25017
