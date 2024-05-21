# Ben Williams '25 and Sam Starrs '26
# May 2024

import simulation_analysis_funcs
from Simulation import Simulation

# Parameters for the sim
num_people = 100
num_days = 28
min_interactions = 5
max_interactions = 15
max_friends = 25

num_simulations = 100

# Create the dictionaries to keep track of all stats
relevant_dictionaries = simulation_analysis_funcs.get_empty_analysis_dicts()
most_connected_dict_at_end = relevant_dictionaries["most_connected_dict"]
least_connected_dict_at_end = relevant_dictionaries["least_connected_dict"]
loner_dict_at_end = relevant_dictionaries["loner_dict"]

# Run all the simulations and append their statistics
for curr_simulation in range(num_simulations):
    print(f"Running simulation: {curr_simulation}")
    new_sim = Simulation(num_people=num_people, min_interactions=min_interactions,
                         max_interactions=max_interactions, max_friends=max_friends)

    new_sim.run_simulation(num_days, produce_analytics=True)

    for key, item in most_connected_dict_at_end.items():
        most_connected_dict_at_end[key][0].append(new_sim.most_connected_dict[key][0][-1])

    for key, item in least_connected_dict_at_end.items():
        least_connected_dict_at_end[key][0].append(new_sim.least_connected_dict[key][0][-1])

    for key, item in loner_dict_at_end.items():
        if key != "race_distribution" and key != "age_distribution":
            loner_dict_at_end[key][0].append(new_sim.loner_dict[key][0][-1])

# Print out simulation parameters
print(f"Simulation parameters:\n\tNum people: {num_people}\n\tNum days: {num_days}\n\tMin interactions: {min_interactions}" + \
      f"\n\tMax interactions: {max_interactions}\n\tMax friends: {max_friends}")

# Print out all averaged statistics
print("\nAverages for most connected people:")
for key, item in most_connected_dict_at_end.items():
    average = sum(most_connected_dict_at_end[key][0]) / len(most_connected_dict_at_end[key][0])
    print(f"\tAverage for category {key} over {num_simulations} simulations is: {average:.4f}")

print("\nAverages for least connected people:")
for key, item in least_connected_dict_at_end.items():
    average = sum(least_connected_dict_at_end[key][0]) / len(least_connected_dict_at_end[key][0])
    print(f"\tAverage for category {key} over {num_simulations} simulations is: {average:.4f}")

print("\nAverages for loners:")
for key, item in loner_dict_at_end.items():
    if key != "race_distribution" and key != "age_distribution":
        average = sum(loner_dict_at_end[key][0]) / len(loner_dict_at_end[key][0])
        print(f"\tAverage for category {key} over {num_simulations} simulations is: {average:.4f}")