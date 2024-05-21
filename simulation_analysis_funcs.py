# Ben Williams '25 and Sam Starrs '26
# May 10th, 2024

import networkx as nx
from Simulation import Simulation
import numpy as np
import os
import matplotlib.pyplot as plt


def get_loners(simulation):
    """
    Returns a list of Person objects of the people in the simulation without friends
    """
    loners = []

    for person in simulation.people:
        if len(person.friends) == 0:
            loners.append(person)

    return loners


def get_non_loners(simulation):
    """
    Returns a list of Person objects of the people in the simulation with friends
    """
    social_people = []

    for person in simulation.people:
        if len(person.friends) > 0:
            social_people.append(person)

    return social_people


def get_loner_statistics(simulation):
    """
    Gets the statistics for everyone who has no friends at the current point in the simulation.

    Returns a dictionary with the following keys (string):

     total_loners --> the number of people who are left alone

     avg_friend_threshold --> the average friend threshold of every person left alone

     age_distribution --> the number of people at each age that remain

     race_distribution --> the number of people in each race that remain

     avg_same_race_pref --> the average preference (bonus) that these individuals have for the same race

     avg_other_race_pref --> the average preference (penalty) that these individuals have for other races

     avg_same_gender_pref --> the average preference (bonus) that these individuals have for the same gender

     avg_other_gender_pref --> the average preference (bonus/penalty) that these individuals have for the other gender

     avg_same_age_pref --> the average preference (bonus) that these individuals have for people of the exact same age

     avg_age_diff_pref --> the average preference (penalty) that these individuals have for each year of age difference

     avg_same_hobby_pref --> the average preference (bonus) that these individuals have for common hobbies

    """

    results = dict()

    loners = get_loners(simulation)

    age_distribution = np.zeros(50 - 18 + 1) # ages range from 18 --> 52
    race_distribution = np.zeros(6)
    friend_threshold_total = 0
    same_race_pref_total = 0
    other_race_pref_total = 0
    same_gender_pref_total = 0
    other_gender_pref_total = 0
    same_age_pref_total = 0
    other_age_pref_total = 0
    hobby_pref_total = 0

    for person in loners:
        age_distribution[person.characteristics["age"] - 18] += 1
        race_distribution[person.characteristics["race"]] += 1
        friend_threshold_total += person.friend_threshold
        same_race_pref_total += person.preferences["same_race"]
        other_race_pref_total += person.preferences["other_race"]
        same_gender_pref_total += person.preferences["same_gender"]
        other_gender_pref_total += person.preferences["opposite_gender"]
        same_age_pref_total += person.preferences["same_age"]
        other_age_pref_total += person.preferences["age_year_diff"]
        hobby_pref_total += person.preferences["same_hobby"]

    total_loners = len(loners)

    if total_loners == 0:
        results["total_loners"] = 0
        results["age_distribution"] = age_distribution
        results["race_distribution"] = race_distribution
        results["avg_friend_threshold"] = None
        results["avg_same_race_pref"] = None
        results["avg_other_race_pref"] = None
        results["avg_same_gender_pref"] = None
        results["avg_other_gender_pref"] = None
        results["avg_same_age_pref"] = None
        results["avg_age_diff_pref"] = None
        results["avg_same_hobby_pref"] = None
    else:
        results["total_loners"] = total_loners
        results["age_distribution"] = age_distribution / total_loners
        results["race_distribution"] = race_distribution / total_loners
        results["avg_friend_threshold"] = float("{:.3f}".format(friend_threshold_total / total_loners))
        results["avg_same_race_pref"] = float("{:.3f}".format(same_race_pref_total / total_loners))
        results["avg_other_race_pref"] = float("{:.3f}".format(other_race_pref_total / total_loners))
        results["avg_same_gender_pref"] = float("{:.3f}".format(same_gender_pref_total / total_loners))
        results["avg_other_gender_pref"] = float("{:.3f}".format(other_gender_pref_total / total_loners))
        results["avg_same_age_pref"] = float("{:.3f}".format(same_age_pref_total / total_loners))
        results["avg_age_diff_pref"] = float("{:.3f}".format(other_age_pref_total / total_loners))
        results["avg_same_hobby_pref"] = float("{:.3f}".format(hobby_pref_total / total_loners))

    return results


def get_friend_group_info(simulation):
    """
    Returns a dictionary containing information about the connected components on the graph with >1 node/person

    The dictionary has the following keys/info:

     num_fgs --> the number of disconnected friend groups

     avg_fg_size --> the average number of people in each friend group

    """

    # Create networkx graph
    friendship_graph = nx.Graph()
    friendship_graph.add_edges_from(simulation.friendships)

    results = dict()

    results["num_fgs"] = nx.number_connected_components(friendship_graph)

    # friend_groups is a generator of sets of friend groups, may be useful later
    friend_groups = nx.connected_components(friendship_graph)
    friend_total = 0
    for friend_group in friend_groups:
        friend_total += len(friend_group)

    # Ensure no divide by 0
    if results["num_fgs"] > 0:
        results["avg_fg_size"] = friend_total / results["num_fgs"]
    else:
        results["avg_fg_size"] = 0

    return results


def get_connectedness_info(simulation):
    """
    Gets information on the connectedness of people in the **largest connected component** (friend group)

    Returns a dictionary with the following keys/info:

     avg_friends --> the average number of friends each person has

     avg_avg_deg_sep --> the average over all people of the average degree of separation each person is from everyone else

     max_avg_deg_sep --> the maximum distance avg degree of separation for a person from everyone else

     max_avg_deg_sep_person --> the person object for the max_avg_deg_of_sep
                                   aka the "least well connected" person that is still in the big group

     min_avg_deg_sep --> the minimum average degree of separation for a person from everyone else
                            aka the "most well connected" stat

     min_avg_deg_sep_person --> the person object for the min_avg_deg_of_sep
                                   aka the "most well connected" person

     max_distance --> the farthest away two people are from each other

    """

    # Create networkx graph
    friendship_graph = nx.Graph()
    friendship_graph.add_edges_from(simulation.friendships)

    # Get the largest connected component
    largest_fg_set = max(nx.connected_components(friendship_graph), key=len)

    # Get the subgraph of just this group
    largest_fg_graph = friendship_graph.subgraph(largest_fg_set).copy()

    total_friends = 0
    total_avg_degree_sep = 0
    max_avg_deg = 0
    min_avg_deg = np.inf
    min_avg_deg_person = None
    max_avg_deg_person = None
    max_distance = 0

    # The slow part - looping through a bfs on each person
    for person_id in largest_fg_set:
        # Get the number of friends for the person and add it to the total
        total_friends += len(simulation.people[person_id].friends)

        # Get all the layers
        total_separation = 0
        bfs_layers = nx.bfs_layers(largest_fg_graph, person_id)

        # Go through each layer and add to the total
        layer_num = 0
        for layer in bfs_layers:
            total_separation += len(layer) * layer_num

            # See if this person has people very far away from them
            if layer_num > max_distance:
                max_distance = layer_num

            layer_num += 1

        # We don't include the person we are considering now
        individual_avg_separation = total_separation / (len(largest_fg_set) - 1)
        total_avg_degree_sep += individual_avg_separation

        # See if this is the largest separation
        if individual_avg_separation > max_avg_deg:
            max_avg_deg = individual_avg_separation
            max_avg_deg_person = simulation.people[person_id]

        # See if this is the minimum separation
        if individual_avg_separation < min_avg_deg:
            min_avg_deg = individual_avg_separation
            min_avg_deg_person = simulation.people[person_id]

    results = dict()
    results["avg_friends"] = float("{:.3f}".format(total_friends / len(largest_fg_set)))
    results["avg_avg_deg_sep"] = float("{:.3f}".format(total_avg_degree_sep / len(largest_fg_set)))
    results["min_avg_deg_sep"] = float("{:.3f}".format(min_avg_deg))
    results["min_avg_deg_sep_person"] = min_avg_deg_person
    results["max_avg_deg_sep"] = float("{:.3f}".format(max_avg_deg))
    results["max_avg_deg_sep_person"] = max_avg_deg_person
    results["max_distance"] = max_distance

    return results


def get_individual_statistics(person):
    """
    Takes a person object and returns a dictionary containing information on their characteristics and preferences

    Returns a dictionary with the following keys:

        age --> the age of the person

        friend_threshold --> the friend threshold of the person

        num_friends --> the number of friends the person has

        same_race_pref --> the same-race preference of the person

        other_race_pref --> the other-race preference of the person

        same_gender_pref --> the same-gender preference of the person

        opposite_gender_pref --> the opposite-gender preference of the person

        same_age_pref --> the same age preference of the person

        age_diff_pref --> the preference/penalty for each year of age difference this person has when making friends

        same_hobby_pref --> the common hobby preference of the person

    """

    person_info = dict()

    person_info["age"] = person.characteristics["age"]
    person_info["friend_threshold"] = person.friend_threshold
    person_info["num_friends"] = len(person.friends)
    person_info["same_race_pref"] = person.preferences["same_race"]
    person_info["other_race_pref"] = person.preferences["other_race"]
    person_info["same_gender_pref"] = person.preferences["same_gender"]
    person_info["opposite_gender_pref"] = person.preferences["opposite_gender"]
    person_info["same_age_pref"] = person.preferences["same_age"]
    person_info["age_diff_pref"] = person.preferences["age_year_diff"]
    person_info["same_hobby_pref"] = person.preferences["same_hobby"]

    return person_info

def get_empty_analysis_dicts():
    """
    Initializes and returns a dictionary of empty dictionaries needed to gather all of the statistics from a simulation

    Returns a dictionary with the following keys:

        connectedness_dict --> based off of the get_connectedness_info function

        friend_group_dict --> based off of the get_friend_group_info function

        loner_dict --> based off of the get_loner_statistics function

        most_connected_dict --> to fetch information from the most connected person -
                                    get this from the get_connectedness_info function

        least_connected_dict --> to fetch information from the least connected person -
                                    get this from the get_connectedness_info function

    """
    connectedness_dict = {
        "new_friendships_made": ([], "New Friendships Made", "Number of New Friendships"),
        "avg_friends": ([], "Average Friends", "Number of Friends"),
        "avg_avg_deg_sep": ([], "Average Average Degree of Separation", "Degree of Separation"),
        "max_avg_deg_sep": ([], "Maximum Average Degree of Separation", "Degree of Separation"),
        "min_avg_deg_sep": ([], "Minimum Average Degree of Separation", "Degree of Separation"),
        # "min_avg_deg_sep_person": ([], "Person with Minimum Average Degree of Separation"),
        "max_distance": ([], "Maximum Distance between Two People", "Distance")
    }

    friend_group_dict = {
        "num_fgs": ([], "Number of Disconnected Friend Groups", "Number of Friend Groups"),
        "avg_fg_size": ([], "Average Size of Each Friend Group", "Size of Friend Group")
    }

    loner_dict = {
        "total_loners": ([], "Total Loners", "Number of People"),
        "avg_friend_threshold": ([], "Average Friend Threshold", "Friend Threshold"),
        "age_distribution": ([], "Age Distribution", "Age"),
        "race_distribution": ([], "Race Distribution", "Amount per Race"),
        "avg_same_race_pref": ([], "Average Same Race Preference", "Same Race Preference"),
        "avg_other_race_pref": ([], "Average Other Race Preference", "Other Race Preference"),
        "avg_same_gender_pref": ([], "Average Same Gender Preference", "Same Gender Preference"),
        "avg_other_gender_pref": ([], "Average Other Gender Preference", "Other Gender Preference"),
        "avg_same_age_pref": ([], "Average Same Age Preference", "Same Age Preference"),
        "avg_age_diff_pref": ([], "Average Age Difference Preference", "Age Difference Preference"),
        "avg_same_hobby_pref": ([], "Average Same Hobby Preference", "Same Hobby Preference")
    }

    most_connected_dict = {
        "age": ([], "Age of Most Connected Person", "Age"),
        "friend_threshold": ([], "Friend Threshold of Most Connected Person", "Common Hobby Preference"),
        "num_friends": ([], "Number of Friends of Most Connected Person", "Common Hobby Preference"),
        "same_race_pref": ([], "Same Race Preference of Most Connected Person", "Same Race Preference"),
        "other_race_pref": ([], "Other Race Preference of Most Connected Person", "Other Race Preference"),
        "same_gender_pref": ([], "Same Gender Preference of Most Connected Person", "Same Race Preference"),
        "opposite_gender_pref": ([], "Opposite Gender Penalty of Most Connected Person", "Opposite Gender Penalty"),
        "same_age_pref": ([], "Same Age Preference of Most Connected Person", "Same Age Preference"),
        "age_diff_pref": ([], "Age Difference (per year) Penalty of Most Connected Person", "Age Difference Penalty"),
        "same_hobby_pref": ([], "Common Hobby Preference of Most Connected Person", "Common Hobby Preference"),
    }

    least_connected_dict = {
        "age": ([], "Age of Least Connected Person", "Age"),
        "friend_threshold": ([], "Friend Threshold of Least Connected Person", "Common Hobby Preference"),
        "num_friends": ([], "Number of Friends of Least Connected Person", "Common Hobby Preference"),
        "same_race_pref": ([], "Same Race Preference of Least Connected Person", "Same Race Preference"),
        "other_race_pref": ([], "Other Race Preference of Least Connected Person", "Other Race Preference"),
        "same_gender_pref": ([], "Same Gender Preference of Least Connected Person", "Same Race Preference"),
        "opposite_gender_pref": ([], "Opposite Gender Preference of Least Connected Person", "Opposite Gender Preference"),
        "same_age_pref": ([], "Same Age Preference of Least Connected Person", "Same Age Preference"),
        "age_diff_pref": ([], "Age Difference (per year) Penalty of Least Connected Person", "Age Difference Penalty"),
        "same_hobby_pref": ([], "Common Hobby Preference of Least Connected Person", "Common Hobby Preference"),
    }

    analysis_dicts = {
        "connectedness_dict": connectedness_dict,
        "friend_group_dict": friend_group_dict,
        "loner_dict": loner_dict,
        "most_connected_dict": most_connected_dict,
        "least_connected_dict": least_connected_dict,
    }

    return analysis_dicts


def get_analytics(simulation, output_dir="analytics"):
    """
    Generate and save analytics plots for the simulation.

    Parameters:
        simulation : The simulation object to get the analytics for
        output_dir (str): The directory to save the analytics plots. Default is "analytics".
    """

    connectedness_dict = simulation.connectedness_dict
    friend_group_dict = simulation.friend_group_dict
    loner_dict = simulation.loner_dict
    most_connected_dict = simulation.most_connected_dict
    least_connected_dict = simulation.least_connected_dict

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(output_dir + "/connectedness", exist_ok=True)
    os.makedirs(output_dir + "/friend_group", exist_ok=True)
    os.makedirs(output_dir + "/loners", exist_ok=True)
    os.makedirs(output_dir + "/most_connected_person", exist_ok=True)
    os.makedirs(output_dir + "/least_connected_person", exist_ok=True)


    time_steps = list(range(1, len(connectedness_dict["avg_friends"][0]) + 1))

    for key, value in connectedness_dict.items():
        plt.figure(figsize=(10, 5))
        plt.plot(time_steps, connectedness_dict[key][0], marker='o', color='b', label=connectedness_dict[key][2])
        plt.xlabel('Time Steps')
        plt.ylabel(connectedness_dict[key][1])
        plt.title(connectedness_dict[key][1] + " Over Time")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir + "/connectedness", f'{key}.png'))

    for key, value in friend_group_dict.items():
        plt.figure(figsize=(10, 5))
        plt.plot(time_steps, friend_group_dict[key][0], marker='o', color='b', label=friend_group_dict[key][2])
        plt.xlabel('Time Steps')
        plt.ylabel(friend_group_dict[key][1])
        plt.title(friend_group_dict[key][1] + " Over Time")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir + "/friend_group", f'{key}.png'))

    for key, value in loner_dict.items():
        plt.figure(figsize=(10, 5))
        plt.plot(time_steps, loner_dict[key][0], marker='o', color='b', label=loner_dict[key][2])
        plt.xlabel('Time Steps')
        plt.ylabel(loner_dict[key][1])
        plt.title(loner_dict[key][1] + " Over Time")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir + "/loners", f'{key}.png'))

    for key, value in most_connected_dict.items():
        plt.figure(figsize=(10, 5))
        plt.plot(time_steps, most_connected_dict[key][0], marker='o', color='b', label=most_connected_dict[key][2])
        plt.xlabel('Time Steps')
        plt.ylabel(most_connected_dict[key][1])
        plt.title(most_connected_dict[key][1] + " Over Time")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir + "/most_connected_person", f'{key}.png'))

    for key, value in least_connected_dict.items():
        plt.figure(figsize=(10, 5))
        plt.plot(time_steps, least_connected_dict[key][0], marker='o', color='b', label=least_connected_dict[key][2])
        plt.xlabel('Time Steps')
        plt.ylabel(least_connected_dict[key][1])
        plt.title(least_connected_dict[key][1] + " Over Time")
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(output_dir + "/least_connected_person", f'{key}.png'))

    simulation.print_analysis()


if __name__ == "__main__":
    sim = Simulation(num_people=100, max_friends=50)
    sim.run_simulation(num_days=20)

    # loner_stats = get_loner_statistics(sim)
    # for key in loner_stats.keys():
    #     print(f"Stat: {key} | result: {loner_stats[key]}")

    # friend_group_info = get_friend_group_info(sim)
    # for day in range(10):
    #     sim.simulate_day()
    #     friend_group_info = get_friend_group_info(sim)
    #     print(f"Day {day}, friend_group_info {friend_group_info}")
    print(get_loner_statistics(sim))
    print("-------------")
    print(get_friend_group_info(sim))
    print("-------------")
    print(get_connectedness_info(sim))
    sim.visualize_curr_friendships(show_loners=False)
